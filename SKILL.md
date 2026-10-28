---
name: editor-video-ia
description: Edita videos grabados a cámara (talking head) y saca reels verticales con acabado de editor profesional — corrección de color y looks de cine, cambio o desenfoque de fondo con IA, voz de estudio, transiciones variadas, íconos y logos que siguen las manos o recorren la pantalla, cortes sin pausas ni muletillas, subtítulos con 7 estilos con palabras clave resaltadas, tarjetas animadas (listas ✓/✗, números que suben, flujos de pasos), zooms, cámara que pasa a recuadro o pantalla dividida, logos oficiales de las herramientas que se nombran, tomas de apoyo, efectos de sonido y música con ducking — renderizado a MP4 con Remotion, más miniatura, subtítulos .srt y control de calidad. Antes de editar SIEMPRE entrevista a la persona: qué tipo de video es (video largo horizontal o reels verticales), si quiere copiar el estilo de algún creador (link o capturas) y los datos de su marca. Úsala cuando alguien pase un video (.mp4/.mov) y pida "edita este video", "hazme la edición", "ponle subtítulos y animaciones", "quítale las pausas", "que se vea profesional", "sácame reels / shorts / clips de este video", "quiero que se vea como los videos de [creador]", "corrige el color", "cámbiale / desenfoca el fondo", "mejora el audio", "hazme la miniatura", "que el logo salga de mi mano", "pon un ícono que me siga", "que vuele por la pantalla", aunque no mencione la skill.
---

# Editor de video con IA (videos largos y reels)

Convierte una grabación a cámara en un video editado con estilo de creador profesional. La parte
mecánica (transcribir, cortar, recortar, renderizar) está en `scripts/`; lo que requiere criterio es
**la entrevista inicial** y **decidir las escenas** leyendo la transcripción.

Rutas: `SKILL` = carpeta de esta skill (donde está este archivo). Python de la skill: `$SKILL/.venv/bin/python`.
Habla siempre en español neutro, con "tú", y explica en simple: la persona probablemente no es editora ni programadora.

---

## Paso 0 — Dependencias (la primera vez)

```
bash "$SKILL/scripts/setup.sh"
```
Si falta ffmpeg, Node o Python, el script dice cómo instalarlo según el sistema. En Windows, recomendar WSL
(Ubuntu) o Git Bash con ffmpeg/Node/Python instalados. La primera transcripción descarga el modelo de
Whisper (~1,5 GB): avisar que tarda.

---

## Paso 1 — Entrevista (OBLIGATORIA antes de tocar el video)

Hacer las preguntas en **un solo mensaje** (si hay una herramienta de preguntas con opciones, usarla).
No preguntar lo que la persona ya dijo. Preguntas:

1. **¿Qué tipo de video es?**
   - **Video largo** (horizontal 16:9, YouTube / curso / webinar)
   - **Reels / Shorts** (vertical 9:16) — ¿a partir de un video largo o de una grabación vertical corta?
     ¿Cuántos reels quiere? (sugerir 3–6 de 30–60 s)
   - **Ambos** (primero el largo, después los reels del mismo material)
2. **¿Quieres copiar el estilo de alguien?** (opcional) Pedir **un link a un video** del creador o
   **3–5 capturas** de sus videos. Si dice que no, usar el estilo por defecto de la skill
   (tarjetas oscuras, acento lima y violeta). → ver `references/copiar-estilo.md`.
3. **Tu marca**: colores (o "los de mi logo"), tu @usuario para la marca de agua, y tu logo si quieres.
4. **¿Ya hiciste los cortes?** Si la persona ya cortó errores y pausas, NO volver a cortar
   (`cut.py --gap 99`). Si no, la skill quita pausas y tomas repetidas.
