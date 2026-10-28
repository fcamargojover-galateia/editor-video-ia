#!/usr/bin/env python3
"""[PREPARADO, SIN ACTIVAR] Genera imágenes o videos con IA para usarlos como fondo, b-roll u objetos.

HOY NO FUNCIONA: falta elegir proveedor y poner una clave (API key). Sin eso, el script explica
qué hace falta y no gasta nada. El resto de la skill funciona igual sin esto.

Uso (cuando esté activado):
  generar.py <carpeta edicion-...> --que "un cohete despegando, fondo negro" --tipo imagen
             [--formato 16:9|9:16|1:1] [--cuantas 1] [--transparente] [--nombre cohete]

--tipo imagen|video    video cuesta bastante más y tarda minutos
--transparente         solo imagen: recorta el fondo después de generar (usa fondo.py)
Guarda en remotion/public/generado/<nombre>.png|mp4 y dice cómo usarlo en video.tsx.

CÓMO ACTIVARLO (más adelante)
-----------------------------
1. Elige proveedor y consigue una clave:
   · openai     → imágenes y video (Sora). https://platform.openai.com/api-keys
   · gemini     → imágenes y video (Veo).  https://aistudio.google.com/apikey
   · replicate  → muchos modelos abiertos. https://replicate.com/account/api-tokens
   · kie        → imágenes y video con muchos modelos (Market). https://kie.ai/api-key
2. Crea  ~/.claude/skills/editor-video-ia/config.json  con:
       { "proveedor": "openai", "clave": "sk-...", "modelo_imagen": "", "modelo_video": "" }
   (o exporta la variable de entorno EDITOR_IA_CLAVE y EDITOR_IA_PROVEEDOR)
3. Verifica el nombre del modelo vigente en la documentación del proveedor y ponlo en el config:
   los nombres cambian seguido, por eso este script NO trae ninguno fijo.
4. Prueba:  generar.py <carpeta> --que "prueba" --tipo imagen --cuantas 1

AVISOS IMPORTANTES
------------------
· Cada generación CUESTA DINERO. La skill debe pedirte permiso y decirte el costo estimado antes.
· El texto de tu pedido (y nada más) se envía al proveedor. No se envía tu video ni tu audio.
· Derechos: no generar imágenes de personas reales, logos ni marcas de terceros.
· El código de llamada a cada API está escrito pero SIN PROBAR (no hay clave para probarlo):
  la primera vez puede necesitar un ajuste según la documentación vigente del proveedor.
"""
import argparse, base64, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CONFIG = SKILL / "config.json"
FORMATOS = {"16:9": (1536, 864), "9:16": (864, 1536), "1:1": (1024, 1024)}
# Costos aproximados por unidad, solo para avisar antes de gastar (revisar precios vigentes).
COSTO = {"imagen": 0.04, "video": 0.50}


def leer_config():
    cfg = {}
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
        except json.JSONDecodeError:
            sys.exit(f"{CONFIG} tiene un error de formato (JSON). Revísalo.")
    cfg.setdefault("proveedor", os.environ.get("EDITOR_IA_PROVEEDOR", ""))
    cfg.setdefault("clave", os.environ.get("EDITOR_IA_CLAVE", ""))
    return cfg


def sin_configurar(cfg):
    print("La generación de imágenes/video con IA todavía NO está activada.\n")
    print("Para activarla hacen falta dos cosas:")
    print("  1. Elegir proveedor (openai, gemini, replicate o kie) y crear una clave en su web.")
    print(f"  2. Crear {CONFIG} con:")
    print('     { "proveedor": "openai", "clave": "sk-...", "modelo_imagen": "<modelo vigente>" }\n')
    if cfg.get("proveedor") and not cfg.get("clave"):
        print(f"(Tienes proveedor «{cfg['proveedor']}» pero falta la clave.)")
    if cfg.get("clave") and not cfg.get("proveedor"):
        print("(Tienes clave pero falta decir el proveedor.)")
    print("Mientras tanto, para fondos y tomas de apoyo puedes usar:")
    print("  · tus propias fotos/videos            → fondo.py --modo imagen|video --valor ruta")
    print("  · fondos generados por la skill       → fondo.py --modo estudio|degradado|desenfoque")
    print("  · bancos gratuitos (Pexels, Pixabay)  → descargar a mano y usar --valor")
    sys.exit(2)


