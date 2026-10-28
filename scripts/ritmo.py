#!/usr/bin/env python3
"""Detecta el tempo y los golpes (beats) de la música para sincronizar cortes, zooms y transiciones.

Uso:  ritmo.py <musica.wav|mp3> <carpeta edicion-... o reels/<n>> [--desde 0]

Escribe remotion/src/beats.ts (BPM y BEATS en segundos del video). En video.tsx: alBeat(t) lleva un tiempo
al golpe más cercano (fx.tsx). Usarlo en transiciones y punch-ins, NUNCA en cosas atadas a una palabra.
--desde  segundo de la canción donde arranca la música en el video (render.sh la usa desde 0).
"""
import argparse, subprocess, sys
from pathlib import Path


def main():
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("musica"); ap.add_argument("work")
    ap.add_argument("--desde", type=float, default=0)
    a = ap.parse_args()
    sr = 22050
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", str(a.desde), "-i", str(Path(a.musica).expanduser()),
                                   "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"])
    x = np.frombuffer(raw, np.float32)
    if len(x) < sr * 5:
        sys.exit("La música es demasiado corta para detectar el ritmo.")
    hop, win = 512, 2048
    n = 1 + (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    frames = x[idx] * np.hanning(win)[None, :]
    mag = np.log1p(np.abs(np.fft.rfft(frames, axis=1)))
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, mode="same")  # quitar la tendencia
    flux = np.maximum(flux, 0)
    flux /= flux.max() + 1e-9
    fps = sr / hop
    # tempo por autocorrelación entre 70 y 180 BPM (preferencia suave por ~100–120)
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    lags = np.arange(len(ac))
    bpm_l = 60 * fps / np.maximum(lags, 1)
    ok = (bpm_l >= 70) & (bpm_l <= 180)
    w = ac * np.exp(-0.5 * (np.log2(np.maximum(bpm_l, 1) / 110) / 0.9) ** 2)
    lag = lags[ok][np.argmax(w[ok])]
    bpm = 60 * fps / lag
    # fase: la que más energía junta sobre la grilla
    best, ph = -1, 0
    for p in range(int(lag)):
        sc = flux[p::int(lag)].sum()
        if sc > best:
            best, ph = sc, p
    period = 60 / bpm
    t0 = ph / fps
    beats = []
    t = t0
    dur = len(x) / sr
    while t < dur:
        # ajuste fino: el pico más cercano (±60 ms)
        i = int(round(t * fps)); r = int(0.06 * fps)
        seg = flux[max(0, i - r):i + r + 1]
        tt = (max(0, i - r) + int(np.argmax(seg))) / fps if len(seg) else t
        beats.append(round(tt, 3))
        t += period
    out = Path(a.work).expanduser().resolve() / "remotion" / "src" / "beats.ts"
    out.write_text("// Lo genera scripts/ritmo.py a partir de la música (tiempos de cada golpe, en segundos).\n"
                   f"export const BPM = {bpm:.1f};\nexport const BEATS: number[] = {beats};\n")
    print(f"Tempo: {bpm:.1f} BPM · {len(beats)} golpes · primer golpe en {beats[0]:.2f}s → {out}")


if __name__ == "__main__":
    main()
