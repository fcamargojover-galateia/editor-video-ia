#!/usr/bin/env python3
"""Aviso de CARTELES SOBRE LA CARA (tarjetas, títulos, subtítulos, íconos) en un render.

Uso:  caracheck.py <render.mp4> <fuente.mp4> [--escenas 54.2-57.9,12-14] [--paso 0.5] [--min 1.0]

Compara la grabación sin efectos (<fuente>: remotion/public/cam.mp4 en reels, cut.mp4 en videos largos)
con el render: si en la fuente se detecta la cara pero en el render NO, es probable que algo la esté tapando.

Lo que busca es un overlay ENCIMA de la cara mientras la persona habla (eso molesta). Un *cambio de enfoque*
—una escena a pantalla completa que reemplaza la toma para explicar algo o cerrar la idea— es un recurso
deseado, no un problema: declararlo con `--escenas inicio-fin,...` y queda fuera del aviso.

Es orientativo: un acercamiento fuerte, el blanco y negro o un giro de cabeza también pueden dar falsos
positivos. Revisar los tramos con stills.sh.
"""
import argparse
import cv2


def caras(path, paso):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    out, t = {}, 0.0
    while t * fps < n:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ok, fr = cap.read()
        if not ok:
            break
        h, w = fr.shape[:2]
        esc = 480 / max(h, w)
        g = cv2.cvtColor(cv2.resize(fr, (int(w * esc), int(h * esc))), cv2.COLOR_BGR2GRAY)
        c = det.detectMultiScale(g, 1.1, 4, minSize=(40, 40))
        out[round(t, 2)] = len(c) > 0
        t += paso
    cap.release()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("fuente")
    ap.add_argument("--paso", type=float, default=0.5)
    ap.add_argument("--min", type=float, default=1.0, dest="minimo")
    ap.add_argument("--escenas", default="", help="cambios de enfoque a pantalla completa, 'a-b,c-d' (no se avisan)")
    a = ap.parse_args()
    escenas = []
    for tramo in filter(None, (x.strip() for x in a.escenas.split(","))):
        ini, fin = tramo.split("-")
        escenas.append((float(ini), float(fin)))
    r, f = caras(a.render, a.paso), caras(a.fuente, a.paso)
    ts = sorted(t for t in r if t in f)
    malos = [t for t in ts if f[t] and not r[t]]
    con_cara = sum(1 for t in ts if f[t])
    tramos, ini, prev = [], None, None
    for t in malos:
        if ini is None:
            ini = prev = t
        elif t - prev <= a.paso * 1.01:
            prev = t
        else:
            tramos.append((ini, prev + a.paso)); ini = prev = t
    if ini is not None:
        tramos.append((ini, prev + a.paso))
    largos = [(s, e) for s, e in tramos if e - s >= a.minimo]
    dentro = lambda s, e: any(s >= x - 0.3 and e <= y + 0.8 for x, y in escenas)
    declarados = [(s, e) for s, e in largos if dentro(s, e)]
    avisos = [(s, e) for s, e in largos if not dentro(s, e)]
    print(f"Cara detectada en la fuente en {con_cara}/{len(ts)} muestras; sin detectar en el render en {len(malos)}.")
    for s, e in declarados:
        print(f"ℹ️  Cambio de enfoque declarado: {s:.1f}s – {e:.1f}s  ({e - s:.1f}s)")
    if not avisos:
        print("✅ Ningún cartel tapa la cara.")
        return
    print(f"⚠️  Posible cartel sobre la cara ≥ {a.minimo:g}s en:")
    for s, e in avisos:
        print(f"   {s:6.1f}s – {e:6.1f}s  ({e - s:.1f}s)")
    print("→ Revisar con stills.sh. Si es un cartel/subtítulo sobre el rostro: moverlo, achicarlo o acortarlo.")
    print("  Si es un cambio de enfoque a pantalla completa (recurso buscado): declararlo con --escenas y listo.")


if __name__ == "__main__":
    main()
