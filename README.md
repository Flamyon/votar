# Votar

Cuestionario para comparar tus posiciones politicas con las de los partidos españoles de forma verificable y sin depender de la identidad de partido: 119 afirmaciones con acuerdo (1-5) y peso (1-3), y la posicion de cada partido codificada a partir de lo que ha votado y hecho, con su fuente.

Se puede usar de dos formas:

- **Web**, para cualquiera: una sola pagina estatica. Las respuestas se quedan en el navegador de quien la usa. No hay servidor, cuentas, cookies ni analitica, y la politica de seguridad (CSP) de la pagina le impide enviar nada.
- **Local**, con Python: se responde sobre un .md propio y la afinidad se calcula en la terminal.

Python 3.8 o superior, solo con la biblioteca estandar: no hay nada que instalar.

## Web

```bash
python3 web.py   # genera public/index.html a partir de ideales.md
```

`public/index.html` se puede abrir directamente en el navegador. Muestra la afinidad global con cada partido, la afinidad por bloques, los choques en lo que mas pesa y el detalle pregunta a pregunta con la base y la fuente de cada codigo. Tiene la opcion de ignorar los codigos poco seguros (`~`).

### Desplegar

- **GitHub Pages:** subir el repo a GitHub y activar *Settings → Pages → Source: GitHub Actions*. El flujo [.github/workflows/web.yml](.github/workflows/web.yml) pasa las pruebas, genera la pagina y la publica en cada push a `main`. Es gratis con el repo publico; con un repo privado, GitHub Pages necesita un plan de pago.
- **Netlify o Cloudflare Pages:** comando de build `python3 web.py` y carpeta de publicacion `public`.
- **Cualquier hosting estatico:** generar la pagina y subir `public/index.html`.

## Uso local

```bash
python3 cuestionario.py --vaciar=~/mis-ideales.md   # tu copia en blanco, fuera del repo
python3 cuestionario.py ~/mis-ideales.md            # responder: abre http://127.0.0.1:8765 y guarda al momento
python3 afinidad.py ~/mis-ideales.md                # ver la afinidad con cada partido
python3 afinidad.py ~/mis-ideales.md --write        # ... y escribirla en la seccion 8 de tu copia
python3 afinidad.py ~/mis-ideales.md --sin-dudosos  # repetir el calculo sin los codigos poco seguros (~)
python3 -m unittest                                 # pruebas (sobre copias temporales)
```

Los dos scripts se niegan a escribir en `ideales.md`, la plantilla del repo.

En el cuestionario: **1-5** o **N** para el acuerdo, **1-3** para el peso, **Esc** para volver atras, **← →** para moverse y **Enter** para guardar. Se puede parar en cualquier momento: al volver empieza por la primera pregunta sin responder. Ctrl+C cierra el servidor. Si el puerto 8765 esta ocupado: `PORT=8800 python3 cuestionario.py ~/mis-ideales.md`.

La copia local tiene el cuestionario completo (tambien valores, prioridades y criterios de voto). La web solo pregunta las 119 afirmaciones que entran en el calculo.

## Metodo

1. Responder sin mirar antes las posiciones de los partidos.
2. Cada partido esta codificado en la seccion 9 de `ideales.md` con la misma escala 1-5: `?` si no tiene posicion clara (se excluye) y `~` si hay poca evidencia. Cada codigo lleva su base y, si hace falta, una fuente numerada al final de la tabla.
3. Afinidad = `1 - Σ P·|A - partido| / Σ P·4`, excluyendo NS y `?`. Tambien por bloque y solo con lo de peso 3.
4. Lo que no mide el calculo (corrupcion, pactos, lineas rojas, voto util en tu provincia) lo valora cada uno.

## Actualizar las posiciones de los partidos

Editar la tabla de la seccion 9 de `ideales.md` y despues:

```bash
python3 -m unittest && python3 web.py
```

Con GitHub Pages basta con hacer push. Las copias locales llevan su propio anexo: para recalcular con los codigos nuevos, copiar la seccion 9 a tu copia y volver a pasar `afinidad.py --write`.

## Archivos

| Archivo | Que hace |
| --- | --- |
| `ideales.md` | Plantilla publica: cuestionario en blanco y anexo de partidos con fuentes. Fuente unica de la web |
| `web.py` | Genera `public/index.html` con las preguntas y los codigos de `ideales.md` |
| `web.html` | La pagina de la web: preguntas, calculo y resultados, todo en el navegador |
| `cuestionario.py` | Servidor local que muestra las preguntas con botones y escribe en tu .md |
| `afinidad.py` | Calcula la afinidad global, por bloque y los choques en lo que mas pesa |
| `test_votar.py` | Pruebas: plantilla en blanco, lectura y escritura del .md, y que la web calcula igual que `afinidad.py` |

## Privacidad

Las respuestas son opiniones politicas.

- `ideales.md` no lleva respuestas de nadie: una prueba falla si alguien guarda respuestas, resumen o resultados en la plantilla.
- La web no carga recursos externos ni envia datos. El progreso se guarda en el `localStorage` del navegador y se borra con *Borrar mis respuestas*.
- El servidor local solo escucha en `127.0.0.1`.