def pedir(url, datos, cabeceras, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(datos).encode(), headers={"Content-Type": "application/json", **cabeceras})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "ignore")[:600]
        sys.exit(f"El proveedor respondió {e.code}:\n{cuerpo}\n\n"
                 "Suele ser: nombre de modelo desactualizado (ponlo en config.json), clave inválida o sin saldo.")


# ---------- proveedores (código escrito, SIN PROBAR: ajustar según la doc vigente) ----------
def gen_openai(cfg, texto, tipo, formato, n):
    if tipo == "video":
        sys.exit("Video con OpenAI: revisa la documentación de Sora y completa esta función.")
    modelo = cfg.get("modelo_imagen") or sys.exit('Falta "modelo_imagen" en config.json (p. ej. el modelo de imágenes vigente).')
    w, h = FORMATOS[formato]
    r = pedir("https://api.openai.com/v1/images/generations",
              {"model": modelo, "prompt": texto, "n": n, "size": f"{w}x{h}"},
              {"Authorization": f"Bearer {cfg['clave']}"})
    return [base64.b64decode(d["b64_json"]) if "b64_json" in d else urllib.request.urlopen(d["url"]).read()
            for d in r.get("data", [])]


def gen_gemini(cfg, texto, tipo, formato, n):
    if tipo == "video":
        sys.exit("Video con Gemini (Veo): revisa la documentación y completa esta función.")
    modelo = cfg.get("modelo_imagen") or sys.exit('Falta "modelo_imagen" en config.json.')
    r = pedir(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={cfg['clave']}",
              {"contents": [{"parts": [{"text": texto}]}]}, {})
    out = []
    for c in r.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "inlineData" in p:
                out.append(base64.b64decode(p["inlineData"]["data"]))
    return out


def gen_replicate(cfg, texto, tipo, formato, n):
    modelo = cfg.get("modelo_video" if tipo == "video" else "modelo_imagen")
    if not modelo:
        sys.exit('Falta "modelo_imagen"/"modelo_video" en config.json (formato "owner/modelo").')
    cab = {"Authorization": f"Bearer {cfg['clave']}", "Prefer": "wait"}
    r = pedir(f"https://api.replicate.com/v1/models/{modelo}/predictions",
              {"input": {"prompt": texto, "aspect_ratio": formato}}, cab)
    for _ in range(60):
        if r.get("status") in ("succeeded", "failed", "canceled"):
            break
        time.sleep(5)
        with urllib.request.urlopen(urllib.request.Request(r["urls"]["get"], headers=cab)) as g:
            r = json.loads(g.read())
    if r.get("status") != "succeeded":
        sys.exit(f"La generación no terminó bien: {r.get('error') or r.get('status')}")
    salida = r["output"]
    urls = salida if isinstance(salida, list) else [salida]
    return [urllib.request.urlopen(u).read() for u in urls]


