#!/usr/bin/env python3
"""Afinidad con cada partido a partir de ideales.md (respuestas + anexo 9).

Formula de la seccion 7: 1 - sum(P*|A - partido|) / sum(P*4), excluyendo NS y `?`.
Uso:  python3 afinidad.py ~/mis-ideales.md   -> imprime el resultado
      python3 afinidad.py ~/mis-ideales.md --write  -> ademas lo escribe en la seccion 8
      python3 afinidad.py ~/mis-ideales.md --sin-dudosos -> ignora los codigos con `~` (prueba de robustez)
"""
import re
import sys
from collections import defaultdict

import cuestionario as c

INICIO, FIN = "<!-- afinidad:inicio -->", "<!-- afinidad:fin -->"
MIN_BLOQUE = 3  # items codificados minimos para elegir mejor/peor bloque
MAX_CHOQUES = 6
SIN_DUDOSOS = "--sin-dudosos" in sys.argv


def load():
    lines = c.read()
    mine = {q["id"]: q for q in c.parse(lines) if q["kind"] == "scale" and q["hasP"]}
    parties, codes, annex = [], {}, False
    for line in lines:
        if line.startswith("## "):
            annex = line.startswith("## 9.")
            continue
        if not annex or not line.startswith("|"):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if cells[0] == "ID":
            parties = cells[1:-1]
        elif re.fullmatch(r"[A-Z]+\d+", cells[0]):
            codes[cells[0]] = dict(zip(parties, cells[1:1 + len(parties)]))
    return mine, parties, codes


def value(code):
    if SIN_DUDOSOS and code.endswith("~"):
        return None
    v = code.rstrip("~")
    return int(v) if v in ("1", "2", "3", "4", "5") else None


def affinity(items):
    den = sum(p * 4 for p, _, _ in items)
    return 1 - sum(p * abs(a - x) for p, a, x in items) / den if den else None


def pct(v):
    return "—" if v is None else f"{100 * v:.0f}%"


def short(text, n=48):
    text = re.sub(r"^A: (.*?) B: .*$", r"\1 / B", text)
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def compute():
    mine, parties, codes = load()
    answered = {k: q for k, q in mine.items() if q["a"] in "12345" and q["p"] in ("1", "2", "3")}
    total_w = sum(int(q["p"]) for q in answered.values())
    res = {}
    for party in parties:
        items, blocks, clashes = [], defaultdict(list), []
        for qid, q in answered.items():
            x = value(codes.get(qid, {}).get(party, "?"))
            if x is None:
                continue
            it = (int(q["p"]), int(q["a"]), x)
            items.append(it)
            blocks[q["section"]].append(it)
            if it[0] == 3 and abs(it[1] - x) >= 3:
                clashes.append(f"{qid} ({short(q['text'])}: tu {it[1]}, ellos {x})")
        ranked = sorted((affinity(v), b) for b, v in blocks.items() if len(v) >= MIN_BLOQUE)
        res[party] = dict(
            global_=affinity(items),
            p3=affinity([i for i in items if i[0] == 3]),
            coverage=sum(i[0] for i in items) / total_w if total_w else 0,
            n=len(items),
            blocks={b: affinity(v) for b, v in blocks.items()},
            best=ranked[-1] if ranked else None,
            worst=ranked[0] if ranked else None,
            clashes=clashes,
        )
    sections = list(dict.fromkeys(q["section"] for q in answered.values()))
    return parties, res, sections, len(answered)


def render():
    parties, res, sections, n = compute()
    order = sorted(parties, key=lambda p: -(res[p]["global_"] or 0))
    variante = ", ignorando los codigos con `~`" if SIN_DUDOSOS else ""
    out = [f"> Calculado con `afinidad.py` sobre {n} respuestas (sin NS{variante}). Cobertura = parte del peso P de mis respuestas que el partido tiene codificada; por debajo del 60% el dato es poco fiable.",
           "",
           "| Partido | Afinidad global | Solo P3 | Cobertura | Mejor bloque | Peor bloque |",
           "| --- | --- | --- | --- | --- | --- |"]
    for p in order:
        r = res[p]
        best = f"{r['best'][1]} ({pct(r['best'][0])})" if r["best"] else "—"
        worst = f"{r['worst'][1]} ({pct(r['worst'][0])})" if r["worst"] else "—"
        out.append(f"| {p} | **{pct(r['global_'])}** | {pct(r['p3'])} | {pct(r['coverage'])} ({r['n']}) | {best} | {worst} |")
    out += ["", "Afinidad por bloque:", "", "| Bloque | " + " | ".join(order) + " |",
            "| --- |" + " --- |" * len(order)]
    for s in sections:
        out.append(f"| {s} | " + " | ".join(pct(res[p]["blocks"].get(s)) for p in order) + " |")
    out += ["", "Choques fuertes en lo que decide mi voto (P3, diferencia de 3 o mas):", ""]
    for p in order:
        cl = res[p]["clashes"]
        more = f"; y {len(cl) - MAX_CHOQUES} mas" if len(cl) > MAX_CHOQUES else ""
        out.append(f"- **{p}** ({len(cl)}): " + ("; ".join(cl[:MAX_CHOQUES]) + more if cl else "ninguno"))
    return "\n".join(out)


if __name__ == "__main__":
    if c.es_plantilla():
        sys.exit("ideales.md es la plantilla publica y no tiene respuestas.\n"
                 "Uso: python3 afinidad.py ~/mis-ideales.md [--write]")
    text = render()
    print(text)
    if "--write" in sys.argv:
        lines = c.read()
        i, j = lines.index(INICIO), lines.index(FIN)
        lines[i + 1:j] = text.split("\n")
        c.MD.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n-> escrito en {c.MD.name}, seccion 8")
