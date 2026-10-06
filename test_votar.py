"""Comprueba que los scripts leen y escriben el .md sin estropearlo y que la web calcula igual.

Uso: python3 -m unittest   (trabaja sobre copias temporales rellenadas con respuestas inventadas)
"""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import afinidad as a
import cuestionario as c
import web

ORIGINAL = Path(__file__).with_name("ideales.md")


def rellenar(md):
    """Respuestas inventadas y deterministas, con algun NS."""
    lines = md.read_text(encoding="utf-8").split("\n")
    for n, q in enumerate(q for q in c.parse(lines) if q["kind"] == "scale"):
        d = dict(a="NS") if n % 11 == 5 else dict(a=str(1 + n * 7 % 5), p=str(1 + n % 3))
        for j, s in c.apply(q, d).items():
            lines[j] = s
    md.write_text("\n".join(lines), encoding="utf-8")


class TestVotar(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.md = self.dir / "ideales.md"
        shutil.copy(ORIGINAL, self.md)
        rellenar(self.md)
        self.prev, c.MD = c.MD, self.md

    def tearDown(self):
        c.MD = self.prev
        a.SIN_DUDOSOS = False
        shutil.rmtree(self.dir)

    def test_la_plantilla_del_repo_esta_en_blanco(self):
        blank = self.dir / "blanco.md"
        c.MD = ORIGINAL
        c.blank(blank)
        self.assertEqual(blank.read_text(encoding="utf-8"), ORIGINAL.read_text(encoding="utf-8"),
                         "ideales.md tiene respuestas, resumen o resultados: no deben subirse al repo")

    def test_reescribir_sin_cambios_deja_el_fichero_igual(self):
        lines = c.read()
        for q in c.parse(lines):
            d = dict(a=q.get("a"), p=q.get("p"), nota=q.get("nota"), value=q.get("value"),
                     values=[x["value"] if isinstance(x, dict) else x for x in q.get("items", [])])
            for j, s in c.apply(q, d).items():
                self.assertEqual(lines[j], s, q["id"])

    def test_guardar_una_respuesta(self):
        before = c.read()
        c.save(dict(id="F1", a="3", p="2", nota="prueba"))
        after = c.read()
        q = next(q for q in c.parse(after) if q["id"] == "F1")
        self.assertEqual((q["a"], q["p"], q["nota"]), ("3", "2", "prueba"))
        changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
        self.assertTrue(set(changed) <= {q["line"], 2})  # la respuesta y la fecha de "Actualizado"

    def test_todas_las_preguntas_estan_codificadas(self):
        mine, parties, codes = a.load()
        self.assertEqual(len(parties), 6)
        self.assertEqual([k for k in mine if k not in codes], [])
        self.assertTrue(all(len(v) == len(parties) for v in codes.values()))

    def test_afinidad_entre_0_y_1(self):
        _, res, _, _ = a.compute()
        for party, r in res.items():
            self.assertTrue(0 <= r["global_"] <= 1, party)

    def test_vaciar_deja_todo_sin_responder_y_conserva_el_anexo(self):
        blank = self.dir / "nuevo.md"
        c.blank(blank)
        c.MD = blank
        qs = c.parse(c.read())
        self.assertEqual(len(qs), len(c.parse(self.md.read_text(encoding="utf-8").split("\n"))))
        self.assertTrue(all(q["a"] == "_" and q["p"] == "_" for q in qs if q["kind"] == "scale"))
        self.assertTrue(all(not q["value"] for q in qs if q["kind"] == "text"))
        self.assertEqual(len(a.load()[2]), 119)
        text = blank.read_text(encoding="utf-8")
        self.assertIn("- Eje economico (Estado/mercado):\n", text)
        self.assertNotIn("### Lectura", text)

    def test_la_web_lleva_preguntas_y_fuentes_pero_no_respuestas(self):
        out = web.build(self.dir / "public" / "index.html")
        html = out.read_text(encoding="utf-8")
        self.assertNotIn(web.HUECO, html)
        d = web.data()
        self.assertEqual(len(d["preguntas"]), 119)
        self.assertEqual(d["partidos"], a.load()[1])
        self.assertTrue(all(set(q) == {"id", "bloque", "texto", "modo", "codigos", "base"} for q in d["preguntas"]))
        cited = {int(n) for q in d["preguntas"] for n in re.findall(r"\[(\d+)\]", q["base"])}
        self.assertTrue(cited <= {f["n"] for f in d["fuentes"]})

    @unittest.skipUnless(shutil.which("node"), "hace falta node")
    def test_la_web_calcula_igual_que_afinidad_py(self):
        js = re.search(r"// calculo:inicio.*?// calculo:fin", web.PAGINA.read_text(encoding="utf-8"), re.S).group(0)
        resp = {q["id"]: dict(a=q["a"], p=q["p"]) for q in c.parse(c.read()) if q["kind"] == "scale"}
        for sin_dudosos in (False, True):
            a.SIN_DUDOSOS = sin_dudosos
            _, res, _, n = a.compute()
            prog = (js + f"\nconst D = {json.dumps(web.data())}, R = {json.dumps(resp)};"
                    f"\nconsole.log(JSON.stringify(calcular(D.preguntas, D.partidos, R, {json.dumps(sin_dudosos)})));")
            out = json.loads(subprocess.run(["node", "-e", prog], capture_output=True, text=True, check=True).stdout)
            self.assertEqual(out["n"], n)
            for party, r in res.items():
                j = out["res"][party]
                self.assertAlmostEqual(r["global_"], j["global"], places=12)
                self.assertAlmostEqual(r["p3"], j["p3"], places=12)
                self.assertAlmostEqual(r["coverage"], j["cobertura"], places=12)
                self.assertEqual(r["n"], j["n"])
                self.assertEqual(list(r["best"] or []) or None, j["mejor"])
                self.assertEqual(list(r["worst"] or []) or None, j["peor"])
                self.assertEqual(len(r["clashes"]), len(j["choques"]))


if __name__ == "__main__":
    unittest.main()
