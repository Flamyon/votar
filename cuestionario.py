#!/usr/bin/env python3
"""Cuestionario de ideales.md pregunta a pregunta, con botones.

Uso:  python3 cuestionario.py --vaciar=~/mis-ideales.md  ->  copia en blanco, fuera del repo
      python3 cuestionario.py ~/mis-ideales.md           ->  http://127.0.0.1:8765
Cada respuesta se escribe al momento en el .md (no hay otro estado).
ideales.md es la plantilla publica (cuestionario + anexo de partidos): nunca se responde sobre ella.
"""
import datetime
import json
import os
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_args = [a for a in sys.argv[1:] if not a.startswith("-")]
PLANTILLA = Path(__file__).with_name("ideales.md")
MD = Path(_args[0]).expanduser() if _args else PLANTILLA
PORT = int(os.environ.get("PORT", 8765))
LOCK = threading.Lock()

SCALE = re.compile(r"^- \*\*([A-Z]+\d+)\.\*\* (.*?) — (A|Posici[oó]n): (\S+)(?: · P: (\S+))?(?: — Nota: (.*))?$")
CV_LINE = re.compile(r"^- \*\*(CV\d+)\.\*\* (.*)$")
ANSWERED = re.compile(r"^(.*?) \*\*([^*]+)\*\*$")
RANK = re.compile(r"^- (_|\d+) (.+)$")
POINTS = re.compile(r"^  - (_|\d+) (.+)$")
PRIO = re.compile(r"^(\d)\.(?: (.*))?$")
H2 = re.compile(r"^## (\d+)\. (.*)$")
H3 = re.compile(r"^### (\d+\.\d+) (.*)$")
DATE = re.compile(r"Actualizado: \d{4}-\d{2}-\d{2}")


def clean(v):
    return str(v or "").replace("\n", " ").strip()


def num(v):
    v = clean(v)
    return v if v.isdigit() else "_"


def split_answer(rest):
    m = ANSWERED.match(rest)
    return (m.group(1), m.group(2)) if m else (rest, "")


def options_of(prompt):
    s = prompt.rstrip(":").strip()
    for sep in ("? ", ": "):
        if sep in s:
            s = s.rsplit(sep, 1)[1]
            break
    s = s.strip("()")
    return s.split(" / ") if " / " in s else []


def run_length(lines, i, rx):
    n = 0
    while i + n < len(lines) and rx.match(lines[i + n]):
        n += 1
    return n


def parse(lines):
    qs, h2, h3, quote, ctx = [], ("", ""), None, "", 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if m := H2.match(line):
            h2, h3 = m.groups(), None
        elif m := H3.match(line):
            h3 = m.groups()
        elif line.startswith("> "):
            quote = line[2:]
        else:
            q = None
            if m := SCALE.match(line):
                qid, text, mode, a, p, nota = m.groups()
                q = dict(id=qid, kind="scale", text=text, mode=mode, a=a,
                         hasP=p is not None, p=p or "_", nota=nota or "", line=i)
            elif h2[0] == "2" and line.startswith("- "):
                ctx += 1
                prompt, value = split_answer(line[2:])
                q = dict(id=f"CTX{ctx}", kind="text", bold=False, prompt=prompt,
                         value=value, options=options_of(prompt), line=i)
            elif h3 and h3[0] == "3.1" and RANK.match(line):
                n = run_length(lines, i, RANK)
                q = dict(id="VALORES", kind="rank", prompt=h3[1], lines=list(range(i, i + n)),
                         items=[dict(zip(("value", "label"), RANK.match(lines[j]).groups()))
                                for j in range(i, i + n)])
                i += n - 1
            elif h2[0] == "5" and PRIO.match(line):
                n = run_length(lines, i, PRIO)
                q = dict(id="PRIORIDADES", kind="list", prompt=quote, lines=list(range(i, i + n)),
                         items=[PRIO.match(lines[j]).group(2) or "" for j in range(i, i + n)])
                i += n - 1
            elif m := CV_LINE.match(line):
                qid, rest = m.groups()
                n = run_length(lines, i + 1, POINTS)
                if n:
                    q = dict(id=qid, kind="points", prompt=rest, lines=list(range(i + 1, i + 1 + n)),
                             items=[dict(zip(("value", "label"), POINTS.match(lines[j]).groups()))
                                    for j in range(i + 1, i + 1 + n)])
                    i += n
                else:
                    prompt, value = split_answer(rest)
                    q = dict(id=qid, kind="text", bold=True, prompt=prompt, value=value,
                             options=options_of(prompt), line=i)
            if q:
                q["section"] = f"{h3[0]} {h3[1]}" if h3 else f"{h2[0]}. {h2[1]}"
                qs.append(q)
        i += 1
    return qs


