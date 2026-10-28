#!/usr/bin/env python3
"""Control de calidad del MP4 final antes de publicar (lo que un editor revisa en la exportación).

Uso:  qc.py <video.mp4> [--plataforma youtube|instagram|tiktok]

Revisa: resolución y fps, volumen integrado (LUFS) y picos, saturación digital del audio, silencios
largos, fotogramas negros y congelados, duración máxima para la plataforma. Imprime ✅ / ⚠️ con qué hacer.
"""
import argparse, json, re, subprocess


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--plataforma", default="youtube", choices=["youtube", "instagram", "tiktok"])
    a = ap.parse_args()
    d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                            "stream=codec_type,width,height,r_frame_rate,sample_rate:format=duration,bit_rate",
                                            "-of", "json", a.video]))
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    au = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    dur = float(d["format"]["duration"])
    n, m = v["r_frame_rate"].split("/")
    fps = float(n) / float(m)
    res = []
    ok = lambda c, msg, fix="": res.append(("✅" if c else "⚠️ ", msg + ("" if c else f"  → {fix}")))

    W, H = v["width"], v["height"]
    vertical = H > W
    ok((vertical and W >= 1080) or (not vertical and H >= 1080), f"Resolución {W}x{H}", "exportar al menos en 1080p")
    if a.plataforma != "youtube":
        ok(vertical, "Formato vertical 9:16", "para Reels/TikTok usar la plantilla vertical")
    ok(abs(fps - round(fps)) < 0.02 and round(fps) in (24, 25, 30, 50, 60), f"{fps:.2f} fps", "usar 30 fps")
    lim = {"instagram": 180, "tiktok": 600, "youtube": 12 * 3600}[a.plataforma]
    ok(dur <= lim, f"Duración {dur:.1f}s", f"máximo {lim}s en {a.plataforma}")

    if not au:
        res.append(("⚠️ ", "El video no tiene audio"))
    else:
        e = run(["ffmpeg", "-nostats", "-i", a.video, "-af", "ebur128=peak=true", "-f", "null", "-"])
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)
        P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)
        if I:
            i = float(I[-1])
            ok(-15.5 <= i <= -12.5, f"Volumen {i:.1f} LUFS (objetivo −14)", "volver a renderizar con render.sh (normaliza solo)")
        if P:
            p = float(P[-1])
            ok(p <= -0.5, f"Pico máximo {p:.1f} dBFS", "hay saturación: bajar la música o los efectos")
        s = run(["ffmpeg", "-nostats", "-i", a.video, "-af", "silencedetect=n=-45dB:d=2.5", "-f", "null", "-"])
        sil = re.findall(r"silence_start: ([\d.]+)", s)
        ok(not sil, "Sin silencios largos" if not sil else f"Silencios de >2,5 s en: {', '.join(f'{float(x):.1f}s' for x in sil[:6])}",
           "revisar si es intencional; si no, recortar con cut.py --drop")

    b = run(["ffmpeg", "-nostats", "-i", a.video, "-vf", "blackdetect=d=0.4:pix_th=0.06", "-an", "-f", "null", "-"])
    blk = re.findall(r"black_start:([\d.]+)", b)
    ok(not blk, "Sin pantallas negras" if not blk else f"Negro en: {', '.join(f'{float(x):.1f}s' for x in blk[:6])}",
       "revisar el inicio/fin o un clip de b-roll que falta")
    f = run(["ffmpeg", "-nostats", "-i", a.video, "-vf", "freezedetect=n=-60dB:d=2", "-an", "-f", "null", "-"])
    frz = re.findall(r"freeze_start: ([\d.]+)", f)
    ok(not frz, "Sin imagen congelada" if not frz else f"Imagen congelada en: {', '.join(f'{float(x):.1f}s' for x in frz[:6])}",
       "un clip terminó antes que su tramo o falta un archivo en public/")

    print(f"Control de calidad · {a.video}")
    for icon, msg in res:
        print(f" {icon} {msg}")
    print("Recuerda: mirar el video completo CON audio antes de publicar.")


if __name__ == "__main__":
    main()
