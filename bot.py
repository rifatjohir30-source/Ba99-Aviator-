import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from datetime import datetime, timezone

PORT = int(os.environ.get("PORT", "8000"))
DATA_FILE = Path("periods.json")
lock = Lock()


def load_data():
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


periods = load_data()


def save_data():
    DATA_FILE.write_text(
        json.dumps(periods[-100:], ensure_ascii=False),
        encoding="utf-8"
    )


def analyze(period):
    next_period = (int(period) + 1) % 1000
    next_period = f"{next_period:03d}"

    # Demo rule only; not a real market prediction.
    signal = "BIG" if int(next_period[-1]) >= 5 else "SMALL"

    return {
        "period": period,
        "next_period": next_period,
        "signal": signal,
        "confidence": "N/A",
        "note": "Period-based demo signal, not a guaranteed prediction."
    }


HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>3 Digit BIG SMALL BOT</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;background:#0b1020;color:white;
 font-family:Arial,sans-serif;padding:18px
}
.container{max-width:480px;margin:auto}
h2{text-align:center;color:#42e8bd}
.card{
 background:#171f35;padding:20px;border-radius:15px;
 margin:15px 0;border:1px solid #293653
}
label{display:block;margin-bottom:10px;color:#b9c7df}
input{
 width:100%;padding:15px;border-radius:9px;
 border:1px solid #52617d;background:#0b1020;
 color:white;font-size:22px;text-align:center
}
button{
 width:100%;padding:15px;margin-top:12px;
 border:0;border-radius:9px;background:#16c79a;
 color:#061a16;font-size:17px;font-weight:bold
}
.value{text-align:center;font-size:30px;font-weight:bold;margin:12px}
.big{color:#28e69b}
.small{color:#ffbd59}
.muted{color:#9ba9c2;text-align:center;font-size:13px}
.history{padding:10px;border-bottom:1px solid #293653}
</style>
</head>
<body>
<div class="container">
<h2>3 DIGIT BIG SMALL BOT</h2>

<div class="card">
<label>LAST PERIOD NUMBER (3 DIGIT)</label>
<input id="period" type="text" inputmode="numeric"
 maxlength="3" placeholder="Enter 000 - 999">
<button onclick="addPeriod()">ADD PERIOD</button>
</div>

<div class="card">
<div class="muted">NEXT PERIOD</div>
<div class="value" id="next">---</div>
<div class="muted">NEXT BIG / SMALL SIGNAL</div>
<div class="value" id="signal">WAIT</div>
<div class="muted" id="confidence">Confidence: N/A</div>
<p class="muted" id="note"></p>
</div>

<div class="card">
<h3>PERIOD HISTORY</h3>
<div id="history" class="muted">No periods added</div>
</div>
</div>

<script>
async function refresh(){
 const r=await fetch('/api/state');
 const d=await r.json();

 document.getElementById('next').textContent =
   d.next_period || '---';

 const s=document.getElementById('signal');
 s.textContent=d.signal || 'WAIT';
 s.className='value ' + (d.signal==='BIG'?'big':
   d.signal==='SMALL'?'small':'');

 document.getElementById('confidence').textContent =
   'Confidence: N/A';
 document.getElementById('note').textContent =
   d.note || '';

 const h=document.getElementById('history');
 h.innerHTML='';
 if(!d.history.length){
   h.textContent='No periods added';
 }else{
   d.history.slice().reverse().forEach(p=>{
     const div=document.createElement('div');
     div.className='history';
     div.textContent='Period: '+p.period+
       ' | Next: '+p.next_period+
       ' | Signal: '+p.signal;
     h.appendChild(div);
   });
 }
}

async function addPeriod(){
 const input=document.getElementById('period');
 const p=input.value.trim();

 if(!/^\d{3}$/.test(p)){
   alert('Enter exactly 3 digits');
   return;
 }

 const r=await fetch('/api/add',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({period:p})
 });

 const d=await r.json();
 if(!d.ok){
   alert(d.error || 'Error');
   return;
 }

 input.value='';
 refresh();
}

refresh();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api/state":
            with lock:
                history = list(periods)

            latest = analyze(history[-1]) if history else {}
            self.send_json({
                **latest,
                "history": [
                    analyze(p) for p in history[-30:]
                ]
            })
            return

        if self.path == "/health":
            self.send_json({"status": "active"})
            return

        self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path != "/api/add":
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(size))
            period = str(data.get("period", "")).strip()

            if len(period) != 3 or not period.isdigit():
                self.send_json({
                    "ok": False,
                    "error": "Enter exactly 3 digits"
                }, 400)
                return

            with lock:
                periods.append(period)
                del periods[:-100]
                save_data()

            self.send_json({"ok": True, **analyze(period)})

        except Exception:
            self.send_json({
                "ok": False,
                "error": "Invalid request"
            }, 400)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print("3 DIGIT BOT ACTIVE ON PORT", PORT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()