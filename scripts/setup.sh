#!/bin/bash
# Instala las dependencias de la skill (una sola vez; es seguro volver a correrlo).
# Primera vez: 5–15 minutos (descarga Remotion, el navegador de render y el modelo de transcripción).
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
falta=0
command -v ffmpeg >/dev/null || { echo "❌ Falta ffmpeg.  Mac: brew install ffmpeg  ·  Windows: winget install ffmpeg  ·  Linux: sudo apt install ffmpeg"; falta=1; }
command -v node >/dev/null || { echo "❌ Falta Node.js 18 o superior: https://nodejs.org (versión LTS)"; falta=1; }
command -v python3 >/dev/null || { echo "❌ Falta Python 3.9 o superior: https://www.python.org/downloads/"; falta=1; }
[ $falta = 1 ] && exit 1

# Python: las librerías de IA (Whisper, onnxruntime) tardan en sacar versiones para el Python más nuevo,
# así que se prefiere 3.12 / 3.11 / 3.13 / 3.10 si están instalados.
PY=""
for v in 3.12 3.11 3.13 3.10; do
  if command -v "python$v" >/dev/null; then PY="python$v"; break; fi
done
[ -z "$PY" ] && PY=python3
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || { echo "❌ Necesitas Python 3.9 o superior"; exit 1; }
if [ ! -x "$SKILL/.venv/bin/python" ]; then
  echo "→ Creando entorno de Python ($("$PY" -V))…"
  "$PY" -m venv "$SKILL/.venv"
fi
"$SKILL/.venv/bin/python" -c "import faster_whisper, numpy, cv2; assert hasattr(cv2, \"CascadeClassifier\")" 2>/dev/null || {
  echo "→ Instalando transcripción (faster-whisper) y detección de cara (OpenCV)…"
  "$SKILL/.venv/bin/pip" install -q --upgrade pip
  "$SKILL/.venv/bin/pip" install -q faster-whisper numpy "opencv-python-headless<5" || {
    echo "❌ No se pudo instalar faster-whisper con $("$SKILL/.venv/bin/python" -V)."
    echo "   Instala Python 3.12 (Mac: brew install python@3.12), borra $SKILL/.venv y vuelve a correr este script."
    exit 1
  }
}
# Seguimiento de manos y cuerpo (opcional: si falla, el resto de la skill funciona igual)
# Se instala SIN sus dependencias y luego se añaden a mano: mediapipe pide opencv-contrib-python,
# que choca con el OpenCV que ya instalamos (los dos traen cv2). Con el headless funciona igual.
# Tampoco se instalan matplotlib ni sounddevice: mediapipe solo los usa para dibujar y para audio,
# cosas que esta skill no hace (seguir.py registra un sustituto mínimo de matplotlib).
"$SKILL/.venv/bin/python" -c "import mediapipe" 2>/dev/null || {
  echo "→ Instalando seguimiento de manos y cuerpo (mediapipe, ~45 MB + dependencias: tarda)…"
  "$SKILL/.venv/bin/pip" install -q --no-deps mediapipe &&
  "$SKILL/.venv/bin/pip" install -q absl-py attrs certifi flatbuffers protobuf sentencepiece ||
    echo "⚠️  No se pudo instalar mediapipe: seguir.py no estará disponible (el resto sí)."
}
# Cambio de fondo con IA (opcional: si falla, el resto de la skill funciona igual)
"$SKILL/.venv/bin/python" -c "import onnxruntime" 2>/dev/null || {
  echo "→ Instalando recorte de fondo con IA (onnxruntime)…"
  "$SKILL/.venv/bin/pip" install -q onnxruntime || echo "⚠️  No se pudo instalar onnxruntime: fondo.py no estará disponible."
}
if [ ! -d "$SKILL/engine/node_modules/remotion" ]; then
  echo "→ Instalando Remotion (motor de edición)…"
  (cd "$SKILL/engine" && npm install --silent)
fi
chmod +x "$SKILL"/scripts/*.sh 2>/dev/null || true
echo "✅ Listo: dependencias instaladas"