def apply(q, d):
    """Devuelve {indice_de_linea: linea_nueva} para la respuesta d."""
    k = q["kind"]
    if k == "scale":
        a = d.get("a") if d.get("a") in ("1", "2", "3", "4", "5", "NS") else "_"
        p = d.get("p") if d.get("p") in ("1", "2", "3") else "_"
        s = f"- **{q['id']}.** {q['text']} — {q['mode']}: {a}"
        if q["hasP"]:
            s += f" · P: {p}"
        if nota := clean(d.get("nota")):
            s += f" — Nota: {nota}"
        return {q["line"]: s}
    if k == "text":
        v = clean(d.get("value")).replace("*", "")
        head = f"- **{q['id']}.** " if q["bold"] else "- "
        return {q["line"]: head + q["prompt"] + (f" **{v}**" if v else "")}
    vals = list(d.get("values", []))
    if k == "rank":
        return {j: f"- {num(v)} {it['label']}" for j, it, v in zip(q["lines"], q["items"], vals)}
    if k == "points":
        return {j: f"  - {num(v)} {it['label']}" for j, it, v in zip(q["lines"], q["items"], vals)}
    if k == "list":
        return {j: f"{n}." + (f" {clean(v)}" if clean(v) else "")
                for n, (j, v) in enumerate(zip(q["lines"], vals), 1)}
    return {}


def es_plantilla():
    return MD.resolve() == PLANTILLA.resolve()


def read():
    return MD.read_text(encoding="utf-8").split("\n")


def save(data):
    with LOCK:
        lines = read()
        q = next((q for q in parse(lines) if q["id"] == data.get("id")), None)
        if not q:
            return None
        for j, s in apply(q, data).items():
            lines[j] = s
        today = datetime.date.today().isoformat()
        lines = [DATE.sub(f"Actualizado: {today}", l) if l.startswith("> Documento vivo") else l
                 for l in lines]
        MD.write_text("\n".join(lines), encoding="utf-8")
        return next(x for x in parse(lines) if x["id"] == q["id"])


RESUMEN_VACIO = """> Se rellena al final, a partir de las respuestas.

- Eje económico (Estado/mercado):
- Eje social (libertades/valores):
- Eje territorial:
- Europa y política exterior:
- Temas que más pesan en mi voto:
- Líneas rojas:
"""


