# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import json
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError

PARTIDOS_FILE = "partidos_validos.json"
# Ruta de salida con fecha
hoy = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = f"detalles_partidos_json/{hoy}"

async def obtener_match_id(url: str) -> str:
    """Extrae el matchId de la URL de FotMob."""
    return urlparse(url).path.split("/")[2]

async def scrapear_detalles_partido(page, partido: dict):
    url = partido.get("url")
    match_id = await obtener_match_id(url)
    api_fragment = f"matchDetails?matchId={match_id}"

    # Interceptar y obtener JSON de matchDetails
    try:
        async with page.expect_response(lambda r: api_fragment in r.url, timeout=15000) as resp_info:
            await page.goto(url, timeout=60000)
        response = await resp_info.value
        data = await response.json()
    except TimeoutError:
        print(f"[Error] Timeout obteniendo matchDetails para {url}")
        return
    except Exception as e:
        print(f"[Error] Fallo parsing JSON matchDetails de {url}: {e}")
        return

    # Guardar JSON crudo en la ruta con carpeta por fecha
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    out_file = Path(OUTPUT_DIR) / f"detalles_{match_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Guardado base: {out_file.name}")

async def main():
    # Cargar lista de partidos válidos
    try:
        partidos = json.loads(Path(PARTIDOS_FILE).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Error] No se pudo leer {PARTIDOS_FILE}: {e}")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for partido in partidos:
            await scrapear_detalles_partido(page, partido)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
