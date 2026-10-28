#!/usr/bin/env python3
"""Mejoras de imagen y sonido: corrección de color automática, look de cine (LUT), limpieza de ruido,
nitidez, estabilización y voz de estudio. Se corre UNA vez antes de cut.py / reel_prep.py.

Uso:  mejorar.py <carpeta edicion-...> [--look natural] [--intensidad 0.7] [--auto/--no-auto]
                 [--denoise 0|1|2] [--nitidez 0|1|2] [--estabilizar] [--voz pro] [--piel]

--look        natural · cinematico · calido · frio · moody · vibrante · pastel · bn · ninguno
--intensidad  0–1, cuánto se nota el look (0,6–0,8 suele verse profesional sin exagerar)
--auto        exposición, contraste y balance de blancos automáticos (activado por defecto)
--denoise     limpia el ruido/grano de la cámara (1 = suave, 2 = fuerte: poca luz)
--nitidez     enfoque (1 = suave, 2 = marcado). No usar 2 con caras muy cerca.
--estabilizar quita temblores leves (grabaciones con celular en la mano)
--voz         off · limpia (quita zumbido/ruido de fondo) · pro (limpia + EQ + de-esser + compresor)
              · radio (pro con más cuerpo y compresión)
--piel        protege los tonos de piel al aplicar looks fuertes (activado por defecto)

Escribe <carpeta>/mejoras.json (cut.py y reel_prep.py lo aplican solos, también al re-cortar),
<carpeta>/look.cube y <carpeta>/antes-despues.jpg para revisar. Para quitar todo: --reset.
"""
import argparse, json, math, re, subprocess
from pathlib import Path

LOOKS = ["natural", "cinematico", "calido", "frio", "moody", "vibrante", "pastel", "bn", "ninguno"]


def ffprobe_dur(v):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v]))


