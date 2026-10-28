#!/usr/bin/env python3
"""Cambia o desenfoca el fondo de la persona con IA (Robust Video Matting, sin pantalla verde).

Uso:  fondo.py <carpeta edicion-... o reels/<n>> --modo desenfoque|estudio|color|degradado|imagen|video
               [--valor "#101018" | "#0B0A10,#A77BFF" | ruta.jpg | ruta.mp4] [--fuerza 1.0] [--preview 12.5]

--modo desenfoque  efecto retrato (bokeh): el fondo real, desenfocado (--fuerza 0.5–2)
       matte       NO cambia el fondo: genera public/persona.webm (tú recortada, con transparencia)
                   para que los objetos de seguir.tsx puedan pasar POR DETRÁS de ti (<Persona/>)
       estudio     fondo oscuro con luz suave detrás de la cabeza (usa los colores de theme.ts o --valor)
       color       color liso (--valor "#hex")
       degradado   dos colores (--valor "#arriba,#abajo")
       imagen      una foto (--valor ruta.jpg); se ajusta a pantalla completa
       video       un video en bucle (--valor ruta.mp4)
       original    deshace el cambio
--preview S        solo procesa el segundo S y guarda fondo-preview.jpg (para revisar rápido)

Trabaja sobre remotion/public/cut.mp4 (video largo) o cam.mp4 + camwide.mp4 (reel). Guarda el original
como *_original.mp4 y siempre parte de ese, así se puede cambiar de fondo las veces que haga falta.
La primera vez descarga el modelo (~15 MB). Tarda ~1–3 min por minuto de video en una Mac M1/M2.
"""
import argparse, json, subprocess, sys, urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
MODEL = SKILL / "models" / "rvm_mobilenetv3_fp32.onnx"
MODEL_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"


def hexrgb(h):
    h = h.strip().lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def theme_colors(work):
    """lee C.bg y C.violet del theme.ts del proyecto (si existe)"""
    import re
    for p in (work / "remotion" / "src" / "theme.ts",):
        if p.exists():
            s = p.read_text()
            bg = re.search(r'bg:\s*"(#[0-9A-Fa-f]{6})"', s)
            vi = re.search(r'violet:\s*"(#[0-9A-Fa-f]{6})"', s)
            return (bg.group(1) if bg else "#0B0A10"), (vi.group(1) if vi else "#A77BFF")
    return "#0B0A10", "#A77BFF"


def probe(v):
    d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                            "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(v)]))
    s = d["streams"][0]
    n, m = s["r_frame_rate"].split("/")
    return s["width"], s["height"], float(n) / float(m), float(d["format"]["duration"])


def get_model():
    if MODEL.exists():
        return
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    print("→ Descargando el modelo de recorte (Robust Video Matting, ~15 MB)…")
    tmp = MODEL.with_suffix(".part")
    urllib.request.urlretrieve(MODEL_URL, tmp)
    tmp.rename(MODEL)


def make_bg(mode, valor, W, H, work, np, cv2):
    if mode == "color":
        return np.full((H, W, 3), hexrgb(valor or "#101018"), np.uint8)
    if mode == "degradado":
        a, b = (valor or ",".join(theme_colors(work))).split(",")
        a, b = np.array(hexrgb(a), float), np.array(hexrgb(b), float)
        k = np.linspace(0, 1, H)[:, None, None]
        return np.broadcast_to(a * (1 - k) + b * k, (H, W, 3)).astype(np.uint8).copy()
    if mode == "estudio":
        bg, acc = theme_colors(work) if not valor else (valor.split(",") + [theme_colors(work)[1]])[:2]
        base = np.array(hexrgb(bg), float)
        luz = np.array(hexrgb(acc), float)
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W * 0.5) / (W * 0.45)) ** 2 + ((yy - H * 0.35) / (H * 0.55)) ** 2)
        glow = np.clip(1 - d, 0, 1)[..., None] ** 1.6
        img = base + (luz - base) * glow * 0.55 + 18 * glow
        vig = np.clip(1 - 0.35 * d, 0.55, 1)[..., None]
        return np.clip(img * vig, 0, 255).astype(np.uint8)
    if mode == "imagen":
        im = cv2.cvtColor(cv2.imread(str(Path(valor).expanduser())), cv2.COLOR_BGR2RGB)
        h, w = im.shape[:2]
        s = max(W / w, H / h)
        im = cv2.resize(im, (int(w * s + 1), int(h * s + 1)), interpolation=cv2.INTER_AREA)
        y0, x0 = (im.shape[0] - H) // 2, (im.shape[1] - W) // 2
        return im[y0:y0 + H, x0:x0 + W]
    return None


def reader(path, W, H, loop=False, ss=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-stream_loop", "-1"] if loop else []) + (["-ss", str(ss)] if ss is not None else []) + [
        "-i", str(path), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE)