def blank(dest):
    """Copia el .md con todas las respuestas, el resumen y los resultados vacios (el anexo se conserva)."""
    lines = read()
    for q in parse(lines):
        for j, s in apply(q, {"values": [""] * len(q.get("items", []))}).items():
            lines[j] = s
    text = "\n".join(lines)
    text = re.sub(r"(## 1\. [^\n]*\n\n).*?(?=\n## 2\. )", lambda m: m.group(1) + RESUMEN_VACIO, text, flags=re.S)
    text = re.sub(r"(## 8\. [^\n]*\n\n).*?(?=\n## 9\. )",
                  lambda m: m.group(1) + "<!-- afinidad:inicio -->\n<!-- afinidad:fin -->\n", text, flags=re.S)
    Path(dest).write_text(text, encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send(200, PAGE.replace("{{FILE}}", MD.name), "text/html")
        elif self.path == "/api/q":
            self.send(200, json.dumps(parse(read()), ensure_ascii=False))
        else:
            self.send(404, "{}")

    def do_POST(self):
        if self.path != "/api/a":
            return self.send(404, "{}")
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        q = save(data)
        self.send(200, json.dumps(q, ensure_ascii=False)) if q else self.send(404, "{}")

    def log_message(self, *args):
        pass


PAGE = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cuestionario de ideales</title>
<style>
:root{--bg:#f5f4f0;--card:#fff;--fg:#1d1d1f;--mut:#6b6b70;--line:#dcdad3;--acc:#2f63d0;--acc-fg:#fff;--ok:#2e7d4f;--warn:#b3361f}
@media (prefers-color-scheme:dark){:root{--bg:#131315;--card:#1d1d21;--fg:#ececef;--mut:#9b9ba3;--line:#34343b;--acc:#5b8def;--acc-fg:#fff;--ok:#5cc489;--warn:#ef7b67}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:780px;margin:0 auto;padding:20px 16px 60px}
.top{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:10px;color:var(--mut);font-size:14px}
select{font:inherit;font-size:14px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);max-width:100%}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden;margin-bottom:16px}
.bar>div{height:100%;background:var(--acc);transition:width .2s}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px}
.sec{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin-bottom:8px}
.q{font-size:21px;font-weight:600;margin:0 0 18px;text-wrap:pretty}
.ab{display:grid;gap:10px;margin:-4px 0 6px}
.ab div{padding:10px 12px;border:1px solid var(--line);border-radius:10px}
.ab b{color:var(--acc);margin-right:6px}
.lbl{font-size:13px;color:var(--mut);margin:16px 0 6px}
.row{display:flex;flex-wrap:wrap;gap:8px}
.col{display:grid;gap:8px}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:10px;padding:9px 14px;min-height:44px}
button:hover{border-color:var(--acc)}
button.on{background:var(--acc);color:var(--acc-fg);border-color:var(--acc)}
button.pri{background:var(--acc);color:var(--acc-fg);border-color:var(--acc)}
.dim{opacity:.45}
.opt{flex:1 1 110px;text-align:left}
.opt span{font-weight:700}
.opt small{display:block;font-size:12px;opacity:.8}
.item{text-align:left;display:flex;gap:10px;align-items:center}
.item b{display:inline-block;min-width:1.6em;text-align:center}
.pt{display:flex;gap:10px;align-items:center}
input[type=text],input[type=number]{font:inherit;width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--fg)}
input[type=number]{width:90px;flex:none}
.nav{display:flex;justify-content:space-between;gap:8px;margin-top:14px;flex-wrap:wrap}
.hint{color:var(--mut);font-size:13px;margin-top:14px}
.ok{color:var(--ok)}.warn{color:var(--warn)}
#toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--fg);color:var(--bg);padding:8px 16px;border-radius:20px;font-size:14px;opacity:0;transition:opacity .15s;pointer-events:none}
#toast.show{opacity:.92}#toast.bad{background:var(--warn);color:#fff}
</style></head><body><main>
<div class="top"><span id="prog"></span><select id="jump"></select></div>
<div class="bar"><div id="bar"></div></div>
<div class="card" id="card">Cargando…</div>
<div class="nav"><button id="prev">← Anterior</button><button id="skip">Saltar →</button><button id="open">Siguiente pendiente</button></div>
<div class="hint">Se guarda al momento en <b>{{FILE}}</b>. Atajos: <b>1-5</b> / <b>N</b> responder · <b>1-3</b> peso · <b>Esc</b> volver al acuerdo · <b>← →</b> moverse · <b>Enter</b> guardar.</div>
</main><div id="toast"></div>
<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const AGREE=["Muy en desacuerdo","En desacuerdo","Neutral","De acuerdo","Muy de acuerdo","Sin opinión"];
const DIL=["Totalmente A","","Equilibrio","","Totalmente B","Sin opinión"];
const PESO=["Me importa poco","Me importa","Puede decidir mi voto"];
let Q=[],i=0,st={};

