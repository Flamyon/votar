# Votar

Cuestionario para comparar tus posiciones politicas con las de los partidos españoles de forma verificable y sin depender de la identidad de partido: 119 afirmaciones con acuerdo (1-5) y peso (1-3), y la posicion de cada partido codificada a partir de lo que ha votado y hecho, con su fuente.

Se puede usar de dos formas:

- **Web**, para cualquiera: una sola pagina estatica. Las respuestas se quedan en el navegador de quien la usa. No hay servidor, cuentas, cookies ni analitica, y la politica de seguridad (CSP) de la pagina le impide enviar nada.
- **Local**, con Python: se responde sobre un .md propio y la afinidad se calcula en la terminal.

Python 3.8 o superior, solo con la biblioteca estandar: no hay nada que instalar.

## Web

```bash
python3 web.py   # genera public/index.html a partir de ideales.md (y copia og.png)
```

`public/index.html` se puede abrir directamente en el navegador. Muestra la afinidad global con cada partido, la afinidad por bloques, los choques en lo que mas pesa y el detalle pregunta a pregunta con la base y la fuente de cada codigo. Tiene la opcion de ignorar los codigos poco seguros (`~`).

### Desplegar

- **GitHub Pages:** subir el repo a GitHub y activar *Settings → Pages → Source: GitHub Actions*. El flujo [.github/workflows/web.yml](.github/workflows/web.yml) pasa las pruebas, genera la pagina y la publica en cada push a `main`. Es gratis con el repo publico; con un repo privado, GitHub Pages necesita un plan de pago.
- **Netlify o Cloudflare Pages:** comando de build `python3 web.py` y carpeta de publicacion `public`.
- **Cualquier hosting estatico:** generar la pagina y subir la carpeta `public`.

Si se publica en otra direccion, cambiar `og:url` y `og:image` en `web.html`: son las etiquetas de la tarjeta (titulo, descripcion e imagen) que muestran X, WhatsApp o Telegram al compartir el enlace.

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
4. Los partidos con cobertura por debajo del 60% (parte del peso de tus respuestas en la que tienen posicion documentada) se listan aparte: su porcentaje no es comparable. Las diferencias de menos de 3 puntos se presentan como empate.
5. Lo que no mide el calculo (corrupcion, pactos, lineas rojas, voto util en tu provincia) lo valora cada uno.

### Contra el sesgo

- **Redaccion equilibrada.** Las afirmaciones estan escritas en los dos sentidos para que contestar "de acuerdo" a todo no incline el resultado: en 50 estar de acuerdo coincide mas con PSOE, Sumar y Podemos, en 46 con PP y Vox y 14 no separan esos bloques. En los dilemas, A y B tambien se reparten. `test_la_redaccion_esta_equilibrada` falla si se descompensa.
- **Todo verificable.** La web muestra la base y la fuente de cada codigo, y junto a cada pregunta un enlace para proponer una correccion por X (a @flamyonn), igual que las sugerencias.
- **Sin inventar.** Si no hay posicion clara, `?`; si hay poca evidencia, `~`, y la web permite repetir el calculo sin esos codigos.

## Actualizar las posiciones de los partidos

Editar la tabla de la seccion 9 de `ideales.md` y despues:

```bash
python3 -m unittest && python3 web.py
```

Con GitHub Pages basta con hacer push. Las copias locales llevan su propio anexo: para recalcular con los codigos nuevos, copiar la seccion 9 a tu copia y volver a pasar `afinidad.py --write`. Ojo con las copias hechas antes de octubre de 2026: desde entonces 12 afirmaciones dicen lo contrario que antes (DL1, DL3, V1, S3, S4, T6, T7, X3, X9, X11, M1 y K2) y G5 es una pregunta nueva, asi que su anexo no es intercambiable con el actual.

Si una pregunta cambia de sentido o de contenido, las respuestas que la gente tiene guardadas en el navegador quedan desfasadas: hay que migrarlas en `web.html` (ver `INVERTIDAS_V2` y `CAMBIADAS_V2`).

## Archivos

| Archivo | Que hace |
| --- | --- |
| `ideales.md` | Plantilla publica: cuestionario en blanco y anexo de partidos con fuentes. Fuente unica de la web |
| `web.py` | Genera `public/index.html` con las preguntas y los codigos de `ideales.md` |
| `web.html` | La pagina de la web: preguntas, calculo y resultados, todo en el navegador |
| `og.html`, `og.png` | Imagen de la tarjeta al compartir el enlace y su fuente (el comando para regenerarla esta dentro) |
| `cuestionario.py` | Servidor local que muestra las preguntas con botones y escribe en tu .md |
| `afinidad.py` | Calcula la afinidad global, por bloque y los choques en lo que mas pesa |
| `test_votar.py` | Pruebas: plantilla en blanco, redaccion equilibrada, lectura y escritura del .md, y que la web calcula igual que `afinidad.py` |
| `.github/` | Publicacion en GitHub Pages |

## Privacidad

Las respuestas son opiniones politicas.

- `ideales.md` no lleva respuestas de nadie: una prueba falla si alguien guarda respuestas, resumen o resultados en la plantilla.
- La web no carga recursos externos ni envia datos. El progreso se guarda en el `localStorage` del navegador y se borra con *Borrar mis respuestas*.
- El servidor local solo escucha en `127.0.0.1`.
