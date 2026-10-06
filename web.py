#!/usr/bin/env python3
"""Genera la version web del cuestionario: un solo public/index.html, sin servidor.

Uso:  python3 web.py   -> public/index.html y public/og.png (imagen de la tarjeta al compartir)
Lee las preguntas y el anexo de partidos de ideales.md (nunca respuestas). Quien
la use responde en su navegador: no se envia nada a ningun sitio.
"""
import json
import re
import shutil
import sys
from pathlib import Path

import afinidad as a
import cuestionario as c

PAGINA = Path(__file__).with_name("web.html")
TARJETA = Path(__file__).with_name("og.png")
SALIDA = Path(__file__).with_name("public") / "index.html"
HUECO = "/*DATOS*/null"
FUENTE = re.compile(r"^\[(\d+)\] (.*?)(?: ·)?$")


def annex():
    """Base de cada codigo, notas de criterio y fuentes de la seccion 9."""
    bases, notes, sources, inside, after = {}, [], [], False, False
    for line in c.read():
        if line.startswith("## "):
            inside = line.startswith("## 9.")
        elif not inside:
            continue
        elif line.startswith("> ") and "python3" not in line:
            notes.append(line[2:])
        elif line.startswith("|"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if re.fullmatch(r"[A-Z]+\d+", cells[0]):
                bases[cells[0]] = cells[-1]
        elif line == "Fuentes:":
            after = True
        elif after and (m := FUENTE.match(line)):
            sources.append(dict(n=int(m.group(1)), md=m.group(2)))
    return bases, notes, sources


def data():
    mine, parties, codes = a.load()
    bases, notes, sources = annex()
    questions = [dict(id=k, bloque=q["section"], texto=q["text"], modo=q["mode"],
                      codigos=codes[k], base=bases.get(k, "")) for k, q in mine.items()]
    return dict(partidos=parties, preguntas=questions, criterios=notes, fuentes=sources)


def build(dest=SALIDA):
    page = PAGINA.read_text(encoding="utf-8")
    if page.count(HUECO) != 1:
        sys.exit(f"{PAGINA.name} debe contener {HUECO} una sola vez")
    blob = json.dumps(data(), ensure_ascii=False).replace("</", "<\\/")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page.replace(HUECO, blob), encoding="utf-8")
    shutil.copy(TARJETA, dest.with_name(TARJETA.name))
    return dest


if __name__ == "__main__":
    print(f"-> {build()}  (se puede abrir directamente en el navegador)")
