#!/usr/bin/env python3
"""Sigue las manos, los dedos, la cara y los hombros de la persona para pegarles objetos encima.

Uso:  seguir.py <carpeta edicion-... o reels/<n>> [--paso 0.1] [--ancho 640] [--manos 2] [--revisar 12.5]

Escribe remotion/src/puntos.ts con las pistas (en % del cuadro) y los gestos detectados.
En video.tsx se usan con <Seguir punto="manoDer" …> y <Mover pasos={[{punto:"manoDer"}, …]}>.

IZQUIERDA / DERECHA SON LAS DE LA PANTALLA (lo que ves), no las de la persona.

Puntos que genera:
  manoIzq manoDer          centro de la palma
  indiceIzq indiceDer      punta del índice
  pulgarIzq pulgarDer      punta del pulgar
  pinzaIzq pinzaDer        entre el pulgar y el índice (para "sostener" algo)
  munecaIzq munecaDer      muñeca
  cara  sobreCabeza  menton  hombroIzq  hombroDer  centroManos

Gestos: abierta · puno · senala · pinza · pulgar   (se imprimen con su segundo exacto)

--revisar S  además guarda seguimiento.jpg con los puntos dibujados en el segundo S (para comprobar).
La primera vez descarga los modelos (~12 MB). Tarda aproximadamente lo que dura el video.
"""
import argparse, json, math, subprocess, sys, urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
MODELOS = SKILL / "models"
URL_MANO = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
URL_POSE = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

# índices de MediaPipe Hands
MUNECA, PULGAR, INDICE, MEDIO, ANULAR, MENIQUE = 0, 4, 8, 12, 16, 20
BASES = [0, 5, 9, 13, 17]
PIP = {PULGAR: 2, INDICE: 6, MEDIO: 10, ANULAR: 14, MENIQUE: 18}


def bajar(url, dest):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"→ Descargando {dest.name}…")
    tmp = dest.with_suffix(".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)


def probe(v):
    d = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                            "stream=width,height:format=duration", "-of", "json", str(v)]))
    s = d["streams"][0]
    return s["width"], s["height"], float(d["format"]["duration"])


def dedos_extendidos(lm):
    """[pulgar, índice, medio, anular, meñique] extendido o no (comparando con la muñeca)"""
    w = lm[MUNECA]
    d = lambda p: math.hypot(p[0] - w[0], p[1] - w[1])
    out = []
    for tip in (PULGAR, INDICE, MEDIO, ANULAR, MENIQUE):
        out.append(d(lm[tip]) > d(lm[PIP[tip]]) * 1.12)
    return out


def gesto_de(lm):
    ext = dedos_extendidos(lm)
    pulgar, indice, medio, anular, menique = ext
    sep = math.hypot(lm[PULGAR][0] - lm[INDICE][0], lm[PULGAR][1] - lm[INDICE][1])
    palma = math.hypot(lm[0][0] - lm[9][0], lm[0][1] - lm[9][1]) + 1e-6
    # pinza = pulgar e índice juntos PERO la mano estirada hacia afuera.
    # (en un puño el pulgar y el índice también se tocan: por eso se exige que el índice se aleje
    #  de la muñeca más que la palma; si no, es puño.)
    alcance = math.hypot(lm[INDICE][0] - lm[MUNECA][0], lm[INDICE][1] - lm[MUNECA][1]) / palma
    if sep / palma < 0.38 and alcance > 1.35 and not medio and not anular:
        return "pinza"
    if all(ext[1:]):
        return "abierta"
    if not any(ext[1:]):
        return "pulgar" if pulgar else "puno"
    if indice and not medio and not anular and not menique:
        return "senala"
    return None


