#!/usr/bin/env python3
"""Entregables extra para publicar: subtítulos .srt, capítulos de YouTube y miniatura.

Uso:  extras.py <carpeta edicion-... o reels/<n>> [--srt] [--capitulos] [--fotos 4]
                [--miniatura "Título de la miniatura" [--destacar palabra] [--chip "NUEVO"] [--foto 2]]

--srt        subtitulos.srt (para subir a YouTube/LinkedIn: mejora el alcance y la accesibilidad)
--capitulos  capitulos.txt para la descripción de YouTube, desde las SectionCard de video.tsx
--fotos N    elige los N mejores fotogramas para miniatura (cara nítida, ojos abiertos, bien separados)
             → remotion/public/miniatura_N.jpg + miniaturas.jpg para elegir
--miniatura  renderiza la miniatura (1280x720; portada 1080x1920 en reels) con ese título → miniatura.jpg
Sin opciones hace todo lo que puede (srt + capítulos + fotos).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path


def tc(s, sep=","):
    h, m = int(s // 3600), int(s % 3600 // 60)
    return f"{h:02d}:{m:02d}:{s % 60:06.3f}".replace(".", sep)


def load_words(work):
    p = work / "remotion" / "src" / "words.ts"
    s = p.read_text()
    return json.loads(s[s.index("= [", s.index("WORDS")) + 2:].rstrip().rstrip(";"))


def srt(work):
    W = load_words(work)
    out, cur, n = [], [], 1
    for i, w in enumerate(W):
        cur.append(w)
        txt = " ".join(x["w"] for x in cur)
        nxt = W[i + 1] if i + 1 < len(W) else None
        if len(txt) >= 38 or re.search(r"[.?!]$", w["w"]) or not nxt or nxt["s"] - w["e"] > 0.6:
            out.append(f"{n}\n{tc(cur[0]['s'])} --> {tc(min(w['e'] + 0.3, nxt['s'] if nxt else w['e'] + 0.3))}\n{txt}\n")
            n += 1; cur = []
    (work / "subtitulos.srt").write_text("\n".join(out))
    print("·", work / "subtitulos.srt", f"({n - 1} bloques)")


def capitulos(work):
    src = (work / "remotion" / "src" / "video.tsx").read_text()
    caps = [(float(m.group(1)), m.group(2)) for m in
            re.finditer(r'<SectionCard[^>]*?from=\{([\d.]+)\}[^>]*?title="([^"]+)"', src, re.S)]
    if not caps:
        print("· capítulos: no hay SectionCard en video.tsx (Claude puede proponerlos leyendo la transcripción)")
        return
    lines = ["00:00 Introducción"] + [f"{int(t // 60):02d}:{int(t % 60):02d} {title}" for t, title in caps if t > 5]
    (work / "capitulos.txt").write_text("\n".join(lines) + "\n")
    print("·", work / "capitulos.txt"); print("   " + "\n   ".join(lines))


def fotos(work, n):
    try:
        import cv2, numpy as np
    except ImportError:
        print("· fotos: falta OpenCV (corre setup.sh)"); return []
    if not hasattr(cv2, "CascadeClassifier"):
        print("· fotos: tu OpenCV no trae el detector de caras; corre setup.sh (instala OpenCV 4)"); return []
    pub = work / "remotion" / "public"
    video = next((p for p in (pub / "cut.mp4", pub / "camwide.mp4", pub / "cam.mp4") if p.exists()), None)
    if not video:
        print("· fotos: no hay video cortado todavía"); return []
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eye = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    smile = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = int(fps * 1.0)
    cands, i = [], 0
    while True:
        if not cap.grab():
            break
        if i % step == 0:
            ok, fr = cap.retrieve()
            if ok:
                g = cv2.cvtColor(cv2.resize(fr, (960, int(960 * fr.shape[0] / fr.shape[1]))), cv2.COLOR_BGR2GRAY)
                fs = face.detectMultiScale(g, 1.1, 6, minSize=(80, 80))
                if len(fs):
                    x, y, w, h = max(fs, key=lambda r: r[2] * r[3])
                    roi = g[y:y + h, x:x + w]
                    sharp = cv2.Laplacian(roi, cv2.CV_64F).var()
                    eyes = len(eye.detectMultiScale(roi[: h // 2], 1.1, 8))
                    sm = len(smile.detectMultiScale(roi[h // 2:], 1.6, 20))
                    score = sharp * (1.6 if eyes >= 2 else 0.6) * (1.25 if sm else 1) * (w / g.shape[1] + 0.2)
                    cands.append((score, i / fps, fr))
        i += 1
    cap.release()
    cands.sort(key=lambda c: -c[0])
    picked = []
    for c in cands:
        if all(abs(c[1] - p[1]) > 8 for p in picked):
            picked.append(c)
        if len(picked) >= n:
            break
    paths = []
    for k, (_, t, fr) in enumerate(picked, 1):
        p = pub / f"miniatura_{k}.jpg"
        cv2.imwrite(str(p), fr, [cv2.IMWRITE_JPEG_QUALITY, 95]); paths.append(p)
    if paths:
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", str(p)] for p in paths], []) + ["-filter_complex",
                        "".join(f"[{k}]scale=480:-2[s{k}];" for k in range(len(paths))) + "".join(f"[s{k}]" for k in range(len(paths)))
                        + f"hstack=inputs={len(paths)}" if len(paths) > 1 else "[0]scale=480:-2", str(work / "miniaturas.jpg")], check=True)
        print("·", work / "miniaturas.jpg", "→ opciones:", ", ".join(f"{p.name} ({t:.0f}s)" for p, (_, t, _) in zip(paths, picked)))
    return paths


def miniatura(work, titulo, destacar, chip, foto):
    rem = work / "remotion"
    if not (rem / "public" / f"miniatura_{foto}.jpg").exists():
        fotos(work, max(4, foto))
    props = {"titulo": titulo, "foto": f"miniatura_{foto}.jpg"}
    if destacar: props["destacar"] = destacar
    if chip: props["chip"] = chip
    out = work / "miniatura.jpg"
    r = subprocess.run(["npx", "remotion", "still", "src/index.ts", "Miniatura", str(out), "--props", json.dumps(props, ensure_ascii=False),
                        "--log=error"], cwd=rem)
    if r.returncode == 0:
        print("·", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--srt", action="store_true"); ap.add_argument("--capitulos", action="store_true")
    ap.add_argument("--fotos", type=int, default=0)
    ap.add_argument("--miniatura"); ap.add_argument("--destacar"); ap.add_argument("--chip")
    ap.add_argument("--foto", type=int, default=1)
    a = ap.parse_args()
    work = Path(a.work).expanduser().resolve()
    todo = not (a.srt or a.capitulos or a.fotos or a.miniatura)
    if a.srt or todo: srt(work)
    if a.capitulos or todo: capitulos(work)
    if a.fotos or todo: fotos(work, a.fotos or 4)
    if a.miniatura: miniatura(work, a.miniatura, a.destacar, a.chip, a.foto)


if __name__ == "__main__":
    main()
