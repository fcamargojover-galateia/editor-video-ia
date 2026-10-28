#!/usr/bin/env python3
"""Paso 2: jump cuts. Quita pausas usando los tiempos por palabra, recorta el marco,
pasa a 1920x1080 y genera remotion/public/cut.mp4 + remotion/src/words.ts (tiempos ya cortados).

Uso:  cut.py <carpeta edicion-...> [--gap 0.28] [--crop auto|none|W:H:X:Y] [--drop "12.3-14.1,..."] [--muletillas]

--gap   pausa mínima (s) que se elimina. 0.28 = ritmo ágil tipo YouTube; 0.4 = más respirado.
--drop  tramos del video ORIGINAL a eliminar además de las pausas (tomas falsas, repeticiones).
--muletillas  quita "eh", "ehm", "mmm"… (funciona mejor si prep.py se corrió con --muletillas).
Si existe mejoras.json (scripts/mejorar.py) aplica el color, la limpieza y la voz de estudio.
Al final detecta la cara (remotion/src/face.ts) para que los zooms y recuadros la sigan.
Imprime la transcripción con los tiempos NUEVOS: esos son los que se usan en video.tsx.
"""
import argparse, json, re, subprocess
from pathlib import Path

PAD_IN, PAD_OUT = 0.06, 0.12   # aire antes/después de cada tramo para no comer sílabas
MAX_WORD = 0.95                # Whisper a veces "estira" una palabra sobre un silencio