function done(q){
  if(q.kind==="scale")return q.a!=="_"&&(q.a==="NS"||!q.hasP||q.p!=="_");
  if(q.kind==="text")return !!q.value;
  if(q.kind==="rank")return q.items.every(x=>x.value!=="_");
  if(q.kind==="points")return q.items.some(x=>x.value!=="_");
  return q.items.some(Boolean);
}
async function load(){
  Q=await (await fetch("/api/q")).json();
  const k=Q.findIndex(q=>!done(q));
  go(k<0?Q.length:k);
}
function go(k){i=Math.max(0,Math.min(k,Q.length));st={};render();}
function nextOpen(){
  let k=Q.findIndex((q,j)=>j>i&&!done(q));
  if(k<0)k=Q.findIndex(q=>!done(q));
  go(k<0?Q.length:k);
}
async function save(data){
  let r;
  try{r=await fetch("/api/a",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:Q[i].id,...data})});}catch(e){}
  if(!r||!r.ok){toast("No se pudo guardar. ¿Sigue el script en marcha?",true);return;}
  Q[i]=await r.json();toast("Guardado");nextOpen();
}
let tt;function toast(m,bad){const t=$("#toast");t.textContent=m;t.className="show"+(bad?" bad":"");clearTimeout(tt);tt=setTimeout(()=>t.className="",1100);}

