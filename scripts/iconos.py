#!/usr/bin/env python3
"""Íconos 3D (Fluent Emoji de Microsoft, licencia MIT) por palabra.

Uso:
  iconos.py buscar <palabra> [...]            -> archivo(s) de ícono para esas palabras
  iconos.py sugerir <carpeta-reel-o-video>    -> lista de momentos donde la voz dice una palabra con ícono
                                                 (tiempo, palabra, ícono) + copia los PNG a remotion/public/iconos/
  iconos.py listar                            -> todos los íconos disponibles

En Remotion: <Img src={staticFile("iconos/rocket_3d.png")} />
Si una palabra no tiene ícono, NO inventar: elegir otro de `listar`, o pedir permiso para bajar uno nuevo
(github.com/microsoft/fluentui-emoji/assets/<Nombre>/3D/<nombre>_3d.png).
"""
import json, re, shutil, sys, unicodedata
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "assets" / "iconos3d"

# raíz de palabra (sin tildes, minúscula) -> nombre de archivo sin "_3d.png"
MAPA = {
    # dinero y negocio
    "dinero": "money_bag", "plata": "money_with_wings", "billete": "dollar_banknote", "dolar": "dollar_banknote",
    "euro": "euro_banknote", "moneda": "coin", "ganancia": "money_bag", "ganar": "money_bag", "facturar": "money_bag",
    "ingreso": "money_with_wings", "venta": "shopping_bags", "vender": "shopping_bags", "vende": "shopping_bags",
    "comprar": "shopping_cart", "compra": "shopping_cart", "carrito": "shopping_cart", "tienda": "convenience_store",
    "ecommerce": "shopping_cart", "amazon": "package", "producto": "package", "paquete": "package", "envio": "delivery_truck",
    "logistica": "delivery_truck", "proveedor": "factory", "fabrica": "factory", "empresa": "office_building",
    "negocio": "briefcase", "trabajo": "briefcase", "banco": "bank", "tarjeta": "credit_card", "pago": "credit_card",
    "cobrar": "credit_card", "factura": "receipt", "precio": "label", "barato": "label", "oferta": "label",
    "descuento": "label", "entrada": "ticket", "regalo": "wrapped_gift", "premio": "trophy", "campeon": "trophy",
    "ganador": "1st_place_medal", "exito": "trophy", "lujo": "crown", "joya": "gem_stone", "valioso": "gem_stone",
    "objetivo": "bullseye", "meta": "bullseye", "foco": "bullseye", "idea": "light_bulb", "creativo": "light_bulb",
    "lanzar": "rocket", "lanzamiento": "rocket", "crecer": "rocket", "viral": "fire", "viralizar": "fire", "moda": "fire",
    "tendencia": "fire", "caliente": "fire", "rapido": "high_voltage", "energia": "high_voltage", "extraordinario": "high_voltage",
    "magia": "sparkles", "especial": "sparkles", "nuevo": "sparkles", "estrella": "star", "perfecto": "hundred_points",
    "correcto": "check_mark_button", "funciona": "check_mark_button", "listo": "check_mark_button", "error": "cross_mark",
    "mal": "cross_mark", "cuidado": "warning", "peligro": "warning", "riesgo": "warning", "problema": "warning",
    "importante": "red_exclamation_mark", "pregunta": "red_question_mark", "duda": "red_question_mark",
    "prohibido": "prohibited", "bloqueado": "no_entry", "seguro": "locked", "seguridad": "locked", "privado": "locked",
    "clave": "key", "acceso": "key", "buscar": "magnifying_glass_tilted_left", "busqueda": "magnifying_glass_tilted_left",
    "investigar": "magnifying_glass_tilted_left", "atraer": "magnet", "sistema": "gear", "automatizar": "gear",
    "proceso": "gear", "herramienta": "wrench", "tecnica": "hammer_and_wrench", "metodo": "toolbox",
    "tiempo": "hourglass_not_done", "esperar": "hourglass_not_done", "hora": "alarm_clock", "urgente": "alarm_clock",
    "minuto": "stopwatch", "calendario": "calendar", "fecha": "calendar", "semana": "tear-off_calendar", "mes": "spiral_calendar",
    "ano": "calendar", "nota": "memo", "apunte": "notebook", "libro": "books", "curso": "open_book", "estudiar": "open_book",
    "aprender": "graduation_cap", "universidad": "graduation_cap", "escuela": "school", "computadora": "laptop",
    "software": "laptop", "programa": "desktop_computer", "celular": "mobile_phone", "telefono": "telephone_receiver",
    "mouse": "computer_mouse", "teclado": "keyboard", "robot": "robot", "ia": "robot", "inteligencia": "brain",
    "mente": "brain", "pensar": "thinking_face", "intuicion": "brain", "mentalidad": "brain", "ojo": "eyes", "ver": "eyes",
    "mirar": "eyes", "mensaje": "speech_balloon", "hablar": "speech_balloon", "comentar": "left_speech_bubble",
    "anuncio": "megaphone", "publicidad": "megaphone", "marketing": "megaphone", "aviso": "loudspeaker",
    "voz": "microphone", "podcast": "studio_microphone", "video": "video_camera", "grabar": "video_camera",
    "pelicula": "movie_camera", "foto": "camera", "escena": "clapper_board", "television": "television",
    "audio": "headphone", "musica": "musical_note", "amor": "red_heart", "pasion": "red_heart", "favorito": "red_heart",
    "mundo": "globe_showing_americas", "global": "globe_with_meridians", "internet": "globe_with_meridians",
    "web": "globe_with_meridians", "pais": "world_map", "estados": "world_map", "mundial": "soccer_ball", "futbol": "soccer_ball",
    "basquet": "basketball", "juego": "game_die", "azar": "game_die", "pieza": "puzzle_piece", "enlace": "link",
    "adjunto": "paperclip", "correo": "envelope", "email": "e-mail", "satelite": "satellite_antenna", "rumbo": "compass",
    "futuro": "crystal_ball", "prediccion": "crystal_ball", "ciencia": "atom_symbol", "pandemia": "microbe",
    "virus": "microbe", "enfermedad": "microbe", "salud": "stethoscope", "medicina": "pill", "vacuna": "syringe",
    "nube": "cloud", "tsunami": "water_wave", "ola": "water_wave", "tornado": "tornado", "frio": "snowflake", "sol": "sun",
    "agua": "droplet", "planta": "seedling", "crecimiento": "seedling", "suerte": "four_leaf_clover", "navidad": "christmas_tree",
    "halloween": "jack-o-lantern", "fiesta": "party_popper", "celebrar": "party_popper", "cumpleanos": "balloon",
    "fuegos": "fireworks", "impacto": "collision", "choque": "collision", "mareo": "dizzy", "remolino": "cyclone",
    "spinner": "cyclone", "enojo": "anger_symbol", "muerte": "skull", "fantasma": "ghost", "extraterrestre": "alien",
    "risa": "face_with_tears_of_joy", "increible": "exploding_head", "sorpresa": "exploding_head", "miedo": "face_screaming_in_fear",
    "genial": "smiling_face_with_sunglasses", "wow": "star-struck", "rico": "money-mouth_face", "experto": "face_with_monocle",
    "nerd": "nerd_face", "celebracion": "partying_face", "ruego": "pleading_face", "secreto": "shushing_face",
    "crecer_flecha": "up-right_arrow", "subir": "up-right_arrow", "bajar": "down_arrow", "repetir": "repeat_button",
    "ciclo": "clockwise_vertical_arrows", "escudo": "shield", "proteger": "shield", "justicia": "balance_scale",
    "ley": "balance_scale", "reglas": "balance_scale", "acuerdo": "handshake", "socio": "handshake", "alianza": "handshake",
    "paracaidas": "parachute", "viaje": "airplane", "avion": "airplane", "barco": "ship", "auto": "automobile",
    "moto": "motorcycle", "casa": "house", "hospital": "hospital", "comida": "hamburger", "pizza": "pizza", "cafe": "hot_beverage",
    "cajero": "atm_sign", "cambio": "currency_exchange", "calcular": "abacus", "lista": "clipboard", "registro": "ledger",
    "noticia": "newspaper", "documento": "scroll", "guardar": "bookmark", "varita": "magic_wand", "casino": "slot_machine",
    "videojuego": "video_game", "primero": "keycap_1", "segundo": "keycap_2", "tercero": "keycap_3", "tercer": "keycap_3",
    "cuarto": "keycap_4", "quinto": "keycap_5", "grafico": "chart_increasing", "estadistica": "bar_chart", "caer": "chart_decreasing",
    "pierde": "chart_decreasing", "perder": "chart_decreasing",
}
_SINACENTO = lambda s: "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _SINACENTO(w.lower()))


