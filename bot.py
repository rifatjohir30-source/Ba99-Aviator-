"""
<!DOCTYPE html>
<htmlrecentd>
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
   d.