const K={
 scale:{
  html(q){
    const dl=q.id.startsWith("DL");
    let labels=q.mode==="A"?AGREE:dl?DIL:null,text=q.text;
    if(!labels){
      labels=["","","","","","Sin opinión"];
      for(const m of q.text.matchAll(/(\d) = ([^·]+?)(?=\s*·|\.?$)/g))labels[m[1]-1]=m[2];
      text=q.text.split(/\s*1 = /)[0];
    }
    const a=st.a??q.a,p=st.p??q.p,step=st.step||"a";
    let h="";
    if(dl){const m=q.text.match(/^A: (.*?) B: (.*)$/)||["",q.text,""];h+=`<p class="q">¿Hacia dónde te inclinas?</p><div class="ab"><div><b>A</b>${esc(m[1])}</div><div><b>B</b>${esc(m[2])}</div></div>`;}
    else h+=`<p class="q">${esc(text)}</p>`;
    h+=`<div class="lbl">${q.mode==="A"?"Acuerdo":"Posición"}</div><div class="row">`+["1","2","3","4","5","NS"].map((v,j)=>`<button class="opt ${a===v?"on":""} ${q.hasP&&step==="p"?"dim":""}" data-a="${v}"><span>${v}</span>${labels[j]?`<small>${esc(labels[j])}</small>`:""}</button>`).join("")+`</div>`;
    if(q.hasP)h+=`<div class="lbl">Peso</div><div class="row">`+["1","2","3"].map((v,j)=>`<button class="opt ${p===v?"on":""} ${step==="a"?"dim":""}" data-p="${v}"><span>${v}</span><small>${PESO[j]}</small></button>`).join("")+`</div>`;
    h+=`<div class="lbl">Nota (opcional)</div><input id="nota" type="text" value="${esc(st.nota??q.nota)}" placeholder="Matices: «sí, pero solo si…», o si la pregunta está mal planteada">`;
    return h;
  },
  click(q,b){if(b.dataset.a)this.pickA(q,b.dataset.a);else if(b.dataset.p)this.pickP(q,b.dataset.p);},
  key(q,k){
    const step=st.step||"a";
    if(step==="a"&&/^[1-5]$/.test(k))this.pickA(q,k);
    else if(step==="a"&&k.toLowerCase()==="n")this.pickA(q,"NS");
    else if(step==="p"&&/^[1-3]$/.test(k))this.pickP(q,k);
    else if(step==="p"&&(k==="Escape"||k==="Backspace")){st.step="a";render();}
    else return false;
    return true;
  },
  pickA(q,v){st.a=v;if(v==="NS"||!q.hasP)this.save(q);else{st.step="p";render();}},
  pickP(q,v){st.p=v;if((st.a??q.a)==="_"){st.step="a";render();}else this.save(q);},
  save(q){save({a:st.a??q.a,p:st.p??q.p,nota:$("#nota").value});},
  enter(q){const a=st.a??q.a,p=st.p??q.p;if(a!=="_"&&(a==="NS"||!q.hasP||p!=="_"))this.save(q);}
 },
 text:{
  html(q){
    let h=`<p class="q">${esc(q.prompt)}</p>`;
    if(q.options.length)h+=`<div class="row">`+q.options.map((o,j)=>`<button class="opt ${q.value===o?"on":""}" data-o="${esc(o)}"><span>${j+1}</span><small>${esc(o)}</small></button>`).join("")+`</div><div class="lbl">u otra respuesta</div>`;
    h+=`<div class="row"><input id="txt" type="text" value="${esc(q.value)}" placeholder="Escribe y pulsa Enter" style="flex:1 1 240px;width:auto"><button class="pri" data-save="1">Guardar</button></div>`;
    return h;
  },
  click(q,b){if(b.dataset.o!==undefined)save({value:b.dataset.o});else if(b.dataset.save)save({value:$("#txt").value});},
  key(q,k){const o=q.options[+k-1];if(/^[1-9]$/.test(k)&&o!==undefined){save({value:o});return true;}return false;},
  enter(){save({value:$("#txt").value});},
  focus(q){if(!q.options.length)$("#txt").focus();}
 },
 rank:{
  html(q){
    if(!st.order)st.order=q.items.map((x,j)=>[+x.value,j]).filter(x=>x[0]).sort((a,b)=>a[0]-b[0]).map(x=>x[1]);
    return `<p class="q">${esc(q.prompt)}</p><div class="lbl">Pulsa en orden, de lo que más pesa a lo que menos. Al marcar el último se guarda. Pulsar uno marcado lo desmarca.</div><div class="col">`+q.items.map((x,j)=>{const r=st.order.indexOf(j);return `<button class="item ${r>=0?"on":""}" data-j="${j}"><b>${r>=0?r+1:"·"}</b>${esc(x.label)}</button>`;}).join("")+`</div><div class="row" style="margin-top:12px"><button data-reset="1">Reiniciar</button></div>`;
  },
  click(q,b){
    if(b.dataset.reset){st.order=[];render();return;}
    const j=+b.dataset.j,r=st.order.indexOf(j);
    if(r>=0)st.order.splice(r,1);else st.order.push(j);
    if(st.order.length===q.items.length)save({values:q.items.map((_,j)=>st.order.indexOf(j)+1)});
    else render();
  },
  key(){return false;},enter(){}
 },
 points:{
  html(q){
    return `<p class="q">${esc(q.prompt)}</p><div class="col">`+q.items.map((x,j)=>`<label class="pt"><input type="number" min="0" max="100" step="5" data-j="${j}" value="${x.value==="_"?"":x.value}"><span>${esc(x.label)}</span></label>`).join("")+`</div><div class="row" style="margin-top:12px;align-items:center;gap:14px"><button class="pri" data-save="1">Guardar</button><span id="sum"></span></div>`;
  },
  vals(){return [...document.querySelectorAll("input[data-j]")].map(e=>e.value.trim());},
  input(){const s=this.vals().reduce((a,v)=>a+(+v||0),0),e=$("#sum");e.textContent=`Suma: ${s} / 100`;e.className=s===100?"ok":"warn";},
  focus(){this.input();},
  click(q,b){if(b.dataset.save)save({values:this.vals()});},
  key(){return false;},enter(){save({values:this.vals()});}
 },
 list:{
  html(q){return `<p class="q">${esc(q.prompt)}</p><div class="col">`+q.items.map((v,j)=>`<input type="text" data-j="${j}" value="${esc(v)}" placeholder="${j+1}.">`).join("")+`</div><div class="row" style="margin-top:12px"><button class="pri" data-save="1">Guardar</button></div>`;},
  vals(){return [...document.querySelectorAll("input[data-j]")].map(e=>e.value);},
  click(q,b){if(b.dataset.save)save({values:this.vals()});},
  key(){return false;},
  enter(q,t){const n=t.dataset&&t.dataset.j!==undefined?document.querySelector(`input[data-j="${+t.dataset.j+1}"]`):null;if(n)n.focus();else save({values:this.vals()});},
  focus(){document.querySelector("input[data-j]").focus();}
 }
};

