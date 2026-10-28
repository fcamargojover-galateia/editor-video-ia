# Efectos PRO: variedad, color, fondo y acabado

Todo lo de este archivo vive en `src/fx.tsx` (mismo archivo en `template/` y `template-reel/`), se configura
en `src/theme.ts` → `ESTILO` y se complementa con los scripts `mejorar.py`, `fondo.py`, `ritmo.py`,
`extras.py` y `qc.py`. **Objetivo: que dos videos seguidos no se vean iguales y que el acabado
(color, sonido, fondo) esté al nivel de un editor profesional.**

## 1. Regla de oro de la variedad
- **Nunca el mismo recurso tres veces seguidas**: rotar entradas de tarjetas, transiciones, estilos
  de frase destacada (`Quote` ↔ `TextoCinetico` con distintos `estilo`) y efectos de sonido.
- **Elegir un "lenguaje" por video y respetarlo**: 2–3 transiciones, 4–6 entradas y 1 estilo de
  subtítulos. Variedad no es caos: dentro de un video, coherencia; entre videos, cambiar el preset.
- **Intensidad según el contenido**: sobrio (educativo, corporativo) · normal (YouTube) · intenso
  (reels, entretenimiento). Ver presets abajo.
- Los efectos llamativos (glitch, flash, sacudida) son condimento: máx. 1 cada ~20 s en videos largos.

## 2. ESTILO (theme.ts)
| Campo | Opciones | Nota |
|---|---|---|
| `subtitulos` | `caja` · `contorno` · `pop` · `karaoke` · `marcador` · `minimal` · `neon` | `pop` = palabra por palabra en mayúsculas (reels). `marcador` = palabra clave con resaltador. `minimal` = corporativo |
| `mayusculas` | true / false | `pop` siempre va en mayúsculas |
| `animaciones` | `subir` `bajar` `izquierda` `derecha` `escala` `desenfoque` `revelar` `giro` `caer` `elastico` | Pool para tarjetas sin `anim`. Una tarjeta concreta: `<Card anim="revelar">` |
| `transiciones` | `latigo` `zoom` `flash` `barrido` `luz` `glitch` `sacudida` `desenfoque` | Pool para las transiciones `"auto"` (nunca repite la anterior) |
| `fondo` | `aurora` `grilla` `degradado` `liso` `particulas` `ondas` | Lo que se ve detrás de la cámara en PIP/SPLIT/END |
| `look` | `{ vineta, grano, barras }` | Viñeta y grano 0–1. `barras: true` = formato cine 2.39:1 (solo horizontal) |
| `sonido` | número | Volumen general de efectos |

### Presets sugeridos (copiar en ESTILO y en C)
| Preset | subtitulos | animaciones | transiciones | fondo | look | Para |
|---|---|---|---|---|---|---|
| **Tech** (default) | caja | subir, izquierda, escala, desenfoque, revelar, giro | latigo, zoom, flash, barrido, luz | aurora | 0.3 / 0.18 | IA, software |
| **Energético** | pop | caer, elastico, escala, izquierda, derecha | latigo, sacudida, flash, glitch | particulas | 0.35 / 0.25 | reels, entretenimiento |
| **Elegante** | minimal | desenfoque, revelar, subir | desenfoque, luz, zoom | degradado | 0.4 / 0.3 · barras | marca personal, lujo, coaching |
| **Educativo** | marcador | subir, revelar, escala | zoom, barrido | grilla | 0.2 / 0.1 | cursos, tutoriales |
| **Noche/neón** | neon | escala, desenfoque, giro | glitch, flash, zoom | ondas | 0.45 / 0.3 | gaming, música, tecnología |
| **Corporativo** | minimal | subir, izquierda | barrido, desenfoque | liso | 0.15 / 0 | empresas, B2B |

Si la persona copia el estilo de un creador (`copiar-estilo.md`), traducirlo a estos campos.

## 3. Piezas nuevas (fx.tsx)
- `ConTransiciones list={TRANS}` — envuelve **Background + Camera + tarjetas** (no los subtítulos ni la marca).
  `TRANS = autoTransiciones([tiempos de cambio de encuadre])` o a mano `{ at, tipo: "glitch", dur?, color? }`.
  Sumar el sonido: `<Sounds list={[...SFX, ...sfxDeTransiciones(TRANS)]} />` y **no** poner whoosh a mano en esos tiempos.
  Las transiciones van en cambios de caja (PIP/SPLIT/END); un punch-in sigue siendo corte seco.
- `TextoCinetico from to lines mark estilo` — frase grande: `impacto` (golpe), `ola`, `maquina` (letra
  por letra; con SFX `tecleo`), `apilado` (póster en mayúsculas). Alternar con `Quote`. Ocultar subtítulos en ese tramo.