5. **Música**: archivo propio (mp3/wav libre de derechos), "sin música", o "elige tú" (ver Paso 6).
6. **Acabado visual** (ofrecer opciones con una recomendación; "elige tú" es válido):
   - **Color**: natural (recomendado) · cinematográfico · cálido · frío · moody · vibrante · pastel · blanco y negro.
   - **Fondo**: el original (recomendado si se ve bien) · desenfocado tipo retrato · fondo de estudio con
     los colores de la marca · una imagen/video propio.
   - **Estilo "Creador pro"** (reels): dorado + íconos azules brillantes + tarjetas flotantes + flashes → `references/preset-creador-pro.md`.
   - **Energía de la edición**: sobria · normal · intensa → elige el preset de `references/efectos-pro.md`
     (Tech, Energético, Elegante, Educativo, Neón, Corporativo) y el estilo de subtítulos.
7. **Solo reels — CTA final**: palabra para comentar (ej. "Comenta GUIA y te envío…") y qué se envía.

Con las respuestas:
- Escribir los colores y la marca en `remotion/src/theme.ts` de cada proyecto (`C` y `MARCA`).
  `lime` = acento principal, `violet` = acento secundario, `bg` = fondo.
- Escribir el preset elegido en `theme.ts` → `ESTILO` (subtítulos, entradas, transiciones, fondo, look).
  **Si es el segundo video o más de la misma persona, cambiar algo del preset** (otras transiciones,
  otro estilo de frase destacada) para que su canal no se vea siempre igual, salvo que pida lo contrario.
