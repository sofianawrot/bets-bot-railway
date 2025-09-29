#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def obtener_url_partido(nombre_local, pais, nombre_visitante):
    base_url = "https://www.fotmob.com/match/"
    local_formateado = nombre_local.replace(" ", "-").lower()
    pais_formateado = pais.replace(" ", "-").lower()
    visitante_formateado = nombre_visitante.replace(" ", "-").lower()
    return f"{base_url}{local_formateado}-{pais_formateado}-{visitante_formateado}"

def main():
    try:
        with open("partidos_validos.json", "r", encoding="utf-8") as f:
            partidos = json.load(f)
    except Exception as e:
        print(f"Error al leer partidos_validos.json: {e}")
        return

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)

    for idx, partido in enumerate(partidos):
        local = partido.get("local")
        pais = partido.get("pais")
        visitante = partido.get("visitante")
        hora = partido.get("hora", "No definida")

        url = obtener_url_partido(local, pais, visitante)

        print(f"🔎 Partido {idx+1} -----------------------------")
        print(f"   🏠 Local: {local}")
        print(f"   🚶 Visitante: {visitante}")
        print(f"   ⏰ Hora: {hora}")
        print(f"   🔗 URL generada: {url}")

        try:
            driver.get(url)
            time.sleep(2)
        except Exception as e:
            print(f"Error al abrir la URL {url}: {e}")

    driver.quit()
    print("Proceso completado.")

if __name__ == "__main__":
    main()