function render(){
  const n=Q.filter(done).length;
  $("#prog").textContent=`${n} / ${Q.length} respondidas`;
  $("#bar").style.width=`${Q.length?100*n/Q.length:0}%`;
  const secs=[];
  Q.forEach((q,j)=>{let x=secs.find(z=>z.name===q.section);if(!x)secs.push(x={name:q.section,first:j,open:-1,n:0,d:0});x.n++;if(done(q))x.d++;else if(x.open<0)x.open=j;});
  $("#jump").innerHTML=secs.map(x=>`<option value="${x.open<0?x.first:x.open}" ${Q[i]&&Q[i].section===x.name?"selected":""}>${esc(x.name)} (${x.d}/${x.n})</option>`).join("");
  const c=$("#card");
  if(i>=Q.length){
    c.innerHTML=n===Q.length?`<p class="q">Cuestionario completo ✔</p><p>Todo está guardado en <b>{{FILE}}</b>. Pídele a Claude que rellene el resumen y haga la comparación con los partidos.</p>`
      :`<p class="q">Has llegado al final</p><p>Quedan ${Q.length-n} preguntas sin responder.</p><button class="pri" onclick="go(Q.findIndex(q=>!done(q)))">Ir a la primera pendiente</button>`;
    return;
  }
  const q=Q[i],k=K[q.kind];
  c.innerHTML=`<div class="sec">${esc(q.section)} · ${esc(q.id)} · ${i+1}/${Q.length}${done(q)?' · <span class="ok">respondida</span>':""}</div>`+k.html(q);
  if(k.focus)k.focus(q);
}

const card=$("#card");
card.addEventListener("click",e=>{const b=e.target.closest("button");if(b&&i<Q.length)K[Q[i].kind].click(Q[i],b);});
card.addEventListener("input",e=>{if(e.target.id==="nota")st.nota=e.target.value;const k=Q[i]&&K[Q[i].kind];if(k&&k.input)k.input();});
document.addEventListener("keydown",e=>{
  if(e.ctrlKey||e.metaKey||e.altKey)return;
  const t=e.target,inInput=t.tagName==="INPUT"||t.tagName==="SELECT";
  if(!inInput&&e.key==="ArrowLeft"){go(i-1);return;}
  if(!inInput&&e.key==="ArrowRight"){go(i+1);return;}
  if(i>=Q.length)return;
  const q=Q[i],k=K[q.kind];
  if(e.key==="Enter"){if(t.tagName==="BUTTON")return;e.preventDefault();k.enter(q,t);return;}
  if(inInput){if(e.key==="Escape")t.blur();return;}
  if(k.key(q,e.key))e.preventDefault();
});
$("#prev").onclick=()=>go(i-1);
$("#skip").onclick=()=>go(i+1);
$("#open").onclick=()=>nextOpen();
$("#jump").onchange=e=>go(+e.target.value);
load();
</script></body></html>
"""

if __name__ == "__main__":
    if not MD.exists():
        sys.exit(f"No existe {MD}")
    if dest := next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--vaciar=")), None):
        dest = Path(dest).expanduser()
        if dest.exists():
            sys.exit(f"{dest} ya existe; elige otro nombre")
        blank(dest)
        print(f"Creado {dest} en blanco. Para responderlo: python3 cuestionario.py {dest}")
        sys.exit(0)
    if es_plantilla():
        sys.exit("ideales.md es la plantilla publica: no se responde sobre ella.\n"
                 "Crea tu copia fuera del repo:  python3 cuestionario.py --vaciar=~/mis-ideales.md\n"
                 "y respondela:                  python3 cuestionario.py ~/mis-ideales.md")
    url = f"http://127.0.0.1:{PORT}"
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Cuestionario en {url}  (guardando en {MD})  · Ctrl+C para salir")
    if not os.environ.get("NO_BROWSER"):
        threading.Timer(0.6, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
