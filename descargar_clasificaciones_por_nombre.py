import json
import asyncio
import sys
import os
import unicodedata
from datetime import datetime
from playwright.async_api import async_playwright

PARTIDOS_VALIDOS_FILE = "partidos_validos.json"

# === Diccionario con variantes y normalización ===
diccionario_ligas = {
    "INT": {
        "champions league": 42, "champions": 42,
        "champions league qualification": 10611,
        "europa league": 73,
        "europa league qualification": 10613,
        "conference league": 10216, "conference": 10216,
        "conference league qualification": 10615,
        "afc challenge league": 9470,
        "afc champions league elite": 525,
        "afc champions league elite qualification": 10622,
        "afc champions league two": 9469,
        "arab club champions cup": 10474, "arab club": 10474,
        "asean championship": 9265,
        "asian cup": 290,
        "asian cup qualification playoff": 10609,
        "concacaf central american cup": 9682,
        "concacaf champions cup": 9682,
        "concacaf gold cup": 298,
        "copa america": 44,
        "eurocopa": 50, "euro": 50,
        "euro qualification": 10607, "clasificacion euro": 10607,
        "fifa arab cup": 10242,
        "fifa club world cup": 78, "mundial de clubes": 78,
        "fifa intercontinental cup": 10703,
        "juegos olimpicos": 66, "olympics": 66,
        "atlantic cup": 9514,
        "uefa nations league": 9806,
        "uefa nations league a": 9806, "uefa nations league b": 9807, "uefa nations league c": 9808, "uefa nations league d": 9809,
        "uefa nations league qualification": 10717,
        "uefa super cup": 74, "supercopa uefa": 74,
        "world cup": 77, "copa del mundo": 77,
        "world cup qualification afc": 10197,
        "world cup qualification conmebol": 10199,
        "world cup qualification uefa": 10195,
        "world cup qualification ofc": 10200,
        "copa del mundo de la uefa": 10195,
        "uefa": 10195,
        "eliminatorias de la copa del mundo de la uefa": 10195
    },
    "GER": {
        "bundesliga": 54,
        "2. bundesliga": 146, "segunda bundesliga": 146, "2 bundesliga": 146,
        "bundesliga qualification": 9081, "bundesliga clasificacion": 9081,
        "2. bundesliga qualification": 9734,
        "super cup": 8924, "supercopa": 8924,
    },
    "USA": {
        "usl championship": 8972,
    },  
    "SAU": {
        "saudi pro league": 536,
        "king's cup": 9942, "kings cup": 9942, "copa del rey": 9942,
        "super cup": 10074, "supercopa": 10074,
    },
    "SUI": {
        "challenge league": 163,
        "super league": 69, "super liga": 69, "superleague": 69,
    },
    "CRO": {
        "hnl": 252, "HNL": 252,
    },
    "AUS": {
        "a-league": 113,
        "australia cup": 9471,
    },
    "BUL": {
        "first professional league": 270, "primer liga profesional": 270, "profesional league": 270,
        "first professional league qualification": 270,
        "super cup": 272, "bulgarian cup": 272,   
    },
    "AUT": {
        "bundesliga": 38,
        "cup": 278, "copa": 278,
    },
    "BEL": {
        "first division a": 40, "divison a": 40, "primera division": 40,
        "cup": 149, "belgian cup": 149, "copa de bélgica": 149,
        "first division qualification": 41,
        "super cup": 266, "supercopa": 266,
    },
    "SVK": {
        "1. liga": 176,
    },
    "QAT": {
        "qatar stars league": 535, "liga de las estrellas": 535,
        "qatar stars league qualification": 9661,
    },
    "CZE": {
        "1. liga": 122, "first league": 122,
        "cup": 254, "czech cup": 254, "copa chequia": 254,
        "fnl": 253,
    },
    "NED": {
        "eredivisie": 57,
        "eerste divisie": 111
    },
    "CHN": {
        "super league": 120,
        "china league one": 9137, "china league": 9137,
        "super cup": 9491,
        "cup": 9550,
    },
    "KOR": {
        "k league 1": 9080, "k league": 9080, "k-league 1": 9080, "k - league 1": 9080, "k league I": 9080,
        "k league qualification": 9422,
        "cup": 9551, "copa": 9551,
    },
    "HRV": {
        "hnl": 252, "1. hnl": 252,
        "croatian cup": 275, "fa cup": 275, "copa de croacia": 275,
        "super cup": 276, "supercopa": 276,
    },
    "DNK": {
        "superligaen": 46,
        "1. division": 85, "primera division": 85,
    },
    "SCO": {
        "premiership": 64,
        "championship": 123,
        "league one": 124,
        "premiership playoff": 181,
        "championship qualification": 9737,
        "league cup": 180,
        "league one qualification": 9738,
        "scottish cup": 137,
    },
    "ESP": {
        "laliga": 87, "la liga": 87,
        "laliga2": 140, "segunda division": 140,
        "copa del rey": 138,
        "super cup": 139, "supercopa": 139,
        "copa de la reina": 10651,
    },
    "FIN": {
        "veikkausliiga": 51,
        "veikkausliiga qualification": 52,
        "finland cup": 342, "copa de finlandia": 342,
        "cup": 143, "suomen cup": 143, "copa": 143,
    },
    "FRA": {
        "ligue 1": 53,
        "ligue 2": 110,
        "national": 8970,
        "coupe de france": 134, "copa de francia": 134,
        "ligue 1 qualification": 9666,
        "ligue 2 qualification": 9667,
        "premiere ligue": 9677,
    },
    "GRC": {
        "super league 1": 135, "superliga": 135,
        "greece cup": 145, "copa de grecia": 145,
    },
    "ENG": {
        "premier league": 47,
        "championship": 48,
        "league one": 108,
        "league two": 109,
        "national league": 117,
        "fa cup": 132, "copa fa": 132,
        "fa cup qualification": 10626,
    },
    "ISL": {
        "besta deildin": 215,
        "1. deild": 216,
        "icelandic cup": 217, "cup": 217, "copa islandia": 217,
        "super cup": 10009,
        "league cup": 10076,
    },
    "ITA": {
        "serie a": 55,
        "coppa italia": 141, "copa italiana": 141, "italian cup": 141, "copa de italia": 141,
        "super cup": 222, "supercopa": 222,
    },
    "JPN": {
        "j. league": 223,
        "j. league cup": 224, "league cup": 224,
        "super cup": 440,
        "j. league 2": 8974,
        "cup": 9011, "copa": 9011,
    },
    "LUX": {
        "national division": 229,
        "coupe de luxembourg": 9527, "cup": 9527,
        "national division qualification": 9174,
    },
    "NOR": {
        "eliteserien": 59,
        "eliteserien qualification": 60,
        "1. divisjon": 203, "1. division": 203,
    },
    "NZL": {
        "championship": 8870,
    },
    "NLD": {
        "eredivisie": 57,
        "eerste divisie": 111,
        "eredivisie qualification": 58,
        "super cup": 237, "supercopa": 237,
    },
    "POL": {
        "ekstraklasa": 196,
        "1. liga": 197, "i liga": 197,
        "2. division": 8935, "ii liga": 8935,
    },
    "POR": {
        "liga portugal": 61,
        "liga portugal 2": 185,
        "league cup": 187, "copa de la liga": 187,
        "liga portugal 2 qualification": 9668,
        "liga portugal qualification": 10215,
        "super cup": 188, "supercopa": 188,
        "taca de portugal": 186, "taça de portugal": 186,
    },
    "ROU": {
        "cupa româniei": 190, "cup": 190,
        "super cup": 192, "supercupa": 192,
        "superliga qualification": 9587, 
        "superliga": 189,
        "liga ii": 9113,
    },
    "SGP": {
        "premier league": 9587, "singapore premier league": 9587,
        "singapore cup": 9143, "cup": 9143,
    },
    "SWE": {
        "allsvenskan": 67,
        "allsvenskan qualification": 67,
        "ettan": 168,
        "svenska cupen": 171, "cup": 171, "svenska cup": 171,
    },
    "CHE": {
        "super league": 69,
        "super league qualification": 70,
        "swiss cup": 164, "cup": 164,
    },
    "DEN": {
        "superligaen": 46, "superliga": 46,
        "1. division": 85, "first division": 85,
        "2. division": 239, "segunda division": 239,
    },
    "FRO": {
        "premier league": 250,
    },
    "SVN": {
        "prva liga": 173, "prva liga clasificación": 173,
        "slovenia cup": 174,
    },
    "TUR": {
        "super lig": 71, "superlig": 71, "superliga": 71,
        "1. lig": 165, "1 lig": 165,
        "super cup": 166, "supercopa": 166,
        "turkish cup": 151, "copa de turquía": 151,
    },
}