def track_faces(video, out_ts, every=0.5):
    """Centro de la cara (en % del cuadro) cada `every` s, suavizado. Sin OpenCV o sin caras: no escribe nada."""
    try:
        import cv2
    except ImportError:
        return 0
    if not hasattr(cv2, "CascadeClassifier"):  # OpenCV 5 lo quitó: setup.sh instala OpenCV 4
        return 0
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(1, int(round(fps * every)))
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    pts, i, last = [], 0, None
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % step == 0:
            ok, fr = cap.retrieve()
            if ok:
                h, w = fr.shape[:2]
                small = cv2.cvtColor(cv2.resize(fr, (640, int(640 * h / w))), cv2.COLOR_BGR2GRAY)
                f = cas.detectMultiScale(small, 1.1, 6, minSize=(40, 40))
                if len(f):
                    x, y, fw, fh = max(f, key=lambda r: r[2] * r[3])
                    last = ((x + fw / 2) / small.shape[1] * 100, (y + fh / 2) / small.shape[0] * 100)
                if last:
                    pts.append([round(i / fps, 2), *last])
        i += 1
    cap.release()
    if not pts:
        return 0
    # mediana móvil (5 muestras) para que el encuadre no tiemble
    sm = []
    for k in range(len(pts)):
        win = pts[max(0, k - 2):k + 3]
        sm.append([pts[k][0], round(sorted(p[1] for p in win)[len(win) // 2], 1), round(sorted(p[2] for p in win)[len(win) // 2], 1)])
    Path(out_ts).write_text("// Lo genera cut.py: [segundo, x %, y %] del centro de la cara.\n"
                            "export const FACE: [number, number, number][] = " + json.dumps(sm) + ";\n")
    return len(sm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--gap", type=float, default=0.28)
    ap.add_argument("--crop", default="auto")
    ap.add_argument("--drop", default="")
    ap.add_argument("--muletillas", action="store_true")
    ap.add_argument("--sin-cortes", dest="sin_cortes", action="store_true",
                    help="conserva el video entero (para videos con poca voz: demos, gestos, música)")
    a = ap.parse_args()
    work = Path(a.work).expanduser().resolve()
    video = (work / "source.txt").read_text().strip()
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]))

    import sys; sys.path.insert(0, str(Path(__file__).resolve().parent)); from fixes import fix_words, sin_muletillas
    W = fix_words(json.loads((work / "words.json").read_text()))
    for w in W:
        if w["e"] - w["s"] > MAX_WORD:
            w["e"] = round(w["s"] + 0.8, 2)
    drops = []
    for part in filter(None, a.drop.split(",")):
        x, y = part.split("-"); drops.append((float(x), float(y)))
    W = [w for w in W if not any(x <= (w["s"] + w["e"]) / 2 <= y for x, y in drops)]
    if a.muletillas:
        antes = len(W)
        W = sin_muletillas(W)
        print(f"Muletillas quitadas: {antes - len(W)}")

    if a.sin_cortes:
        # el video entero: los tiempos de las palabras no cambian
        merged = [[0.0, dur]]
        nw = [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in W]
    else:
        segs = []
        for w in W:
            if segs and w["s"] - segs[-1][1] < a.gap:
                segs[-1][1] = w["e"]
            else:
                segs.append([w["s"], w["e"]])
        segs = [[max(0, s - PAD_IN), min(dur, e + PAD_OUT)] for s, e in segs]
        merged = []
        for s, e in segs:
            if merged and s <= merged[-1][1]:
                merged[-1][1] = e
            else:
                merged.append([s, e])

        t, mp = 0.0, []
        for s, e in merged:
            mp.append((s, e, t)); t += e - s

        def remap(x):
            for s, e, o in mp:
                if s - 0.01 <= x <= e + 0.01:
                    return round(o + min(max(x, s), e) - s, 3)
            return None

        nw = [{"w": w["w"], "s": remap(w["s"]), "e": remap(w["e"])} for w in W]
        nw = [w for w in nw if w["s"] is not None]

    crop = a.crop
    if crop == "auto":
        crop = (work / "crop.txt").read_text().strip() if (work / "crop.txt").exists() else "none"
    vf = ("crop=%s," % crop if crop != "none" else "") + \
        "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30"
    mej = json.loads((work / "mejoras.json").read_text()) if (work / "mejoras.json").exists() else {}
    if mej.get("video"):
        vf += "," + mej["video"]
    achain = mej.get("audio", "")

    parts = "".join(
        f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}];"
        f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, e - s - 0.03):.3f}:d=0.03[a{i}];"
        for i, (s, e) in enumerate(merged))
    parts += "".join(f"[v{i}][a{i}]" for i in range(len(merged)))
    parts += f"concat=n={len(merged)}:v=1:a=1[vc][ac];[vc]{vf}[vo]"
    if achain:
        parts += f";[ac]{achain}[ao]"
    (work / "filter.txt").write_text(parts)

    out = work / "remotion" / "public" / "cut.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-filter_complex_script", str(work / "filter.txt"),
                    "-map", "[vo]", "-map", "[ao]" if achain else "[ac]", "-c:v", "libx264", "-crf", "17", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k", str(out)], check=True)
    real = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)]))

    (work / "cut.json").write_text(json.dumps({"segments": merged, "duration": real, "words": nw}, ensure_ascii=False, indent=1))
    (work / "remotion" / "src" / "words.ts").write_text(
        f"export const DURATION = {real:.3f};\nexport const WORDS: {{ w: string; s: number; e: number }}[] = "
        + json.dumps(nw, ensure_ascii=False) + ";\n")

    if real < dur * 0.5:
        print(f"AVISO: se quedó solo el {100 * real / dur:.0f}% del video ({dur:.1f}s → {real:.1f}s).")
        print("  cut.py conserva únicamente lo que se HABLA. Si el video tiene poca voz (demostraciones,")
        print("  gestos, música), pásale --gap 99 y además --sin-cortes para conservarlo entero.")
    print(f"{dur:.1f}s → {real:.1f}s ({len(merged)} tramos). Recorte: {crop}"
          + (" · mejoras aplicadas" if mej else ""))
    nf = track_faces(out, work / "remotion" / "src" / "face.ts")
    print(f"Seguimiento de cara: {nf} puntos" if nf else "Seguimiento de cara: no disponible (zooms al centro)")
    if (work / "fondo.json").exists():
        (work / "remotion" / "public" / "cut_original.mp4").unlink(missing_ok=True)
        print("AVISO: este video tenía el fondo cambiado. Vuelve a correr fondo.py (los cortes cambiaron).")
    print()
    # transcripción con tiempos nuevos, agrupada por frases, para planificar escenas
    line, start = [], None
    for w in nw:
        if start is None: start = w["s"]
        line.append(f"{w['w']}@{w['s']:.2f}")
        if w["w"].endswith((".", "?", "!")) or len(line) >= 14:
            print(f"[{start:6.2f}] " + " ".join(line)); line, start = [], None
    if line: print(f"[{start:6.2f}] " + " ".join(line))


if __name__ == "__main__":
    main()
