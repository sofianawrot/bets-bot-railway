import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

today = datetime.now(ZoneInfo('Europe/Madrid')).date()
today_str = today.isoformat()
DETALLES_DIR = f"detalles_partidos_json/{today_str}"
CLASIF_DIR = f"clasificaciones/{today_str}"
OUTPUT_DIR = os.path.join('clasificaciones_gpt', today_str)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def buscar_en_tablas(tablas, home, away):
    for grupo in tablas:
        if not isinstance(grupo, dict):
            continue
        tabla = grupo.get('table', {})
        all_teams = tabla.get('all', [])
        if not isinstance(all_teams, list):
            continue
        equipos = {e['name']: e for e in all_teams if 'name' in e}
        if home in equipos and away in equipos:
            return equipos[home], equipos[away], grupo.get('leagueName', '')
    return None, None, None

def buscar_en_tabla_all(table, home, away):
    all_teams = table.get('all', [])
    if not isinstance(all_teams, list):
        return None, None
    equipos = {e['name']: e for e in all_teams if 'name' in e}
    if home in equipos and away in equipos:
        return equipos[home], equipos[away]
    return None, None

def formatea_fila(equipo):
    def get(k, alt="no disponible"):
        return str(equipo[k]) if k in equipo and equipo[k] is not None else alt

    pos = get("idx")
    jugados = get("played")
    ganados = get("wins")
    empatados = get("draws")
    perdidos = get("losses")
    dg = get("goalConDiff")
    puntos = get("pts")
    return f"{equipo.get('name', 'Equipo')}: {pos}º | J: {jugados} | G: {ganados} | E: {empatados} | P: {perdidos} | DG: {dg} | PTS: {puntos}"

def safe(s):
    return s.replace(' ', '_').replace(':', '').replace('/', '-')

for filename in os.listdir(DETALLES_DIR):
    if not filename.endswith('.json'):
        continue
    filepath = os.path.join(DETALLES_DIR, filename)
    try:
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] leyendo {filename}: {e}")
        continue

    gen = data.get('general', {}) or {}
    home = gen.get('homeTeam', {}).get('name', 'Local')
    away = gen.get('awayTeam', {}).get('name', 'Visitante')
    league_id = gen.get('parentLeagueId')
    if not league_id:
        print(f"[ADVERTENCIA] Sin parentLeagueId en {filename}")
        continue

    clasif_path = os.path.join(CLASIF_DIR, f"clasificacion_{league_id}.json")
    if not os.path.exists(clasif_path):
        print(f"[ADVERTENCIA] No existe archivo de clasificación: {clasif_path}")
        continue

    try:
        with open(clasif_path, encoding='utf-8') as f:
            clasif_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] leyendo {clasif_path}: {e}")
        continue

    tablas = []
    tabla_general = None
    if isinstance(clasif_data, list):
        for x in clasif_data:
            if isinstance(x, dict) and 'data' in x:
                d = x['data']
                if 'tables' in d:
                    tablas.extend(d['tables'])
                if 'table' in d:
                    tabla_general = d['table']
    elif isinstance(clasif_data, dict) and 'data' in clasif_data:
        d = clasif_data['data']
        if 'tables' in d:
            tablas = d['tables']
        if 'table' in d:
            tabla_general = d['table']

    home_team, away_team, group_name = buscar_en_tablas(tablas, home, away) if tablas else (None, None, None)
    if not (home_team and away_team) and tabla_general:
        home_team, away_team = buscar_en_tabla_all(tabla_general, home, away)
        group_name = None

    mid = gen.get('matchId', filename.replace('.json', '')) if gen else filename.replace('.json', '')
    fname = f"{mid}_{safe(home)}_vs_{safe(away)}.txt"
    outpath = os.path.join(OUTPUT_DIR, fname)

    if home_team and away_team:
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(formatea_fila(home_team) + "\n" + formatea_fila(away_team) + "\n")
        print(f"Generado: {outpath}")
    else:
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write("No hay tabla de clasificación\n")
        print(f"[INFO] No se encontró grupo común o tabla principal para {home} vs {away} en {clasif_path}")