palabras_ignorar = [
    "grupo", "group", "fase de grupos", "fase grupo", "semifinal", "cuartos", "final", "playoff",
    "championship group", "qualification", "clasificación", "championship round",
    "group stage", "ronda", "play-off", "repechaje"
]

def normalizar_texto(txt):
    txt = unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore').decode('utf-8').lower()
    for word in palabras_ignorar:
        txt = txt.replace(word, "")
    return " ".join(txt.split()).strip()

def obtener_ligas_de_partidos_validos():
    if not os.path.exists(PARTIDOS_VALIDOS_FILE):
        print(f"❌ No existe {PARTIDOS_VALIDOS_FILE}")
        sys.exit(1)
    with open(PARTIDOS_VALIDOS_FILE, "r", encoding="utf-8") as f:
        partidos = json.load(f)
    ligas = {}
    for partido in partidos:
        liga = partido.get("liga", "")
        pais = partido.get("pais", "")
        if liga and pais:
            clave = (pais, liga)
            ligas[clave] = True
    return list(ligas.keys())

async def descargar_clasificacion(league_id, output_filename):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"https://www.fotmob.com/leagues/{league_id}/table"
        await page.goto(url, timeout=60000)  # Cambiado aquí, 60s de timeout
        print(f"[*] Navegando a {url}")
        try:
            await page.locator(".fc-cta-consent").click(timeout=4000)
            print("✔️ Cookies aceptadas (.fc-cta-consent).")
        except Exception:
            pass
        try:
            response = await page.wait_for_event(
                "response",
                lambda r: "tltable" in r.url and r.status == 200,
                timeout=30000,
            )
            data = await response.json()
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[+] Clasificación guardada en {output_filename}")
        except Exception as e:
            print(f"[!] No se pudo guardar la clasificación de la liga {league_id} → {e}")
        await browser.close()

