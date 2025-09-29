import os
import sys
import requests
import datetime
import re
from dotenv import load_dotenv

# ---------- CONFIG ----------
# Cargar variables desde el archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
# ----------------------------

# Modo de orden desde argumentos
if len(sys.argv) > 1:
    MODO_ORDEN = sys.argv[1].strip().lower()
    if MODO_ORDEN not in ("liga", "hora"):
        print("❌ Modo no válido. Usa: liga o hora")
        sys.exit(1)
else:
    MODO_ORDEN = "liga"

# Diccionario de banderas
banderas = {    
    "españa": "🇪🇸", "spain": "🇪🇸", "laliga": "🇪🇸",
    "inglaterra": "🇬🇧", "england": "🇬🇧", "premier league": "🇬🇧", "fa cup": "🇬🇧",
    "alemania": "🇩🇪", "germany": "🇩🇪", "bundesliga": "🇩🇪", "dfb pokal": "🇩🇪",
    "francia": "🇫🇷", "france": "🇫🇷", "ligue 1": "🇫🇷", "coupe de france": "🇫🇷",
    "italia": "🇮🇹", "italy": "🇮🇹", "serie a": "🇮🇹", "coppa italia": "🇮🇹",
    "portugal": "🇵🇹", "primeira liga": "🇵🇹", "liga portugal": "🇵🇹", "taça de portugal": "🇵🇹",
    "países bajos": "🇳🇱", "netherlands": "🇳🇱", "eredivisie": "🇳🇱",
    "bélgica": "🇧🇪", "belgium": "🇧🇪", "jupiler pro league": "🇧🇪",
    "suiza": "🇨🇭", "switzerland": "🇨🇭", "super league": "🇨🇭",
    "austria": "🇦🇹", "austria bundesliga": "🇦🇹",
    "escocia": "🏴", "scotland": "🏴", "scottish premiership": "🏴",
    "dinamarca": "🇩🇰", "denmark": "🇩🇰", "superligaen": "🇩🇰",
    "suecia": "🇸🇪", "sweden": "🇸🇪", "allsvenskan": "🇸🇪",
    "finlandia": "🇫🇮", "finland": "🇫🇮", "veikkausliiga": "🇫🇮",
    "noruega": "🇳🇴", "norway": "🇳🇴", "eliteserien": "🇳🇴",
    "polonia": "🇵🇱", "poland": "🇵🇱", "ekstraklasa": "🇵🇱",
    "turquía": "🇹🇷", "turkey": "🇹🇷", "super lig": "🇹🇷",
    "grecia": "🇬🇷", "greece": "🇬🇷", "super league greece": "🇬🇷",
    "rusia": "🇷🇺", "russia": "🇷🇺", "premier liga": "🇷🇺",
    "ucrania": "🇺🇦", "ukraine": "🇺🇦", "premier liga": "🇺🇦",
    "croacia": "🇭🇷", "croatia": "🇭🇷", "hnl": "🇭🇷",
    "chequia": "🇨🇿", "czech republic": "🇨🇿", "1. liga": "🇨🇿",
    "bulgaria": "🇧🇬", "bulgaria first league": "🇧🇬",
    "hungría": "🇭🇺", "hungary": "🇭🇺", "nb i": "🇭🇺",
    "serbia": "🇷🇸", "serbia superliga": "🇷🇸",
    "eslovenia": "🇸🇮", "slovenia": "🇸🇮", "prva liga": "🇸🇮",
    "romania": "🇷🇴", "romania": "🇷🇴", "liga i": "🇷🇴",
    "japon": "🇯🇵", "japan": "🇯🇵", "j. league": "🇯🇵",
    "corea": "🇰🇷", "korea": "🇰🇷", "k league": "🇰🇷",
    "china": "🇨🇳", "china super league": "🇨🇳",
    "estados unidos": "🇺🇸", "usa": "🇺🇸", "mls": "🇺🇸",
    "mexico": "🇲🇽", "méxico": "🇲🇽", "liga mx": "🇲🇽",
    "argentina": "🇦🇷", "argentine": "🇦🇷", "liga profesional": "🇦🇷",
    "brasil": "🇧🇷", "brazil": "🇧🇷", "serie a brasil": "🇧🇷",
    "chile": "🇨🇱", "chile primera division": "🇨🇱",
    "peru": "🇵🇪", "perú": "🇵🇪", "liga 1 peru": "🇵🇪",
    "colombia": "🇨🇴", "colombia primera a": "🇨🇴",
    "uruguay": "🇺🇾", "uruguay primera division": "🇺🇾",
    "paraguay": "🇵🇾", "paraguay primera division": "🇵🇾",
    "ecuador": "🇪🇨", "ecuador serie a": "🇪🇨",
    "champions league": "⚽️", "uefa champions league": "⚽️",
    "europa league": "⚽️", "uefa europa league": "⚽️",
    "conference league": "⚽️", "uefa conference league": "⚽️",
    "mundial": "⚽️", "world cup": "⚽️",
    "club world cup": "⚽️", "fifa club world cup": "⚽️",
    "international": "⚽️",
}

def bandera_para_liga(nombre_liga):
    liga = nombre_liga.lower()
    for clave, bandera in banderas.items():
        if clave in liga:
            return bandera
    return "⚽️"

def limpiar_todos_picks(picks_raw: str):
    picks = []
    for l in picks_raw.split("\n"):
        l = l.strip()
        if not l:
            continue
        if "bloque" in l.lower():
            continue
        if l in ("---", "- ---", "-", "—") or l.strip("-–— ") == "":
            continue
        if not (re.match(r"^[-–—•]\s*", l) or re.search(r"\|\s*\d{2,3}%\b", l)):
            continue
        l = re.sub(r"^[-–—•\s]+", "", l)
        picks.append(l)
    return picks

