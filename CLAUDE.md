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
- `ideales.md` (plantilla publica) y la web llevan tildes. El README y CLAUDE.md las evitan salvo la ñ (estilo del usuario), igual que la copia personal del usuario: el parser acepta `Posicion` y `Posición`.
- Redaccion neutral y equilibrada: `test_la_redaccion_esta_equilibrada` compara en cuantas afirmaciones estar de acuerdo coincide con PSOE/Sumar/Podemos o con PP/Vox. Al invertir el sentido de una afirmacion, invertir sus codigos (6 - x).
- Las respuestas de la web se guardan por ID en el navegador: si una pregunta cambia de sentido o de contenido, migrarlas en `web.html` (`INVERTIDAS_V2`, `CAMBIADAS_V2`; para otro cambio, una clave nueva).
- Sugerencias y correcciones solo por X, a @flamyonn (no por GitHub). Un cambio de codigo se acepta solo con fuente verificable.

## Estado (2026-10-06)

- Elecciones generales el 29-11-2026; candidaturas del 21 al 26 de octubre.
- Los programas del 29N no estaban publicados: cuando salgan, revisar la seccion 9 (sobre todo los `~` y los `?` de SALF), pasar las pruebas y regenerar la web.