def mediana(vals):
    v = sorted(vals)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def suavizar(track, ventana=3, hueco_max=2):
    """Mediana móvil + media ligera. Rellena parpadeos del detector de hasta `hueco_max` muestras;
    los huecos más largos (la mano salió de cuadro) se conservan como None."""
    n = len(track)
    # 1. marcar qué huecos son cortos (se pueden rellenar) y cuáles no
    rellenable = [False] * n
    i = 0
    while i < n:
        if track[i] is None:
            j = i
            while j < n and track[j] is None:
                j += 1
            if j - i <= hueco_max and i > 0 and j < n:   # hueco corto y rodeado de datos
                for k in range(i, j):
                    rellenable[k] = True
            i = j
        else:
            i += 1
    out = []
    for i in range(n):
        if track[i] is None and not rellenable[i]:
            out.append(None); continue
        win = [p for p in track[max(0, i - ventana): i + ventana + 1] if p]
        if not win:
            out.append(None); continue
        out.append([round(mediana([p[0] for p in win]), 2), round(mediana([p[1] for p in win]), 2)])
    # media ligera para quitar el escalón de la mediana
    sm = []
    for i in range(n):
        a, b, c = out[max(0, i - 1)], out[i], out[min(n - 1, i + 1)]
        if not b:
            sm.append(None); continue
        xs = [p for p in (a, b, c) if p]
        sm.append([round(sum(p[0] for p in xs) / len(xs), 2), round(sum(p[1] for p in xs) / len(xs), 2)])
    return sm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--paso", type=float, default=0.1, help="segundos entre muestras (0.07 para manos muy rápidas)")
    ap.add_argument("--ancho", type=int, default=640)
    ap.add_argument("--manos", type=int, default=2)
    ap.add_argument("--revisar", type=float, help="guarda seguimiento.jpg con los puntos dibujados en ese segundo")
    a = ap.parse_args()

    try:
        import numpy as np
        # mediapipe importa matplotlib solo para una función de dibujo 3D que aquí no se usa
        # (tasks/python/vision/drawing_utils.py → plot_landmarks). Si no está instalado, se registra
        # un sustituto mínimo y así nos ahorramos ~20 MB de dependencias que nunca se ejecutan.
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            import types
            mpl = types.ModuleType("matplotlib")
            plt = types.ModuleType("matplotlib.pyplot")
            def _no_disponible(*_a, **_k):
                raise RuntimeError("matplotlib no está instalado (solo hace falta para dibujar en 3D).")
            for _f in ("figure", "axes", "show", "plot", "subplots"):
                setattr(plt, _f, _no_disponible)
            mpl.pyplot = plt
            sys.modules["matplotlib"] = mpl
            sys.modules["matplotlib.pyplot"] = plt
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
    except ImportError:
        sys.exit("Falta mediapipe: corre  bash scripts/setup.sh  (lo instala) y vuelve a intentar.")

    work = Path(a.work).expanduser().resolve()
    pub = work / "remotion" / "public"
    video = next((p for p in (pub / "cut.mp4", pub / "cam.mp4") if p.exists()), None)
    if not video:
        sys.exit("No encontré cut.mp4 ni cam.mp4: corre antes cut.py o reel_prep.py.")
    W, H, dur = probe(video)
    bajar(URL_MANO, MODELOS / "hand_landmarker.task")
    bajar(URL_POSE, MODELOS / "pose_landmarker_lite.task")

    manos = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELOS / "hand_landmarker.task")),
        running_mode=vision.RunningMode.VIDEO, num_hands=a.manos,
        min_hand_detection_confidence=0.45, min_tracking_confidence=0.45))
    pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODELOS / "pose_landmarker_lite.task")),
        running_mode=vision.RunningMode.VIDEO, num_poses=1))

    sw = a.ancho
    sh = round(H * sw / W / 2) * 2
    fps = 1 / a.paso
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps:.6f},scale={sw}:{sh}",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    size = sw * sh * 3
    nombres = ["manoIzq", "manoDer", "indiceIzq", "indiceDer", "pulgarIzq", "pulgarDer",
               "pinzaIzq", "pinzaDer", "munecaIzq", "munecaDer",
               "cara", "sobreCabeza", "menton", "hombroIzq", "hombroDer", "centroManos"]
    pistas = {n: [] for n in nombres}
    gestos_crudos = {"izq": [], "der": []}
    k = 0
    frames_rev = None
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        img = np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
        ms = int(k * a.paso * 1000)
        mpimg = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img))
        rm = manos.detect_for_video(mpimg, ms)
        rp = pose.detect_for_video(mpimg, ms)

        # --- manos, ordenadas por posición en PANTALLA (izquierda primero) ---
        detectadas = []
        for lmset in (rm.hand_landmarks or []):
            lm = [(p.x * 100, p.y * 100) for p in lmset]
            cx = sum(lm[i][0] for i in BASES) / len(BASES)
            detectadas.append((cx, lm))
        detectadas.sort(key=lambda h: h[0])
        lados = ["izq", "der"] if len(detectadas) == 2 else (["izq"] if detectadas and detectadas[0][0] < 50 else ["der"])
        por_lado = {}
        for lado, (_, lm) in zip(lados, detectadas):
            por_lado[lado] = lm
        for lado in ("izq", "der"):
            L = lado[0].upper() + lado[1:]
            lm = por_lado.get(lado)
            if lm:
                palma = [sum(lm[i][0] for i in BASES) / len(BASES), sum(lm[i][1] for i in BASES) / len(BASES)]
                pistas[f"mano{L}"].append([round(palma[0], 2), round(palma[1], 2)])
                pistas[f"indice{L}"].append([round(lm[INDICE][0], 2), round(lm[INDICE][1], 2)])
                pistas[f"pulgar{L}"].append([round(lm[PULGAR][0], 2), round(lm[PULGAR][1], 2)])
                pistas[f"pinza{L}"].append([round((lm[PULGAR][0] + lm[INDICE][0]) / 2, 2),
                                            round((lm[PULGAR][1] + lm[INDICE][1]) / 2, 2)])
                pistas[f"muneca{L}"].append([round(lm[MUNECA][0], 2), round(lm[MUNECA][1], 2)])
                gestos_crudos[lado].append((round(k * a.paso, 2), gesto_de(lm)))
            else:
                for pre in ("mano", "indice", "pulgar", "pinza", "muneca"):
                    pistas[f"{pre}{L}"].append(None)
                gestos_crudos[lado].append((round(k * a.paso, 2), None))
        if len(por_lado) == 2:
            mi, md = por_lado["izq"], por_lado["der"]
            pistas["centroManos"].append([round((mi[MUNECA][0] + md[MUNECA][0]) / 2, 2),
                                          round((mi[MUNECA][1] + md[MUNECA][1]) / 2, 2)])
        else:
            pistas["centroManos"].append(None)

        # --- cara y hombros (pose) ---
        pl = (rp.pose_landmarks or [None])[0]
        if pl:
            P = lambda i: [round(pl[i].x * 100, 2), round(pl[i].y * 100, 2)]
            nariz, oi, od = P(0), P(7), P(8)
            alto_cabeza = abs(oi[1] - nariz[1]) * 2 + 4
            pistas["cara"].append(nariz)
            pistas["sobreCabeza"].append([round((oi[0] + od[0]) / 2, 2), round(nariz[1] - alto_cabeza * 1.9, 2)])
            pistas["menton"].append([nariz[0], round(nariz[1] + alto_cabeza * 0.75, 2)])
            # hombros: 11 y 12, ordenados por pantalla
            h = sorted([P(11), P(12)], key=lambda p: p[0])
            pistas["hombroIzq"].append(h[0]); pistas["hombroDer"].append(h[1])
        else:
            for n in ("cara", "sobreCabeza", "menton", "hombroIzq", "hombroDer"):
                pistas[n].append(None)

        if a.revisar is not None and frames_rev is None and k * a.paso >= a.revisar:
            frames_rev = (img.copy(), {n: pistas[n][-1] for n in nombres})
        k += 1
    proc.stdout.close(); proc.wait()
    if not k:
        sys.exit("No pude leer el video.")

    pistas = {n: suavizar(v) for n, v in pistas.items()}
    vistos = {n: sum(1 for p in v if p) for n, v in pistas.items()}

    # --- gestos: tramos estables de al menos 0,25 s ---
    eventos = []
    for lado, serie in gestos_crudos.items():
        actual, desde = None, None
        minimo = max(2, int(0.25 / a.paso))
        cuenta = 0
        for t, g in serie:
            if g == actual:
                cuenta += 1
                if cuenta == minimo and actual:
                    eventos.append({"t": desde, "mano": lado, "gesto": actual})
            else:
                actual, desde, cuenta = g, t, 1
    eventos.sort(key=lambda e: e["t"])

    ts = work / "remotion" / "src" / "puntos.ts"
    cuerpo = ",\n".join(f'  {n}: {json.dumps(v)}' for n, v in pistas.items())
    ts.write_text(
        "// Lo genera scripts/seguir.py. Posiciones en % del cuadro; null = no se ve en ese momento.\n"
        "// Izquierda/derecha son las de la PANTALLA.\n"
        f"export const PASO = {a.paso};\n"
        "export type Punto = [number, number] | null;\n"
        'export type Gesto = "abierta" | "puno" | "senala" | "pinza" | "pulgar";\n'
        "export const PUNTOS: Record<string, Punto[]> = {\n" + cuerpo + "\n};\n"
        "export const GESTOS: { t: number; mano: \"izq\" | \"der\"; gesto: Gesto }[] = "
        + json.dumps(eventos, ensure_ascii=False) + ";\n")

    print(f"{k} muestras cada {a.paso}s ({dur:.1f}s de video) → {ts}")
    print("Visibilidad:", ", ".join(f"{n} {100 * vistos[n] // k}%" for n in
                                    ("manoIzq", "manoDer", "indiceDer", "cara", "hombroIzq") if n in vistos))
    if eventos:
        print(f"Gestos ({len(eventos)}):")
        for e in eventos[:25]:
            print(f"  {e['t']:6.2f}s  mano {e['mano']}  {e['gesto']}")
        if len(eventos) > 25:
            print(f"  … y {len(eventos) - 25} más")
    else:
        print("Gestos: ninguno claro (las manos pueden estar fuera de cuadro)")
    if max(vistos["manoIzq"], vistos["manoDer"]) < k * 0.25:
        print("AVISO: las manos casi no se ven. Mejor usar 'cara', 'sobreCabeza' u 'hombroDer', o un recorrido con <Mover>.")

    if frames_rev is not None:
        import numpy as np
        img, pts = frames_rev
        try:
            import cv2
            vis = cv2.cvtColor(img, cv2.COLOR_RGB2BGR).copy()
            for n, p in pts.items():
                if p:
                    x, y = int(p[0] / 100 * sw), int(p[1] / 100 * sh)
                    cv2.circle(vis, (x, y), 6, (60, 242, 215), -1)
                    cv2.putText(vis, n, (x + 8, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imwrite(str(work / "seguimiento.jpg"), vis)
            print("Revisa", work / "seguimiento.jpg")
        except ImportError:
            pass


if __name__ == "__main__":
    main()