def buscar_palabra(w: str):
    n = norm(w)
    if not n:
        return None
    cand = [n]
    # singular / plural / sufijos verbales comunes
    for suf in ("s", "es", "ando", "iendo", "ar", "er", "ir", "ado", "ido", "an", "en", "mos"):
        if n.endswith(suf) and len(n) - len(suf) >= 3:
            cand.append(n[: -len(suf)])
    for c in cand:
        if c in MAPA:
            f = DIR / f"{MAPA[c]}_3d.png"
            if f.exists():
                return f.name
    return None


def cargar_palabras(carpeta: Path):
    for base in (carpeta / "remotion" / "src" / "words.ts", carpeta / "remotion" / "src" / "words.ts"):
        if base.exists():
            s = base.read_text()
            m = re.search(r"WORDS[^=]*= (\[.*\]);", s, re.S)
            return json.loads(m.group(1)), base.parent.parent / "public"
    sys.exit(f"No encuentro remotion/src/words.ts en {carpeta}")


def sugerir(carpeta: Path, min_sep: float = 3.0):
    words, public = cargar_palabras(carpeta)
    out, last = [], -99
    for w in words:
        ic = buscar_palabra(w["w"])
        if ic and w["s"] - last >= min_sep:
            out.append((w["s"], w["w"].strip(".,¿?!¡:;"), ic))
            last = w["s"]
    dest = public / "iconos"
    dest.mkdir(parents=True, exist_ok=True)
    for _, _, ic in out:
        shutil.copy(DIR / ic, dest / ic)
    print(f"{len(out)} momentos con ícono (separados ≥ {min_sep}s). Copiados a {dest}")
    for t, w, ic in out:
        print(f"  {t:6.2f}s  {w:<18} -> iconos/{ic}")
    print("\nEs una PROPUESTA: elegir los que cargan sentido (1 cada 3–8 s), no todos.")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "buscar":
        for w in a[1:]:
            print(f"{w}: {buscar_palabra(w) or 'sin ícono'}")
    elif a[0] == "sugerir" and len(a) > 1:
        sugerir(Path(a[1]).expanduser(), float(a[2]) if len(a) > 2 else 3.0)
    elif a[0] == "listar":
        print("\n".join(sorted(p.name.replace("_3d.png", "") for p in DIR.glob("*_3d.png"))))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
