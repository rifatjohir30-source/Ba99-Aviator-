import os
import json
import statistics
from pathlib import Path
from threading import Lock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", 8000))
FILE = Path("aviator_data.json")
lock = Lock()

def load():
    try:
        d = json.loads(FILE.read_text())
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {"history": [], "wins": 0, "losses": 0}

data = load()

def save():
    FILE.write_text(json.dumps(data))

def analyze():
    h = data["history"]
    recent = h[-20:]

    if not recent:
        return {
            "count": 0, "average": 0, "median": 0,
            "highest": 0, "low": 0, "medium": 0,
            "high": 0, "trend": "WAIT"
        }

    low = sum(x < 2 for x in recent)
    medium = sum(2 <= x < 5 for x in recent)
    high = sum(x >= 5 for x in recent)

    trend = max(
        [("LOW", low), ("MEDIUM", medium), ("HIGH", high)],
        key=lambda x: x[1]
    )[0]

    return {
        "count": len(h),
        "average": round(statistics.mean(recent), 2),
        "median": round(statistics.median(recent), 2),
        "highest": round(max(h), 2),
        "low": low,
        "medium": medium,
        "high": high,
        "trend": trend
    }

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aviator Analysis Bot</title>
<style>
body{margin:0;background:#0b1020;color:white;font-family:Arial;padding:16px}
main{max-width:480px;margin:auto}
h2{text-align:center;color:#ffbd59}
.card{background:#19243b;padding:17px;border-radius:13px;margin:14px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.stat{background:#0e1930;padding:14px;text-align:center;border-radius:9px}
.value{font-size:24px;color:#42e8bd;font-weight:bold;margin-top:8px}
textarea{width:100%;height:85px;background:#0b1020;color:white;padding:10px;border:1px solid #65728a;border-radius:8px;box-sizing:border-box;font-size:17px}
button{width:100%;padding:14px;margin-top:10px;border:0;border-radius:8px;background:#ffbd59;font-weight:bold;font-size:16px}
.green{background:#42e8bd}
small{color:#aebbd0}
</style>
</head>
<body>
<main>
<h2>AVIATOR AUTO ANALYSIS</h2>

<div class="card">
<h3>ADD CRASH HISTORY</h3>
<textarea id="numbers" placeholder="1.20, 2.50, 4.30, 1.10"></textarea>
<button onclick="add()">ADD & ANALYZE</button>
<small>Enter actual multiplier results separated by commas or spaces.</small>
</div>

<div class="card">
<h3>LIVE ANALYSIS</h3>
<div class="grid">
<div class="stat">TOTAL<div class="value" id="count">0</div></div>
<div class="stat">AVERAGE<div class="value" id="average">0x</div></div>
<div class="stat">MEDIAN<div class="value" id="median">0x</div></div>
<div class="stat">HIGHEST<div class="value" id="highest">0x</div></div>
<div class="stat">LOW<div class="value" id="low">0</div></div>
<div class="stat">MEDIUM<div class="value" id="medium">0</div></div>
<div class="stat">HIGH<div class="value" id="high">0</div></div>
<div class="stat">TREND<div class="value" id="trend">WAIT</div></div>
</div>
</div>

<div class="card">
<h3>WIN / LOSS TRACKER</h3>
<div class="grid">
<div class="stat">WIN<div class="value" id="wins">0</div></div>
<div class="stat">LOSS<div class="value" id="losses">0</div></div>
</div>
<button class="green" onclick="track('win')">ADD WIN</button>
<button onclick="track('loss')">ADD LOSS</button>
</div>

<div class="card">
<h3>RECENT HISTORY</h3>
<div id="history">No data</div>
<button onclick="resetData()">RESET DATA</button>
</div>

<p><small>Historical statistics only. The next crash multiplier cannot be reliably predicted.</small></p>
</main>

<script>
async function refresh(){
 const r=await fetch('/api/state');
 const d=await r.json();
 const s=d.stats;
 for(const k of ['count','average','median','highest','low','medium','high','trend']){
   document.getElementById(k).textContent =
     ['average','median','highest'].includes(k) ? s[k]+'x' : s[k];
 }
 document.getElementById('wins').textContent=d.wins;
 document.getElementById('losses').textContent=d.losses;
 const box=document.getElementById('history');
 box.innerHTML='';
 if(!d.history.length){box.textContent='No data';}
 d.history.slice(-25).reverse().forEach(x=>{
   const p=document.createElement('p');
   p.textContent=Number(x).toFixed(2)+'x';
   box.appendChild(p);
 });
}

async function add(){
 const el=document.getElementById('numbers');
 const values=el.value.trim().split(/[\\s,;]+/).filter(Boolean).map(Number);
 if(!values.length || values.some(x=>!Number.isFinite(x)||x<1)){
   alert('Enter valid multipliers (1x or higher)');
   return;
 }
 const r=await fetch('/api/add',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({values})
 });
 const d=await r.json();
 if(!d.ok){alert(d.error);return;}
 el.value='';
 refresh();
}

async function track(result){
 await fetch('/api/track',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({result})
 });
 refresh();
}

async function resetData(){
 if(!confirm('Delete all data?'))return;
 await fetch('/api/reset',{method:'POST'});
 refresh();
}
refresh();
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        if self.path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/state":
            with lock:
                self.send_json({
                    "stats": analyze(),
                    "history": data["history"],
                    "wins": data["wins"],
                    "losses": data["losses"]
                })
        elif self.path == "/health":
            self.send_json({"status": "active"})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        try:
            body = self.read_json()
            with lock:
                if self.path == "/api/add":
                    values = body.get("values", [])
                    if not isinstance(values, list) or not values:
                        return self.send_json({"ok": False, "error": "No values"}, 400)
                    if any(not isinstance(x, (int, float)) or isinstance(x, bool)
                           or not 1 <= x <= 100000 for x in values):
                        return self.send_json({"ok": False, "error": "Invalid multiplier"}, 400)
                    data["history"].extend(float(x) for x in values)
                    data["history"] = data["history"][-500:]
                    save()
                    self.send_json({"ok": True})

                elif self.path == "/api/track":
                    result = body.get("result")
                    if result == "win":
                        data["wins"] += 1
                    elif result == "loss":
                        data["losses"] += 1
                    else:
                        return self.send_json({"ok": False}, 400)
                    save()
                    self.send_json({"ok": True})

                elif self.path == "/api/reset":
                    data.update({"history": [], "wins": 0, "losses": 0})
                    save()
                    self.send_json({"ok": True})
                else:
                    self.send_json({"error": "Not found"}, 404)
        except Exception:
            self.send_json({"ok": False, "error": "Invalid request"}, 400)

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    print("AVIATOR ANALYSIS BOT ACTIVE", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()