- Si hay estilo de referencia, aplicarlo según `references/copiar-estilo.md` **antes** de planificar escenas,
  y mostrarle a la persona un resumen de lo que vas a copiar ("cortes cada ~2 s, subtítulos amarillos en
  mayúsculas al centro, zooms en cada remate…") para que confirme.

---

## Video largo (16:9)

### 2. Preparar y transcribir
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/prep.py" "<ruta del video>"
```
Crea `edicion-<nombre>/` junto al video (proyecto Remotion, `words.json`, `transcript.txt`, `contact.jpg`,
`crop.txt`). Tarda ~1 min por minuto de video. Para videos largos, correrlo en segundo plano.
**Mira `contact.jpg`**: si la grabación viene dentro de un marco (apps tipo Screen Studio), `prep.py` lo
detecta en `crop.txt`. Si se equivocó, corregir en el paso 3 con `--crop none` o `--crop W:H:X:Y`.

Si la persona dice muchas muletillas ("eh", "mmm"), correr `prep.py` con `--muletillas`.

### 2b. Color, limpieza e imagen (antes de cortar)
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/mejorar.py" "<carpeta edicion-...>" --look <look> [--intensidad 0.7] [--denoise 1] [--estabilizar] [--voz pro]
```
Corrige exposición, contraste y balance de blancos solo; aplica el look (protegiendo la piel), limpia
ruido y deja la voz de estudio. **Mira `antes-despues.jpg`**. Se aplica solo en `cut.py`/`reel_prep.py`.
Detalle de cada opción: `references/efectos-pro.md` §5–6.

### 3. Cortes
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/cut.py" "<carpeta edicion-...>" [--gap 0.28] [--drop "12.3-14.1,..."] [--muletillas]
```
- Detecta la cara solo (`face.ts`): los zooms se centran en ella y los recuadros la siguen.
- `--sin-cortes` conserva el video entero. Úsalo si hay poca voz (demostraciones, gestos, música):
  cut.py solo guarda lo que se HABLA y avisa si se quedó con menos de la mitad del video.
- `--gap 0.28` = ritmo ágil tipo YouTube · `0.4` = más respirado · **`99` = no cortar nada** (si la persona ya editó).
- Tomas repetidas o errores: leer `transcript.txt`, buscar frases dichas dos veces / frases cortadas, y
  eliminarlas con `--drop` (tiempos del ORIGINAL; afinar con `words.json`). Quedarse con la última toma completa.
- Imprime la transcripción con **los tiempos nuevos**: son los únicos que valen para las escenas.
- Corregir nombres mal transcritos (marcas, el nombre de la persona) en `remotion/src/words.ts`
  y, si se repiten, en `scripts/fixes.py`.

### 3b. Seguimiento de manos y cuerpo (opcional, solo si va a haber objetos pegados a la persona)
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/seguir.py" "<carpeta edicion-...>" --revisar <segundo>
```
Genera `puntos.ts` (manos, dedos, cara, hombros) y la lista de **gestos con su segundo**. Mirar
`seguimiento.jpg` y los porcentajes de visibilidad antes de colgar nada de una mano.
Uso de `<Seguir>`, `<Mover>`, `<Orbita>` y `<Persona>`: `references/seguimiento.md`.

### 3c. Fondo (opcional, después de cortar)
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/fondo.py" "<carpeta edicion-...>" --modo desenfoque|estudio|color|degradado|imagen|video [--valor ...] --preview 10
```
Primero con `--preview` (revisar pelo, manos, lentes en `fondo-preview.jpg`), después sin él. Si se
vuelve a cortar, repetir este paso (cut.py avisa).

### 4. Planificar escenas (el trabajo de criterio)
Leer `references/estilo.md` (catálogo de piezas y reglas de ritmo) **y `references/efectos-pro.md`**
(transiciones, texto cinético, llamadas de atención, sonido variado). Resumen:
- Bloques de ideas de 4–10 s. Cada bloque = un encuadre + (opcional) una tarjeta.
- Listas → `Row` · números → `Stat` + `Counter` · procesos → `Node` + `Arrow` · antes/después → `ProgressBar`
  · frase-remate → `Quote` con zoom · herramienta nombrada → `ToolBadge` con su **logo oficial**
  (`scripts/logo.py`; si da NOT_FOUND, usar el destello de IA y avisar — nunca dibujar un logo de marca).
- Alternar encuadres (cámara completa, recuadro, pantalla dividida, zoom). Nada más de ~8 s sin cambio visual.
  Los primeros 2 s siempre en cámara completa (el gancho es la cara).
- Sincronizar cada elemento con el segundo exacto en que se dice la palabra (±0,1 s).
- Textos en pantalla cortos: títulos ≤ 5 palabras, filas ≤ 6.
- **Tomas de apoyo (b-roll)**: si la persona comenta algo externo (un lanzamiento, una herramienta, un evento),
  sugerir fragmentos cortos del material oficial o capturas de la web. **Pedir permiso antes de descargar**,
  clips de < 10–15 s siempre comentados y con crédito ("Imágenes: [fuente]"). Ver `references/estilo.md` → b-roll
  y `references/ejemplo-video-noticias.tsx`.
- **Variedad (lo que separa una plantilla de un editor)**: transiciones `"auto"` en los cambios de
  encuadre grandes (`ConTransiciones` + `sfxDeTransiciones`), entradas de tarjeta distintas, alternar
  `Quote` con `TextoCinetico` (estilos distintos), `Circulo`/`Flecha` para señalar datos en capturas,
  `EmojiPop` ocasional, `riser` antes de las revelaciones. Nunca el mismo recurso 3 veces seguidas.
- **Objetos sobre el video**: si la persona muestra algo con la mano, cuenta con los dedos o nombra una
  herramienta mientras gesticula, `<Seguir punto="manoDer">` con un logo/emoji (2–5 s, máx. 1 a la vez);
  para que algo "vuele" por la pantalla, `<Mover>` con puntos clave. Con `fondo.py --modo matte` +
  `<Persona />` el objeto pasa por detrás. Reglas y límites: `references/seguimiento.md`.
- Capas en `Main`: `ConTransiciones` (Background, Camera, Broll, escenas) → objetos `Seguir`/`Mover` →
  `Persona` (si hay profundidad) → `Look` → `Subtitles` →
  `Brand` → `BarraProgreso` (videos largos) → `Sounds`.
- Si hay música con ritmo marcado, `ritmo.py` y `alBeat()` en transiciones y punch-ins.
Escribir todo en `remotion/src/video.tsx` (reemplazando el ejemplo). Solo se edita ese archivo.

### 5. Revisar con fotogramas antes de renderizar
```
bash "$SKILL/scripts/stills.sh" "<carpeta edicion-...>" 1.0 5.5 12.3 ...
```
Un segundo en medio de cada escena (con todos los ítems visibles); leer `remotion/out/hoja.jpg`.
Para ver movimiento, transiciones y tiempos sin esperar el render completo: `bash "$SKILL/scripts/previa.sh" "<carpeta>" <desde_s> <hasta_s>` (baja resolución, ~9 s de render por cada 6 s de video) → `remotion/out/previa.mp4`. Buscar textos
que desbordan, subtítulos tapando la cara o una tarjeta, logos mal elegidos, recortes raros. Iterar con
fotogramas (segundos) y renderizar al final (minutos).

### 6. Música
- Si la persona trae música, usar esa. Si pidió "elige tú": sugerir bibliotecas libres de derechos
  (YouTube Audio Library, Pixabay Music) o un generador de música con IA; estilo recomendado para hablar
  encima: lo-fi / electrónica suave instrumental, ~90–100 BPM, sin voces.
- Si la pista es más corta que el video, encadenarla con crossfade:
  `ffmpeg -i m.wav -i m.wav -i m.wav -filter_complex "[0][1]acrossfade=d=4[a];[a][2]acrossfade=d=4[m]" -map "[m]" musica.wav`

### 7. Render final
```
bash "$SKILL/scripts/render.sh" "<carpeta edicion-...>" "<salida>.mp4" ["<musica.wav>"] [volumen=0.16]
```
Renderiza, normaliza la voz a -14 LUFS (estándar de YouTube/Instagram), mezcla la música con ducking
(baja sola cuando se habla) y fades.

### 8. Control de calidad y entregables
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/qc.py" "<salida>.mp4" --plataforma youtube
"$SKILL/.venv/bin/python" "$SKILL/scripts/extras.py" "<carpeta edicion-...>"
"$SKILL/.venv/bin/python" "$SKILL/scripts/extras.py" "<carpeta edicion-...>" --miniatura "Título corto" --destacar palabra
```
Si `qc.py` marca ⚠️, corregir y volver a renderizar.
Aviso de CARTELES sobre la cara (lo que molesta son tarjetas/subtítulos encima del rostro; un cambio de enfoque a pantalla completa es un recurso buscado, se declara y no se avisa):
`"$SKILL/.venv/bin/python" "$SKILL/scripts/caracheck.py" "<salida>.mp4" "<carpeta>/remotion/public/cam.mp4" --escenas 54.2-57.9` (reels; en largos usar `cut.mp4`). Entregar: MP4, `miniatura.jpg` (mostrar las
opciones de `miniaturas.jpg`), `subtitulos.srt`, `capitulos.txt` y un resumen: duración antes → después,
qué escenas y efectos lleva, look/fondo aplicado, resultado del control de calidad y qué conviene revisar
escuchando (no puedes oír el audio: la mezcla se controla con medidores).

---

## Reels / Shorts (9:16)

Leer `references/reels.md` y seguir ese flujo. Resumen:
1. Transcribir con `prep.py` (si ya se hizo el largo, reutilizar esa carpeta).
2. **Elegir fragmentos** que funcionen solos: gancho en los primeros 2 s, se entienden sin el resto,
   tienen desenlace. **Proponer la lista** (tabla: título, tramos, duración, gancho) y esperar el OK,
   salvo que la persona haya dicho "elige tú".
3. Cortar cada reel: `scripts/reel_prep.py` (genera `cam.mp4` vertical y `camwide.mp4` con la cara completa
   para la pantalla dividida). Aplica solo las mejoras de `mejorar.py`; `--muletillas` las quita. Fondo: `fondo.py "reels/<n>"`.
4. Escenas en `reels/<n>/remotion/src/video.tsx` con `DualCam` (la cara NUNCA se recorta al achicar la cámara),
   `HookTitle` al inicio, tarjetas `CARD_SPLIT`, tomas `BrollTop` y `CommentCTA` al final con la palabra de la entrevista.
5. Escenas de FLUJO a pantalla completa (la persona sale del plano y el concepto se explica con etapas, flechas e íconos): componente `Flujo` en `references/reels/ejemplo-flujo-pantalla-completa.tsx`; cuándo y cómo, en `references/preset-creador-pro.md`.
6. Íconos 3D por palabra (estilo "Creador pro"): `"$SKILL/.venv/bin/python" "$SKILL/scripts/iconos.py" sugerir "reels/<n>"` propone ícono según lo que se dice y copia los PNG a `public/iconos/` (191 íconos Fluent 3D en `assets/iconos3d/`, MIT; ver `references/preset-creador-pro.md`).
7. Subtítulos `pop` o `contorno` suelen funcionar mejor en vertical; transiciones más intensas (preset Energético).
8. Fotogramas → render (`render.sh`) → `qc.py --plataforma instagram`, salida en una carpeta `Reels - <video>/`.
   Portada: `extras.py "reels/<n>" --miniatura "Gancho corto"`.

---

## Ajustes típicos
- "Más / menos rápido" → `--gap` en `cut.py` y reajustar tiempos de `video.tsx`.
- "Subtítulos más grandes / en otro lugar / en mayúsculas" → `Subtitles` / `SubsV` en `lib.tsx` / `reel.tsx` del proyecto.
- "Otros colores / otra tipografía" → `theme.ts` (las fuentes vienen de `@remotion/google-fonts`).
- "Cambia la música" → solo rehacer el paso 7.
- "Otro color / más cine / más natural" → `mejorar.py --look ...` + `cut.py` (y `fondo.py` si había) + render.
- "Cambia / desenfoca el fondo" → `fondo.py` + render. "Quita el cambio de fondo" → `--modo original`.
- "El audio tiene ruido / suena lejos" → `mejorar.py --voz pro` (o `radio`) + `cut.py` + render.
- "Se ve repetitivo / más dinámico" → cambiar preset de `ESTILO`, más transiciones `auto`, `TextoCinetico`,
  `Circulo`/`Flecha`, `riser` antes de los datos clave.
- "Está temblando la cámara" → `mejorar.py --estabilizar`.
- "Que el logo salga de mi mano / me siga un ícono / vuele por la pantalla" → `seguir.py` + `<Seguir>`/`<Mover>`.
- "Que pase por detrás de mí" → `fondo.py --modo matte` + `<Persona />`.
- "Genérame una imagen / un video con IA" → `scripts/generar.py` está preparado pero **sin activar**:
  explicarle que hace falta elegir proveedor y poner una clave (cuesta dinero), y que mientras tanto
  puede usar sus propias imágenes, los fondos de la skill o bancos gratuitos.
- Si la persona re-corta el video después de editarlo, no rehacer escenas: transcribir la versión nueva y
  `python3 "$SKILL/scripts/retime.py" <words.ts viejo> <words.ts nuevo> <video.tsx viejo> <video.tsx nuevo>`.

## Licencias (decírselo a la persona si su empresa es grande)
Remotion es gratis para personas y empresas de hasta 3 empleados; empresas más grandes necesitan licencia
(remotion.dev/license). Whisper, ffmpeg y OpenCV son de código abierto.

## Nota (2026-10-23): edición dopamínica sin Remotion
En el proyecto avatares-ia hay un montador por código para reels "dopamínicos" a partir de clips crudos:
`herramientas/shorts-render/efectos_reel.py` (PIL + numpy + ffmpeg, sin drawtext). Catálogo de efectos (punch,
zoom con keyframes, whip-pan, speed ramp, glitch/RGB, flash, shake, color grade, espejado, rack focus, slide/spin/
zoom-through, letterbox, viñeta) y lecciones en `.claude/agents/editor-video.md`, sección «Técnicas de edición
dopamínica (2026-10-23)». Si la persona pide "edición estilo reel de coches/lujo", se puede usar ese módulo.