def procesar(src, dst, mode, valor, fuerza, work, preview=None):
    import numpy as np, cv2, onnxruntime as ort
    W, H, fps, dur = probe(src)
    sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    ds = np.array([min(1.0, 512 / max(W, H))], np.float32)  # resolución interna ~512 px: rápido y estable
    static_bg = make_bg(mode, valor, W, H, work, np, cv2)
    bgr = reader(valor, W, H, loop=True) if mode == "video" else None
    rd = reader(src, W, H, ss=max(0, preview - 1.5) if preview is not None else None)
    n_frames = int(1.5 * fps) + 1 if preview is not None else None
    wr = None
    if mode == "matte" and preview is None:
        # VP9 con canal alfa: Chromium (Remotion) lo reproduce con <OffthreadVideo transparent />
        wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                               "-r", f"{fps:.5f}", "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
                               "-crf", "28", "-b:v", "0", "-an", str(dst)], stdin=subprocess.PIPE)
    elif preview is None:
        wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", f"{fps:.5f}",
                               "-i", "-", "-i", str(src), "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "17",
                               "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", str(dst)], stdin=subprocess.PIPE)
    size = W * H * 3
    k, last = 0, None
    total = int(dur * fps)
    while True:
        buf = rd.stdout.read(size)
        if len(buf) < size:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        x = (fr.astype(np.float32) / 255).transpose(2, 0, 1)[None]
        out = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": ds})
        pha = out[1][0, 0]
        rec = out[2:6]
        a = cv2.GaussianBlur(pha, (0, 0), 0.8)[..., None]
        if mode == "matte":
            bgf = None
        elif mode == "desenfoque":
            # desenfoque "normalizado": el fondo se rellena sin el halo de la persona
            sc = 0.25
            sw, sh = int(W * sc), int(H * sc)
            f_s = cv2.resize(fr, (sw, sh), interpolation=cv2.INTER_AREA).astype(np.float32)
            m_s = cv2.resize(1 - a[..., 0], (sw, sh), interpolation=cv2.INTER_AREA)[..., None]
            sig = max(2, 9 * fuerza)
            num = cv2.GaussianBlur(f_s * m_s, (0, 0), sig)
            den = cv2.GaussianBlur(m_s, (0, 0), sig)[..., None] if m_s.ndim == 2 else cv2.GaussianBlur(m_s[..., 0], (0, 0), sig)[..., None]
            bgf = cv2.resize(num / np.maximum(den, 1e-3), (W, H), interpolation=cv2.INTER_LINEAR)
        elif bgr is not None:
            b2 = bgr.stdout.read(size)
            bgf = np.frombuffer(b2, np.uint8).reshape(H, W, 3).astype(np.float32) if len(b2) == size else np.zeros((H, W, 3), np.float32)
        else:
            bgf = static_bg.astype(np.float32)
        if mode == "matte":
            al = np.clip(a[..., 0] * 255, 0, 255).astype(np.uint8)
            res = np.dstack([fr, al])
        else:
            comp = fr.astype(np.float32) * a + bgf * (1 - a)
            res = np.clip(comp, 0, 255).astype(np.uint8)
        if wr:
            wr.stdin.write(res.tobytes())
        last = res
        k += 1
        if preview is not None and k >= n_frames:
            break
        if wr and k % int(fps * 10) == 0:
            print(f"  {k / fps:5.0f}s / {dur:.0f}s", flush=True)
    rd.stdout.close(); rd.kill()
    if bgr:
        bgr.kill()
    if wr:
        wr.stdin.close(); wr.wait()
        if wr.returncode:
            sys.exit("Falló la escritura del video.")
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--modo", required=True, choices=["desenfoque", "estudio", "color", "degradado", "imagen", "video", "matte", "original"])
    ap.add_argument("--valor")
    ap.add_argument("--fuerza", type=float, default=1.0)
    ap.add_argument("--preview", type=float)
    a = ap.parse_args()
    work = Path(a.work).expanduser().resolve()
    pub = work / "remotion" / "public"
    targets = [pub / "cut.mp4"] if (pub / "cut.mp4").exists() else [p for p in (pub / "cam.mp4", pub / "camwide.mp4") if p.exists()]
    if a.modo == "matte":
        targets = targets[:1]
    if not targets:
        sys.exit("No encontré cut.mp4 ni cam.mp4: corre antes cut.py o reel_prep.py.")
    if a.modo in ("imagen", "video") and not a.valor:
        sys.exit("Falta --valor con la ruta de la imagen o del video de fondo.")

    if a.modo == "original":
        for t in targets:
            o = t.with_name(t.stem + "_original.mp4")
            if o.exists():
                o.replace(t)
        (work / "fondo.json").unlink(missing_ok=True)
        print("Fondo original restaurado.")
        return

    try:
        import onnxruntime  # noqa
    except ImportError:
        sys.exit("Falta onnxruntime: corre  bash scripts/setup.sh  (lo instala) y vuelve a intentar.")
    get_model()
    import cv2
    for t in targets:
        if a.modo == "matte":
            src = t.with_name(t.stem + "_original.mp4")
            src = src if src.exists() else t
            out = t.parent / "persona.webm"
            print(f"→ Recortando la persona para la profundidad ({out.name})…")
            procesar(src, out, "matte", None, 1.0, work)
            print("Listo. En video.tsx: pon <Persona /> DESPUÉS del objeto que debe quedar detrás de ti.")
            return
        orig = t.with_name(t.stem + "_original.mp4")
        if not orig.exists():
            t.replace(orig)
        if a.preview is not None:
            img = procesar(orig, None, a.modo, a.valor, a.fuerza, work, preview=a.preview)
            if not t.exists():
                orig.replace(t)  # en preview no se cambia nada
            out = work / ("fondo-preview.jpg" if t.stem != "camwide" else "fondo-preview-wide.jpg")
            cv2.imwrite(str(out), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            print("Preview:", out)
            continue
        print(f"→ {t.name}: fondo «{a.modo}»…")
        procesar(orig, t, a.modo, a.valor, a.fuerza, work)
    if a.preview is None:
        (work / "fondo.json").write_text(json.dumps({"modo": a.modo, "valor": a.valor, "fuerza": a.fuerza}))
        print("Listo. Revisa con stills.sh que los bordes del pelo y las manos se vean bien.")


if __name__ == "__main__":
    main()
