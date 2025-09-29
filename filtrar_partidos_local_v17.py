#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# 1) Mapea cada código de país (FotMob) a tus ligas favoritas (nombres exactos en FotMob)
favoritas_por_pais = {
    "INT": [
        "Champions League",
        "Europa League",
        "AFC Challenge League Elite",
        "AFC Champions League Two",
        "ASEAN Championship",
        "ASEAN",
        "Asian Cup",
        "Champions League Clasificación",
        "Conference League",
        "Conference League Clasificación",
        "Eurocopa",
        "Europa League Clasificación",
        "UEFA Super Cup",
        "Copa del Mundo",
        "Copa Mundial de Clubes de la FIFA",
        "FIFA Club World Cup"
        "Copa del Mundo",
        "Copa del Mundo de la UEFA",
        "Eliminatorias de la Copa del Mundo de la UEFA",
    ],
    "GER": ["Bundesliga", "2. Bundesliga", "Super Cup"],
    "USA": ["USL Championship"],
    "AUS": ["A-League"],
    "AUT": ["Bundesliga", "Cup", "Copa"],
    "BUL": ["First Professional League", "Bulgarian Cup", "First professional league Qualification", "Super Cup"],
    "BEL": ["First Division A", "First Division A Clasificación", "Belgian Cup", "Super Cup", "Primera Division", "Division A"],
    "CZE": ["1. Liga", "1. Liga qualification", "Czech Cup", "FNL"],
    "CHN": ["Super League", "China League One", "Super Cup", "Cup", "China League"],
    "ITA": ["Serie A", "Coppa Italia", "Copa de Italia", "Italian Cup", "Supercoppa", "Supercopa", "Super Cup"],
    "KOR": [
        "K League 1",  # existente
        "K-League 1",  # añadido para variación con guion
        "K League Qualification",
        "Cup"
        "K-League I"
        "K League I"
    ],
    "CRO": ["HNL", "Croatian Cup", "Super Cup"],
    "DEN": ["Superligaen", "1. Division", "2. Division"],
    "FRO": ["Premier League", "Primera Liga"],
    "ENG": ["League One", "Premier League", "Championship"],
    "UAE": ["Cup"],
    "SCO": ["Premiership", "Championship", "League One", "Scottish Cup"],
    "SVK": ["1. Liga"],
    "SVN": ["Prva Liga", "Prva Liga Clasificación", "Slovenia Cup"],
    "ESP": ["LaLiga", "LaLiga2", "Copa del Rey", "Supercopa de España"],
    "FIN": ["Veikkausliiga", "Veikkausliiga Clasificación", "Suomen Cup", "Finland Cup", "Cup", "Copa"],
    "FRA": ["Ligue 1", "Ligue 2", "National", "Premier League", "Coupe de France", "Ligue 1 Clasificación", "Ligue 2 Clasificación"],
    # Japon: incluir todas las fases de su Copa
    "JPN": ["J. League", "Super Cup", "Cup", "Copa", "League Cup"],
    "LUX": ["National División", "National División Clasificación", "Coupe de Luxembourg"],
    "NOR": ["Eliteserien", "Eliteserien Clasificación", "1. Divisjon", "Primera Division", "1. Division"],
    "NED": ["Eredivisie", "Eredivisie Clasificación", "Eerste Divisie", "Super Cup"],
    "POL": ["Ekstraklasa", "1 Liga", "I Liga", "II Liga"],
    "POR": ["Liga Portugal", "Liga Portugal Clasificación", "League Cup", "Super Cup", "Taça de Portugal"],
    "ROU": ["Liga I", "Super Cup", "Superliga", "Liga II"],
    "SGP": ["Singapore Premier League", "Singapore Cup"],
    "SWE": ["Allsvenskan", "Allsvenskan Clasificación", "Superettan", "Superettan Clasificación", "Svenska Cupen", "Svenska Cup", "Cup", "Copa"],
    "SUI": ["Super League", "Super League Clasificación", "Challenge League", "Challenge League Clasificación"],
    "TUR": ["Süper Lig"],
    # Islandia: incluir 1. Deild y todas las fases de su Copa
    "ISL": ["1. Deild", "Cup", "Besta Deildin", "Icelandic Cup", "Copa de Islandia", "Copa", "Super Cup", "Supercup", "Super Copa", "League Cup"],
}

# 2) Países que quieres vetar
paises_vetados = {
    "ALB","ALG","ARG","ARM","AZE","BAN","BLR","BOL","BIH","BRA","CHL",
    "CYP","COL","CRI","ECU","EGY","SLV","GEO","GTM","HND","IND","IDN",
    "IRQ","IRN","FRO","KAZ","KWT","LVA","LTU","MKD","MYS","MAR","MDA",
    "MNE","MEX","NGA","PAN","PRY","PER","RUS","SRB","ZAF","THA","TZA",
    "UKR","URY","VEN","VIE",
}

# 3) Términos que mueven a descartar un partido (incluye 'cosafa' y 'damallsvenskan')
términos_descartados = ["women", "youth", "joven", "sub19", "U19", "kvinner", "woman", "frauen", "femenino", "w", "(w)", "north", "south", "liga f", "(f)", "woman", "u20", "u-20", "sub", "cosafa", "damallsvenskan", "sub20", "sub-20", "sub18", "vrouwen", "sub-18", "sub 18"]

# --- carga de datos ---
with open("partidos_hoy.json", encoding="utf-8") as f:
    partidos = json.load(f)

validos = []
for p in partidos:
    pais = p.get("pais", "")
    liga = p.get("liga", "")
    liga_lc = liga.lower()

    # 1) país no vetado
    if pais in paises_vetados:
        continue

    # 2) no contener términos descartados
    if any(t in liga_lc for t in términos_descartados):
        continue

    # 3) tener mapeo de ligas para ese país
    patrones = favoritas_por_pais.get(pais)
    if not patrones:
        continue

    # 4) buscar coincidencia (exacta o fallback para competiciones 'Cup')
    match = False
    for pat in patrones:
        pl = pat.lower()
        if pl in liga_lc:
            match = True
            break
        # si el patrón es exactamente 'cup', capturamos cualquier fase de copa
        if pl == "cup" and "cup" in liga_lc:
            match = True
            break

    if match:
        validos.append(p)

# guardar
with open("partidos_validos.json", "w", encoding="utf-8") as f:
    json.dump(validos, f, ensure_ascii=False, indent=2)

print(f"🎯 Partidos filtrados válidos: {len(validos)}")
print("💾 Guardados en partidos_validos.json")
