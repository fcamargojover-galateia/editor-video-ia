# Preset "Creador pro" (reels verticales, estilo de creador de contenido)

Origen: el usuario pasó un reel de referencia y pidió replicarlo; la prueba quedó aprobada (2026-10-16).
Código completo y funcionando: `references/reels/ejemplo-creador-pro.tsx` (copiar a `reels/<n>/remotion/src/video.tsx`
y cambiar textos, tiempos y el arreglo `BIGS`). Fuentes: `@remotion/google-fonts/Anton` e `Inter`.

## Receta
- **Cámara a pantalla completa** (`CAM_FULL`) todo el reel; punch-ins en seco (zoom 1.16–1.26 alternando con 1.0) en cada cambio de idea.
- **Color**: filtro `saturate(1.3) contrast(1.07) brightness(1.16)` + velo cálido (`soft-light`, rojo/naranja). Si la grabación es oscura, mejor
  `mejorar.py` o un fondo más claro (`fondo.py`).
- **Gancho** arriba-izquierda, 2–3 líneas en Anton ~176 px, inclinado −8°, degradado dorado con contorno negro; entra de a una línea y sale a los ~3 s.
- **Subtítulos normales**: grupos de hasta 3 palabras, Inter 800 ~70 px, blancos, sin caja, sombra suave, y=1170 (a la altura del pecho).
- **Frases clave (`BIGS`)**: 1–2 líneas en dorado Anton ~104–124 px + **ícono 3D** a la izquierda (rebota al entrar, flota). Los íconos salen de `assets/iconos3d/` (Fluent Emoji 3D, MIT);
  `scripts/iconos.py sugerir <carpeta>` propone ícono por palabra y los copia a `remotion/public/iconos/`.
  Reemplazan al subtítulo normal mientras están. Una cada 3–8 s, sobre sustantivos que cargan el sentido.
- **Tarjetas blancas inclinadas** (`FloatCard`, ±8°) arriba a la derecha con un gráfico o ilustración; 2–3 s cada una.
- **Etiqueta de vidrio** abajo (y≈1400) con un dato; **escena a pantalla completa** de fondo claro con ilustración animada para el remate.
- **Blanco y negro** por tramos de ~2 s en frases de énfasis ("es un ejemplo tonto", "no es fácil de saber").
- **Transiciones** en cada cambio de idea, rotando: flash, zoom con desenfoque, látigo, sacudida, desenfoque. Sonido: impacto, pop en cada frase clave, riser antes de la escena final.
- Sin CTA si el usuario no definió palabra (`CTA_SECONDS = 0`).

## Animaciones que EXPLICAN (lo que más valora el usuario)
Una animación que hace entender un concepto que la gente no sabe o no recuerda vale más que un efecto bonito.
Ejemplo completo y probado: `references/reels/ejemplo-flujo-pantalla-completa.tsx` (reel "Método 3"). Patrones:
- **Comparar opciones** (`TresMetodos`): 3 cajas con una mini-curva cada una; las tres están desde el principio en gris
  y se "encienden" cuando la voz las nombra; ✗ en las descartadas y ✓ + marco dorado en la que importa.
- **Curva que se dibuja** (`CurvaPico`): `<path pathLength={1} strokeDasharray={1} strokeDashoffset={1-p}/>` se traza sola;
  línea plana gris + tramo naranja que se dispara, con el ícono 3D del motivo (tsunami, pandemia) en el quiebre.
- **Línea de tiempo** (`LineaAnios`): hitos que aparecen uno a uno con el ícono del tema y la distancia rotulada ("4 años");
  cierra con una frase que saca la conclusión ("no es del calendario: es extraordinario").
- **Objeto dibujado** (`Spinner` en SVG): cuando nombra algo que el espectador quizá no recuerda, mostrarlo girando/animado.
**Van siempre en pantalla dividida** (`CAM_BOTTOM` + `Panel` arriba, y ≤ 845): la animación tiene su espacio y la cara
queda entera abajo. Las frases grandes con ícono (`BIGS`) van solo en cámara completa, a la altura del pecho (y≈1052).
Ritmo probado: 4 animaciones explicativas en 57 s, de 3,5–5,5 s cada una.

### Escena de FLUJO a pantalla completa (`Flujo`)
La persona **sale del plano** y el concepto se explica solo, con etapas encadenadas por flechas que se dibujan.
Es lo que hay que usar cuando el usuario pide "una animación donde se explique el proceso / las etapas / el camino".
```tsx
<Flujo from={11} to={17.4} titulo={["QUÉ PASA CUANDO","PASA ALGO AFUERA"]}
  etapas={[{ at: 11.3, icono: "water_wave", titulo: "Pasa algo de golpe", sub: "una pandemia" }, ...]}
  remate={{ at: 16.3, icono: "high_voltage", texto: "Eso es un factor extraordinario" }} />
```
- `orientacion="vertical"` (default): 3–4 tarjetas apiladas (820 px) con flecha curva entre cada una. Cabe de y 470 a 1370, remate en 1420.
- `orientacion="horizontal"`: línea de tiempo de 3 nodos (240 px) con flecha y `etiqueta` encima ("4 años"). Nodos en y 700, remate en 1150.
  Máximo 3 nodos: 3×240 + 2×120 = 960 px (si no, se salen de los 1080). Título de 2 líneas para que no quede aire arriba.
- Cada etapa entra con rebote y su `pop`; la flecha se dibuja (`pathLength`) y la punta aparece al final. ~1,3 s por etapa.
- Declarar el tramo en `ESCENAS` (oculta los subtítulos, que la escena trae su propio texto) y en `caracheck.py --escenas`.
- **Importante**: las etapas tienen que decir lo que la persona DICE, no inventar pasos que no menciona.

## Cara: qué evitar y qué sí usar
**Evitar**: carteles, tarjetas, títulos o subtítulos ENCIMA de la cara mientras habla (eso es lo que molesta).
**Recomendado**: *cambio de enfoque* — una escena a pantalla completa (animación, gráfico, ilustración) que reemplaza
la toma para explicar un concepto o cerrar la idea. Mantiene el ritmo y la atención; usarlo cuando el contenido lo pida,
no solo al final. También la pantalla dividida (tarjeta arriba, cara entera abajo) para toda animación explicativa.
Revisar con `caracheck.py` y declarar las escenas a pantalla completa con `--escenas 54.2-57.9` para que no las marque:
los avisos que queden son overlays reales sobre la cara.

## Límites conocidos
- Íconos: 191 íconos 3D de Fluent (objetos y conceptos; no hay marcas, para eso `logo.py`). Si falta uno, pedir permiso y bajarlo de github.com/microsoft/fluentui-emoji.
- Funciona mejor con grabación vertical a cámara y buena luz; con fuente horizontal se recorta y se ve más blanda.
- Cursor con clic y capturas reales: pedirlas al usuario (no incluidas).
