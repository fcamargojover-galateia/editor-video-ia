# Objetos que siguen a la persona y objetos que se mueven

Para poner íconos, logos, emojis o imágenes **encima del video** y que se peguen a una mano, floten
alrededor de la cabeza, recorran la pantalla o pasen por detrás de la persona.

Piezas en `src/seguir.tsx`. Datos en `src/puntos.ts`, que genera `scripts/seguir.py`.

## 1. Preparar el seguimiento (una vez por video, después de `cut.py`)
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/seguir.py" "<carpeta>" --revisar 12.5
```
- Tarda aproximadamente lo que dura el video. Imprime **qué porcentaje del tiempo se ve cada punto**
  y la **lista de gestos con su segundo exacto**: léela antes de planificar, es la que manda.
- `--revisar S` guarda `seguimiento.jpg` con los puntos dibujados en ese segundo: **míralo siempre**
  antes de colgar algo de una mano.
- `--paso 0.07` si las manos se mueven muy rápido (más preciso, archivo más grande).
- Si un punto se ve menos del ~40 % del tiempo, no cuelgues nada de él: usa `cara`, `sobreCabeza`,
  `hombroDer` o un recorrido con `<Mover>`.

**Izquierda y derecha son las de la PANTALLA** (lo que ves), no las de la persona.

| Puntos disponibles | |
|---|---|
| `manoIzq` `manoDer` | centro de la palma (el más usado) |
| `indiceIzq` `indiceDer` | punta del índice (señalar) |
| `pulgarIzq` `pulgarDer` | punta del pulgar |
| `pinzaIzq` `pinzaDer` | entre pulgar e índice: para "sostener" algo pequeño |
| `munecaIzq` `munecaDer` | muñeca |
| `cara` `menton` `sobreCabeza` | nariz · debajo del mentón · por encima del pelo |
| `hombroIzq` `hombroDer` `centroManos` | |

Gestos detectados: `abierta` · `puno` · `senala` · `pinza` · `pulgar`.

## 2. `Seguir`: pegar algo a un punto
```tsx
<Seguir punto="manoDer" from={12.4} to={17.2} offset={[0, -120]} inercia={0.3}>
  <Burbuja size={160}>🚀</Burbuja>
</Seguir>
```
| Prop | Para qué |
|---|---|
| `offset` | px respecto al punto. `[0,-120]` = flotando por encima de la mano |
| `inercia` | 0 pegado · **0.25 natural** · 0.6 muy flotante (llega después que la mano) |
| `flotar` | vaivén suave en px (default 8). 0 = quieto |
| `escala` | tamaño |
| `giroPorVelocidad` | se inclina hacia donde se mueve la mano |
| `aparece` | `pop` (default) · `fade` · `destello` · `ninguna` |
| `ocultarSinPunto` | true (default): si la mano sale de cuadro, se desvanece |

Dentro puede ir cualquier cosa: `<Burbuja>🔥</Burbuja>`, `<Logo file="logos/openai.svg" height={120} />`,
`<Sparkle />`, un `<Img>` tuyo o un texto.

**Disparar con un gesto**: lee los segundos que imprimió `seguir.py` y úsalos como `from`. Para que sea
automático: `const t = gestoEn("abierta", 0, "der")` (nº de aparición y mano opcionales).
Acompaña el momento con `<Chispas at={t} />` y un `pop` o `brillo` en los SFX.

## 3. `Mover`: recorrido libre
```tsx
<Mover
  pasos={[
    { at: 20.0, punto: "manoDer", escala: 0.2, opacidad: 0 },   // sale de la mano
    { at: 20.5, punto: "manoDer", escala: 1 },
    { at: 22.0, x: 78, y: 28, curva: "suave" },                  // vuela a la esquina
    { at: 26.0, x: 78, y: 28 },                                   // se queda
    { at: 26.6, x: 110, y: 28, curva: "seco", opacidad: 0 },      // se va de cuadro
  ]}
  estela={3}
>
  <Logo file="logos/claude.svg" height={130} />
</Mover>
```
- `x`/`y` en **% del cuadro** (0–100). O `punto: "manoDer"` para salir de / aterrizar en una mano.
- `curva`: `suave` (default) · `lineal` · `rebote` · `elastico` · `seco`.
- `curvo` (default true): hace un arco en vez de una línea recta. Mucho más natural.
- `estela`: 2–4 copias desvanecidas detrás, para movimientos rápidos.
- `escala`, `giro`, `opacidad` se interpolan entre pasos.

`<Orbita punto="cara" from={8} to={14} radio={300} vueltas={1}>` da vueltas alrededor de un punto
(se atenúa cuando pasa por detrás).

## 4. Profundidad: que el objeto pase POR DETRÁS de la persona
```
"$SKILL/.venv/bin/python" "$SKILL/scripts/fondo.py" "<carpeta>" --modo matte
```
Genera `public/persona.webm` (tú recortada, con transparencia). Después, en `video.tsx`:
```tsx
<Camera keys={KEYS} />
<Mover pasos={…}>…</Mover>   {/* queda DETRÁS */}
<Persona />                   {/* tú, recortada, por encima */}
```
Todo lo que vaya **antes** de `<Persona />` queda detrás de ti; lo que vaya después, delante.
Es el truco que hace que un objeto se vea "en la escena" y no pegado encima.
Tarda ~2–3× la duración del video. Si vuelves a cortar, hay que repetirlo.

## 5. Reglas para que se vea bien (y no ridículo)
- **Máximo 1 objeto siguiendo a la vez**, y 2–5 s cada uno. Más es ruido.
- **Solo cuando tiene sentido**: la persona nombra la herramienta, muestra algo con la mano, hace una
  cuenta con los dedos. Un ícono flotando porque sí distrae del mensaje.
- **No tapes la cara**: usa `offset` para dejarlo al lado o por encima de la mano, nunca sobre los ojos.
- **Revisa con fotogramas** (`stills.sh`) en el medio del tramo: es lo único que confirma que el objeto
  está donde crees.
- Si la mano se mueve rápido, sube `inercia` (0.35–0.5) y añade `estela`: disimula el temblor del detector.
- En **reels verticales** funciona muy bien con la cámara en `CAM_FULL`; con `CAM_BOTTOM` el espacio es
  poco y conviene `sobreCabeza` u `hombroDer`.

## 6. Límites honestos (decírselos a la persona)
- Si la mano sale de cuadro, queda tapada o se mueve muy borrosa, el seguimiento se pierde: el objeto
  se desvanece (o se queda quieto con `ocultarSinPunto={false}`).
- Con las manos muy juntas, izquierda y derecha pueden intercambiarse un instante.
- El detector trabaja sobre el video **ya cortado**: si vuelves a cortar, hay que correr `seguir.py` otra vez.
- Esto **no genera** imágenes nuevas: usa logos oficiales, emojis, formas de la skill o archivos tuyos.
  Generar imágenes/video con IA está preparado pero sin activar: ver `scripts/generar.py`.