def stats(video, t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                          "-vf", "scale=640:-2,signalstats,metadata=print:file=-", "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    d = {}
    for k in ("YAVG", "YLOW", "YHIGH", "SATAVG", "UAVG", "VAVG"):
        m = re.search(rf"signalstats\.{k}=([\d.]+)", out)
        if m:
            d[k] = float(m.group(1))
    return d


def analizar(video, dur):
    ts = [dur * k / 9 for k in range(1, 9)]
    rows = [s for s in (stats(video, t) for t in ts) if len(s) == 6]
    if not rows:
        return None
    avg = {k: sum(r[k] for r in rows) / len(rows) for k in rows[0]}
    return avg


def correccion_auto(a):
    """Devuelve (filtros, notas) para exposición, contraste, balance y saturación."""
    clamp = lambda v, lo, hi: max(lo, min(hi, v))
    notas, f = [], []
    y = a["YAVG"]
    gamma = clamp((112 / max(20, y)) ** 0.55, 0.85, 1.35)
    rango = a["YHIGH"] - a["YLOW"]
    contrast = clamp(1 + (175 - rango) / 700, 1.0, 1.14)
    sat = 1.0
    if a["SATAVG"] < 22:
        sat = 1.12
    elif a["SATAVG"] > 60:
        sat = 0.95
    if abs(gamma - 1) > 0.03:
        notas.append(f"{'aclaro' if gamma > 1 else 'oscurezco'} los medios tonos (gamma {gamma:.2f})")
    if contrast > 1.01:
        notas.append(f"subo contraste ×{contrast:.2f}")
    if sat != 1:
        notas.append(f"saturación ×{sat:.2f}")
    f.append(f"eq=gamma={gamma:.3f}:contrast={contrast:.3f}:saturation={sat:.3f}")
    # balance de blancos: U>128 = dominante azul, V>128 = dominante roja. La piel sube V de forma natural
    # (≈ +6), así que solo se corrige lo que pasa de eso y a mitad de fuerza.
    du = a["UAVG"] - 128
    dv = a["VAVG"] - 134
    bm = clamp(-du / 128 * 1.6, -0.15, 0.15) if abs(du) > 3 else 0
    rm = clamp(-dv / 128 * 1.2, -0.15, 0.15) if abs(dv) > 4 else 0
    if bm or rm:
        gm = clamp(-(bm + rm) / 3, -0.06, 0.06)
        f.append(f"colorbalance=rm={rm:.3f}:gm={gm:.3f}:bm={bm:.3f}:rs={rm * 0.5:.3f}:bs={bm * 0.5:.3f}")
        cast = []
        if bm < 0: cast.append("azul")
        if bm > 0: cast.append("amarilla")
        if rm < 0: cast.append("roja/naranja")
        if rm > 0: cast.append("verde/cian")
        notas.append("corrijo dominante " + " y ".join(cast))
    return f, notas


# ---------- looks: función (r,g,b) 0–1 → (r,g,b) ----------
def smooth(x, k=0.5):
    """curva S: k = fuerza"""
    s = x * x * (3 - 2 * x)
    return x + (s - x) * k


def lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def es_piel(r, g, b):
    """peso 0–1 de cuánto se parece a un tono de piel (tono naranja, saturación media)"""
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 0.12 or mx - mn < 0.04:
        return 0.0
    if mx == r:
        h = ((g - b) / (mx - mn)) % 6 * 60
    elif mx == g:
        h = ((b - r) / (mx - mn) + 2) * 60
    else:
        h = ((r - g) / (mx - mn) + 4) * 60
    s = (mx - mn) / mx
    wh = max(0.0, 1 - abs(h - 22) / 22)
    ws = max(0.0, 1 - abs(s - 0.42) / 0.35)
    return wh * ws


def look_fn(name):
    def sat(r, g, b, k):
        l = lum(r, g, b)
        return l + (r - l) * k, l + (g - l) * k, l + (b - l) * k

    def split(r, g, b, sh, hi, k):
        l = lum(r, g, b)
        ws, wh = (1 - l) ** 2, l ** 2
        return (r + k * (ws * sh[0] + wh * hi[0]), g + k * (ws * sh[1] + wh * hi[1]), b + k * (ws * sh[2] + wh * hi[2]))

    def natural(r, g, b):
        r, g, b = (smooth(c, 0.25) for c in (r, g, b))
        return sat(r, g, b, 1.05)

    def cinematico(r, g, b):
        r, g, b = (smooth(c, 0.45) for c in (r, g, b))
        r, g, b = split(r, g, b, (-0.06, 0.02, 0.07), (0.07, 0.02, -0.06), 1.0)
        return sat(r, g, b, 0.92)

    def calido(r, g, b):
        r, g, b = (smooth(c, 0.3) for c in (r, g, b))
        return sat(r * 1.05 + 0.01, g * 1.01, b * 0.9, 1.06)

    def frio(r, g, b):
        r, g, b = (smooth(c, 0.3) for c in (r, g, b))
        return sat(r * 0.94, g * 1.0, b * 1.07 + 0.01, 0.97)

    def moody(r, g, b):
        r, g, b = (0.06 + 0.9 * smooth(c, 0.55) for c in (r, g, b))
        r, g, b = split(r, g, b, (-0.03, 0.03, 0.05), (0.04, 0.01, -0.03), 1.0)
        return sat(r, g, b, 0.78)

    def vibrante(r, g, b):
        r, g, b = (smooth(c, 0.35) for c in (r, g, b))
        return sat(r, g, b, 1.28)

    def pastel(r, g, b):
        r, g, b = (0.08 + 0.88 * smooth(c, 0.15) for c in (r, g, b))
        r, g, b = split(r, g, b, (0.02, 0.0, 0.05), (0.05, 0.02, 0.0), 1.0)
        return sat(r, g, b, 0.85)

    def bn(r, g, b):
        l = smooth(0.25 * r + 0.65 * g + 0.1 * b, 0.6)
        return l, l, l

    return {"natural": natural, "cinematico": cinematico, "calido": calido, "frio": frio, "moody": moody,
            "vibrante": vibrante, "pastel": pastel, "bn": bn}[name]


def escribir_lut(path, name, intensidad, piel=True, n=33):
    fn = look_fn(name)
    lines = [f'TITLE "{name}"', f"LUT_3D_SIZE {n}", ""]
    for bi in range(n):
        for gi in range(n):
            for ri in range(n):
                r, g, b = ri / (n - 1), gi / (n - 1), bi / (n - 1)
                lr, lg, lb = fn(r, g, b)
                k = intensidad
                if piel and name != "bn":
                    k *= 1 - 0.55 * es_piel(r, g, b)
                out = [min(1, max(0, o + (l - o) * k)) for o, l in ((r, lr), (g, lg), (b, lb))]
                lines.append("%.5f %.5f %.5f" % tuple(out))
    # cube: el índice rojo varía más rápido
    Path(path).write_text("\n".join(lines) + "\n")


VOZ = {
    "off": "",
    "limpia": "highpass=f=75,afftdn=nr=10:nf=-42:tn=1,lowpass=f=16500",
    "pro": "highpass=f=75,afftdn=nr=12:nf=-42:tn=1,equalizer=f=250:t=q:w=1.1:g=-2.5,"
           "equalizer=f=3800:t=q:w=1.3:g=2.5,equalizer=f=11000:t=q:w=0.8:g=1.5,deesser=i=0.35,"
           "acompressor=threshold=0.08:ratio=3:attack=6:release=120:makeup=1.6",
    "radio": "highpass=f=70,afftdn=nr=12:nf=-42:tn=1,equalizer=f=130:t=q:w=1:g=2.5,equalizer=f=300:t=q:w=1:g=-3,"
             "equalizer=f=3500:t=q:w=1.2:g=3,deesser=i=0.45,"
             "acompressor=threshold=0.05:ratio=4.5:attack=4:release=90:makeup=2.2",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--look", default="natural", choices=LOOKS)
    ap.add_argument("--intensidad", type=float, default=0.7)
    ap.add_argument("--auto", dest="auto", action="store_true", default=True)
    ap.add_argument("--no-auto", dest="auto", action="store_false")
    ap.add_argument("--denoise", type=int, default=0, choices=[0, 1, 2])
    ap.add_argument("--nitidez", type=int, default=1, choices=[0, 1, 2])
    ap.add_argument("--estabilizar", action="store_true")
    ap.add_argument("--voz", default="pro", choices=list(VOZ))
    ap.add_argument("--piel", dest="piel", action="store_true", default=True)
    ap.add_argument("--no-piel", dest="piel", action="store_false")
    ap.add_argument("--reset", action="store_true", help="quita todas las mejoras")
    a = ap.parse_args()

    work = Path(a.work).expanduser().resolve()
    if a.reset:
        for f in ("mejoras.json", "look.cube"):
            (work / f).unlink(missing_ok=True)
        print("Mejoras quitadas. Vuelve a correr cut.py / reel_prep.py.")
        return
    video = (work / "source.txt").read_text().strip()
    dur = ffprobe_dur(video)

    vf, notas = [], []
    if a.estabilizar:
        vf.append("deshake=rx=32:ry=32")
        notas.append("estabilizo temblores leves")
    if a.denoise:
        vf.append("hqdn3d=2:1.5:4:3" if a.denoise == 1 else "hqdn3d=4:3:7:6")
        notas.append("limpio el ruido de la imagen")
    if a.auto:
        st = analizar(video, dur)
        if st:
            f, n = correccion_auto(st)
            vf += f; notas += n
            print("Medición: brillo %.0f · rango %.0f–%.0f · saturación %.0f · U %.1f · V %.1f"
                  % (st["YAVG"], st["YLOW"], st["YHIGH"], st["SATAVG"], st["UAVG"], st["VAVG"]))
    if a.look != "ninguno" and a.intensidad > 0:
        cube = work / "look.cube"
        escribir_lut(cube, a.look, max(0, min(1, a.intensidad)), a.piel)
        vf.append(f"lut3d=file='{cube}':interp=tetrahedral")
        notas.append(f"look «{a.look}» al {int(a.intensidad * 100)} %" + (" (protegiendo la piel)" if a.piel and a.look != "bn" else ""))
    if a.nitidez:
        vf.append("unsharp=5:5:0.45:5:5:0" if a.nitidez == 1 else "unsharp=5:5:0.8:5:5:0")
        notas.append("enfoque " + ("suave" if a.nitidez == 1 else "marcado"))
    af = VOZ[a.voz]
    if af:
        notas.append(f"voz «{a.voz}»: " + {"limpia": "sin zumbido ni ruido de fondo",
                                           "pro": "limpia + ecualizada + sin sibilancias + comprimida",
                                           "radio": "tipo locutor, con más cuerpo"}[a.voz])

    cfg = {"video": ",".join(vf), "audio": af,
           "params": {k: getattr(a, k) for k in ("look", "intensidad", "auto", "denoise", "nitidez", "estabilizar", "voz", "piel")}}
    (work / "mejoras.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1))

    # antes / después (3 fotogramas, sin estabilizar ni ruido temporal para que sea rápido)
    prev_vf = ",".join(x for x in vf if not x.startswith(("deshake", "hqdn3d")))
    tiles = []
    for k, t in enumerate((dur * 0.2, dur * 0.5, dur * 0.8)):
        o = work / f"_ad{k}.jpg"
        chain = f"scale=640:-2,split[a][b];[b]{prev_vf}[c];[a][c]hstack" if prev_vf else "scale=640:-2,split[a][b];[a][b]hstack"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                        "-filter_complex", chain, str(o)], check=True)
        tiles.append(o)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", str(x)] for x in tiles], []) +
                   ["-filter_complex", f"vstack=inputs={len(tiles)}", str(work / "antes-despues.jpg")], check=True)
    for x in tiles:
        x.unlink()

    print("Mejoras guardadas:")
    for n in notas:
        print("  ·", n)
    print(f"Revisa {work / 'antes-despues.jpg'} (izquierda = original, derecha = mejorado).")
    print("Se aplican solas en cut.py y reel_prep.py (si ya cortaste, vuelve a correr cut.py).")


if __name__ == "__main__":
    main()