def gen_kie(cfg, texto, tipo, formato, n):
    """kie.ai Market: POST /api/v1/jobs/createTask y consulta en /api/v1/jobs/recordInfo.
    "modelo_imagen"/"modelo_video" = id del modelo tal como aparece en https://kie.ai/market
    (los campos de "input" pueden variar por modelo: ajustar según su página)."""
    modelo = cfg.get("modelo_video" if tipo == "video" else "modelo_imagen")
    if not modelo:
        sys.exit('Falta "modelo_imagen"/"modelo_video" en config.json (id del modelo en https://kie.ai/market).')
    base = "https://api.kie.ai/api/v1/jobs"
    cab = {"Authorization": f"Bearer {cfg['clave']}"}
    salidas = []
    for _ in range(n):
        r = pedir(f"{base}/createTask",
                  {"model": modelo, "input": {"prompt": texto, "aspect_ratio": formato}}, cab)
        if r.get("code") != 200:
            sys.exit(f"kie.ai rechazó la tarea: {r.get('code')} {r.get('msg')}")
        tid = r["data"]["taskId"]
        for _ in range(120):
            time.sleep(5)
            req = urllib.request.Request(f"{base}/recordInfo?taskId={tid}", headers=cab)
            with urllib.request.urlopen(req, timeout=60) as g:
                d = json.loads(g.read())
            info = d.get("data") or {}
            if info.get("state") == "success":
                salidas += json.loads(info["resultJson"]).get("resultUrls", [])
                break
            if info.get("state") == "fail":
                sys.exit(f"kie.ai falló: {info.get('failCode')} {info.get('failMsg')}")
        else:
            sys.exit(f"kie.ai no terminó a tiempo (taskId {tid}).")
    return [urllib.request.urlopen(u).read() for u in salidas]


PROVEEDORES = {"openai": gen_openai, "gemini": gen_gemini, "replicate": gen_replicate, "kie": gen_kie}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--que", required=True, help="qué quieres que genere, en español o inglés")
    ap.add_argument("--tipo", default="imagen", choices=["imagen", "video"])
    ap.add_argument("--formato", default="16:9", choices=list(FORMATOS))
    ap.add_argument("--cuantas", type=int, default=1)
    ap.add_argument("--nombre", default="generado")
    ap.add_argument("--transparente", action="store_true")
    ap.add_argument("--si", action="store_true", help="confirmar el gasto sin preguntar")
    a = ap.parse_args()

    cfg = leer_config()
    if not cfg.get("proveedor") or not cfg.get("clave"):
        sin_configurar(cfg)
    if cfg["proveedor"] not in PROVEEDORES:
        sys.exit(f"Proveedor «{cfg['proveedor']}» desconocido. Opciones: {', '.join(PROVEEDORES)}")

    costo = COSTO[a.tipo] * a.cuantas
    print(f"Generar {a.cuantas} {a.tipo}(s) con {cfg['proveedor']} · costo estimado ≈ US$ {costo:.2f}")
    if not a.si:
        if input("¿Continuar? (s/n) ").strip().lower() not in ("s", "si", "sí", "y"):
            sys.exit("Cancelado.")

    out_dir = Path(a.work).expanduser().resolve() / "remotion" / "public" / "generado"
    out_dir.mkdir(parents=True, exist_ok=True)
    datos = PROVEEDORES[cfg["proveedor"]](cfg, a.que, a.tipo, a.formato, a.cuantas)
    if not datos:
        sys.exit("El proveedor no devolvió ningún archivo.")
    ext = "mp4" if a.tipo == "video" else "png"
    rutas = []
    for i, b in enumerate(datos, 1):
        p = out_dir / (f"{a.nombre}.{ext}" if len(datos) == 1 else f"{a.nombre}_{i}.{ext}")
        p.write_bytes(b)
        rutas.append(p)
        print("·", p)
    print("\nEn video.tsx:")
    if a.tipo == "video":
        print(f'  b-roll: {{ from, to, src: "generado/{rutas[0].name}" }}  ·  fondo: fondo.py --modo video --valor "{rutas[0]}"')
    else:
        print(f'  objeto: <Img src={{staticFile("generado/{rutas[0].name}")}} style={{{{ height: 220 }}}} />')
        print(f'  fondo:  fondo.py --modo imagen --valor "{rutas[0]}"')
    if a.transparente:
        print("\nPara recortarle el fondo a la imagen, usa una herramienta de recorte o pídeselo a Claude.")


if __name__ == "__main__":
    main()
