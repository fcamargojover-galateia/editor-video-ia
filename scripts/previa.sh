#!/bin/bash
# Vista previa RÁPIDA (baja resolución, sin mezcla de audio final) de un tramo, para iterar sin esperar el render completo.
# Uso: previa.sh <carpeta edicion-... o reels/N> [desde_seg=0] [hasta_seg=12] [escala=0.4]
# Salida: <carpeta>/remotion/out/previa.mp4  (se abre con `open`)
set -e
WORK="$(cd "$1" && pwd)"; DESDE="${2:-0}"; HASTA="${3:-12}"; ESC="${4:-0.4}"
cd "$WORK/remotion"; mkdir -p out
A=$(python3 -c "print(int(float('$DESDE')*30))"); B=$(python3 -c "print(int(float('$HASTA')*30))")
npx remotion render src/index.ts Main out/previa.mp4 --frames="$A-$B" --scale="$ESC" --crf=34 --log=error 2>&1 | grep -v "network requests" || true
echo "$WORK/remotion/out/previa.mp4"
