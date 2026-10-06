# Votar

Cuestionario de afinidad politica para las elecciones en España: web estatica publica (`web.py` + `web.html` → `public/index.html`) y herramienta local en Python. Comandos y despliegue en [README.md](README.md).

## Reglas

- La decision es de quien responde: presentar rankings, filtros y fuentes, pero no recomendar un partido (tampoco en la web).
- Los codigos de la seccion 9 de `ideales.md` se basan en evidencia y llevan su fuente. Pesa mas lo votado y hecho que el programa. Sin posicion clara: `?`. Poca evidencia: `~`.
- No inventar posiciones de SALF ni de partidos pequeños: si no estan documentadas, `?`.
- `ideales.md` es la plantilla publica (cuestionario en blanco + anexo de partidos) y la unica fuente de la web. Nunca escribir en ella respuestas, resumenes ni resultados de nadie, ni notas que los delaten (como "(NS)" en el anexo). `test_la_plantilla_del_repo_esta_en_blanco` lo vigila.
- Las respuestas personales viven fuera del repo y no se copian aqui.
- Tras cambiar el cuestionario o los codigos: `python3 -m unittest` y `python3 web.py`.
- `og.png` (tarjeta al compartir) repite datos de la web: si cambian el numero de preguntas o la fecha de las elecciones, editar `og.html` y regenerarla.
- La web no hace peticiones de red: sin CDNs, fuentes externas, analitica ni cookies (la CSP de `web.html` lo impide). Las respuestas solo viven en el `localStorage` de quien la usa.
- El calculo de `web.html` (entre `calculo:inicio` y `calculo:fin`) replica `afinidad.py`; una prueba con node comprueba que dan lo mismo.
- El usuario prefiere herramientas rapidas (botones y atajos) a rellenar markdown a mano.
- No desplegar ni subir a remotos sin que el usuario lo pida.
- `ideales.md` y el README evitan tildes salvo la ñ (estilo del usuario). La interfaz de la web si las lleva.

## Estado (2026-10-06)

- Elecciones generales el 29-11-2026; candidaturas del 21 al 26 de octubre.
- Los programas del 29N no estaban publicados: cuando salgan, revisar la seccion 9 (sobre todo los `~` y los `?` de SALF), pasar las pruebas y regenerar la web.
