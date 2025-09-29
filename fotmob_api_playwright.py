import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def run():
    # --- Usar fecha de Madrid, no UTC ---
    hoy = datetime.now().strftime("%Y-%m-%d")
    url_api = None
    data_partidos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def intercept_response(response):
            nonlocal url_api, data_partidos
            # NUEVO ENDPOINT: api/data/matches?
            if "/api/data/matches?" in response.url and response.status == 200:
                try:
                    json_data = response.json()
                    data_partidos = json_data
                    url_api = response.url
                except Exception as e:
                    print(f"Error leyendo JSON: {e}")

        page.on("response", intercept_response)

        print("🌐 Accediendo a FotMob...")
        page.goto("https://www.fotmob.com/?show=all", timeout=60000)
        page.wait_for_timeout(8000)  # Deja 7-8 seg para asegurar carga

        browser.close()

    if not data_partidos:
        print("❌ No se capturó la respuesta de /api/data/matches")
        return

    partidos = []
    for liga in data_partidos.get("leagues", []):
        liga_nombre = liga.get("name", "")
        pais = liga.get("ccode", "")
        for match in liga.get("matches", []):
            local = match.get("home", {}).get("name")
            visitante = match.get("away", {}).get("name")
            timestamp = match.get("status", {}).get("utcTime")
            hora = None
            if timestamp:
                try:
                    hora = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    hora = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                hora = (hora + timedelta(hours=2)).strftime("%H:%M")

            partidos.append({
                "hora": hora or "por_definir",
                "local": local,
                "visitante": visitante,
                "pais": pais,
                "liga": liga_nombre,
                "url": f"https://www.fotmob.com/match/{match.get('id')}"
            })

    with open("partidos_hoy.json", "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

    print(f"✅ Se guardaron {len(partidos)} partidos en partidos_hoy.json")

if __name__ == "__main__":
    run()