- `Circulo at to x y w h` — círculo dibujado a mano alrededor de algo (dato en una captura, un botón).
- `Flecha at to x y angulo largo` — flecha curva que se dibuja apuntando a (x, y).
- `EmojiPop at to emoji x y size` — emoji que salta y flota (máx. 1 cada ~30 s; con `pop`).
- `BarraProgreso` — barra fina de progreso arriba (videos largos: ayuda a la retención).
- `Look` — viñeta, grano y barras. Va después de las capas visuales y antes de los subtítulos.
- `alBeat(t)` — lleva un tiempo al golpe de la música más cercano (requiere `ritmo.py`). Úsalo en
  transiciones, punch-ins y cortes de b-roll; **nunca** en algo atado a una palabra (eso manda la voz).
- `Card anim="..."` — entrada concreta para una tarjeta.
- Miniatura: composición `Miniatura` (ver `extras.py --miniatura`).

- **Objetos sobre el video** (siguen la mano, vuelan, orbitan, pasan por detrás): `seguimiento.md`.

## 4. Sonido sin repetición
- Tipos: `whoosh` `swoosh` `pop` `ding` `click` `boom` `impacto` `riser` `glitch` `shutter` `tecleo` `brillo`.
- `Sounds` rota las variantes de cada tipo (`whoosh`, `whoosh_2`, `whoosh_3`…) y varía tono (±6 %) y
  volumen (±12 %): nunca suenan dos iguales seguidos.
- `riser` = 1,4 s de subida: ponerlo 1,3 s **antes** de una revelación importante (un número, un resultado).
- `shutter` = captura de pantalla / foto. `tecleo` con `PromptCard` o `TextoCinetico estilo="maquina"`.
- Para crear más variantes: `python3 scripts/sfx_gen.py --seed N` (o reemplazar WAV manteniendo nombres).

## 5. Imagen: color y limpieza (`mejorar.py`, ANTES de cut.py)
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/mejorar.py" "<carpeta>" --look natural --intensidad 0.7 [--denoise 1] [--nitidez 1] [--estabilizar] [--voz pro]
```
- **Siempre** corre la corrección automática (exposición, contraste, balance de blancos, saturación),
  calibrada para caras: no enfría la piel.
- Looks: `natural` (default seguro) · `cinematico` (teal & orange) · `calido` · `frio` · `moody`
  (negros levantados, desaturado) · `vibrante` · `pastel` · `bn`. Protegen la piel (`--no-piel` para desactivar).
- `--denoise 1` si la grabación tiene grano (poca luz, celular). `--estabilizar` si fue grabado a mano.
- **Mira `antes-despues.jpg`** y muéstraselo a la persona si el look es fuerte. Se aplica solo en
  `cut.py` y `reel_prep.py`, también al re-cortar. Quitar todo: `--reset`.

## 6. Voz de estudio (`mejorar.py --voz`)
`limpia` (zumbido y ruido de fondo) · **`pro`** (default: limpia + EQ de presencia + de-esser + compresor) ·
`radio` (locutor, más cuerpo) · `off`. render.sh después normaliza a −14 LUFS como siempre.
Si la voz suena "metálica" o con artefactos → `--voz limpia` o `off` (pasa con ruidos muy fuertes).

## 7. Fondo (`fondo.py`, DESPUÉS de cut.py / reel_prep.py)
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/fondo.py" "<carpeta>" --modo desenfoque|estudio|color|degradado|imagen|video [--valor ...] [--preview 12]
```
- Primero `--preview <segundo>` → `fondo-preview.jpg` para revisar bordes (pelo, manos, lentes).
- `desenfoque` = efecto retrato, el más natural y seguro. `estudio` = fondo oscuro con luz de los
  colores de la marca. `imagen`/`video` = fondos propios (pedir el archivo; nada con derechos de terceros).
- Tarda ~2–3× la duración del video. Si se re-corta el video, cut.py avisa: volver a correr fondo.py.
- `--modo original` deshace.

## 8. Música al ritmo (`ritmo.py`)
`"$SKILL/.venv/bin/python" "$SKILL/scripts/ritmo.py" musica.wav "<carpeta>"` → `beats.ts`. Después
`alBeat()` en transiciones/punch-ins. En reels con música marcada, cortar la b-roll en los golpes se siente pro.

## 9. Muletillas
`prep.py --muletillas` (Whisper escribe los "eh", "mmm") + `cut.py --muletillas` / `reel_prep.py --muletillas`
los quita. "Este" y "o sea" no se quitan solos (a veces tienen sentido): usar `--drop`.

## 10. Entrega profesional
- `extras.py "<carpeta>"` → `subtitulos.srt` (subirlo a YouTube: mejora alcance y accesibilidad),
  `capitulos.txt` (desde las `SectionCard`) y los 4 mejores fotogramas para miniatura.
- `extras.py "<carpeta>" --miniatura "Título corto" --destacar palabra --chip "NUEVO" --foto 2` →
  `miniatura.jpg` (1280x720; en reels, portada 1080x1920). Títulos de 3–6 palabras.
- `qc.py <final.mp4> [--plataforma youtube|instagram|tiktok]` → control de calidad (volumen, picos,
  silencios, negros, congelados, formato). Correrlo SIEMPRE antes de entregar y contar el resultado.