async def main():
    ligas = obtener_ligas_de_partidos_validos()
    hoy = datetime.now().strftime("%Y-%m-%d")
    out_dir = f"clasificaciones/{hoy}"
    os.makedirs(out_dir, exist_ok=True)
    procesadas = set()
    print(f"\nSe han detectado {len(ligas)} ligas en {PARTIDOS_VALIDOS_FILE}.\n")
    for (pais, liga) in ligas:
        print(f"Procesando liga: {liga} ({pais})")
        liga_normalizada = normalizar_texto(liga)
        country_ligas = diccionario_ligas.get(pais, {})
        league_id = None
        # PRIMERO coincidencia EXACTA
        for nombre_base, id_fotmob in country_ligas.items():
            if liga_normalizada == nombre_base:
                league_id = id_fotmob
                break
        # Si no, coincidencia parcial (fallback)
        if league_id is None:
            for nombre_base, id_fotmob in country_ligas.items():
                if nombre_base in liga_normalizada:
                    league_id = id_fotmob
                    break
        if not league_id:
            print(f"❌ No tengo el ID para '{liga}' ({pais}). Añádelo en el diccionario para cubrir esta variante.")
            continue
        if league_id in procesadas:
            print(f"⏭️ Clasificación de la liga {league_id} ya guardada en esta ejecución (grupos dentro de la misma liga).")
            continue
        output_filename = os.path.join(out_dir, f"clasificacion_{league_id}.json")
        await descargar_clasificacion(league_id, output_filename)
        procesadas.add(league_id)
    print("\n✅ Todo completado con éxito. ¡A analizar se ha dicho!")

if __name__ == "__main__":
    asyncio.run(main())