def limpiar_justificacion(just):
    just_limpio = []
    for l in just.splitlines():
        txt = l.strip()
        if not txt:
            continue
        if txt.lower().startswith("justificación:"):
            txt = txt[len("justificación:"):].strip()
        if txt.strip("-–— ") == "":
            continue
        just_limpio.append(txt)
    return " ".join(just_limpio).strip()

def extraer_picks_y_justificacion(texto):
    partes = re.split(r"JUSTIFICACIÓN", texto, maxsplit=1, flags=re.IGNORECASE)
    if len(partes) == 2:
        return partes[0].strip(), partes[1].strip()
    else:
        return texto.strip(), ""

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    r = requests.post(url, data=payload)
    print("Respuesta Telegram:", r.text)
    return r.ok

def parse_hora(hora_str):
    m = re.search(r"(\d{1,2}):(\d{2})", hora_str or "")
    if not m:
        return (99, 99)
    return int(m.group(1)), int(m.group(2))

# --- Carga ---
hoy = datetime.date.today().strftime('%d-%m-%Y')
input_folder = f"inputs_gpt_completo/{datetime.date.today().strftime('%Y-%m-%d')}/"
output_folder = f"respuestas_gpt/{datetime.date.today().strftime('%Y-%m-%d')}/"

if not os.path.isdir(output_folder):
    print(f"❌ La carpeta {output_folder} no existe.")
    sys.exit(1)

partidos_por_liga = {}
for filename in os.listdir(input_folder):
    if not filename.endswith(".txt"):
        continue
    ruta_input = os.path.join(input_folder, filename)
    ruta_output = os.path.join(output_folder, filename.replace(".txt", "_output.txt"))
    if not os.path.exists(ruta_output):
        continue
    liga, partido, hora = "", "", ""
    with open(ruta_input, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Competición:"):
                liga = line.replace("Competición:", "").strip()
            elif line.startswith("Partido:"):
                partido = line.replace("Partido:", "").strip()
            elif line.startswith("Hora:"):
                hora = line.replace("Hora:", "").strip()
    if not liga:
        liga = "Otras competiciones"
    with open(ruta_output, "r", encoding="utf-8") as f:
        picks_raw = f.read().strip()
        if "NO HAY APUESTA RECOMENDADA" in picks_raw.upper() or "PARTIDO DESCARTADO" in picks_raw.upper():
            continue
    picks_block, justificacion = extraer_picks_y_justificacion(picks_raw)
    picks_lines = limpiar_todos_picks(picks_block)
    if not partido or not picks_lines:
        continue
    partidos_por_liga.setdefault(liga, []).append({
        "liga": liga,
        "partido": partido,
        "hora": hora,
        "picks_lines": picks_lines,
        "justificacion": justificacion
    })

# --- Mensaje ---
separador = "—————————————————"
titulo = f"*PICKS {hoy}*"
mensaje_final = f"{titulo}\n{separador}\n"

if MODO_ORDEN == "liga":
    primer_liga = True
    for liga, lista in partidos_por_liga.items():
        # Ordena partidos por hora dentro de cada liga
        lista.sort(key=lambda x: parse_hora(x["hora"]))
        if not primer_liga:
            mensaje_final += f"\n{separador}\n"
        bandera = bandera_para_liga(liga)
        liga_limpia = re.sub(r"\s*\(\d+\)\s*", " ", liga).strip()
        mensaje_final += f"*{bandera} {liga_limpia.upper()} ({len(lista)})*\n\n"
        primer_liga = False
        for idx, p in enumerate(lista):
            mensaje_final += f"*{p['partido']}* ({p['hora']})\n"
            for linea in p["picks_lines"]:
                mensaje_final += f"- {linea}\n"
            if p["justificacion"]:
                just = limpiar_justificacion(p["justificacion"])
                if just:
                    # 🔻 SIN "Justificación:"
                    mensaje_final += f"\n{just}"
            if idx != len(lista) - 1:
                mensaje_final += "\n\n"
else:
    todos = []
    for liga, lista in partidos_por_liga.items():
        bandera = bandera_para_liga(liga)
        liga_limpia = re.sub(r"\s*\(\d+\)\s*", " ", liga).strip()
        for p in lista:
            hh, mm = parse_hora(p["hora"])
            todos.append({
                "hh": hh, "mm": mm,
                "hora": p["hora"],
                "liga": liga_limpia,
                "bandera": bandera,
                "partido": p["partido"],
                "picks_lines": p["picks_lines"],
                "justificacion": p["justificacion"]
            })
    todos.sort(key=lambda x: (x["hh"], x["mm"], x["partido"].lower()))
    for i, p in enumerate(todos):
        mensaje_final += f"{p['hora']} — *{p['partido']}* ({p['bandera']} {p['liga']})\n"
        for linea in p["picks_lines"]:
            mensaje_final += f"- {linea}\n"
        if p["justificacion"]:
            just = limpiar_justificacion(p["justificacion"])
            if just:
                # 🔻 SIN "Justificación:"
                mensaje_final += f"\n{just}"
        if i != len(todos) - 1:
            mensaje_final += "\n\n"

# --- Envío ---
max_len = 4000
if len(mensaje_final) <= max_len:
    enviar_telegram(mensaje_final)
else:
    bloque = ""
    for linea in mensaje_final.splitlines(keepends=True):
        if len(bloque) + len(linea) > max_len:
            enviar_telegram(bloque.rstrip())
            bloque = ""
        bloque += linea
    if bloque.strip():
        enviar_telegram(bloque.rstrip())

print(f"¡Picks enviados a Telegram en modo: {MODO_ORDEN.upper()}!")