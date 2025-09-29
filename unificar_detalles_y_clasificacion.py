# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# --- CONFIGURACIÓN ---
today = datetime.now(ZoneInfo('Europe/Madrid')).date()
today_str = today.isoformat()
DETALLES_DIR = f"detalles_partidos_json/{today_str}"
CLASIF_DIR = f"clasificaciones/{today_str}"
OUTPUT_DIR = os.path.join('inputs_gpt_completo', today_str)
os.makedirs(OUTPUT_DIR, exist_ok=True)

NOMBRES_COPAS = {
    9550: "Copa de China",
    # Añade aquí otras copas si quieres personalizar el nombre
}

# --- FUNCIÓN DE MOTIVACIÓN MEJORADA ---
def detectar_motivacion(equipo_nombre, clasificacion, leyenda, total_jornadas=34):
    if not clasificacion or not isinstance(clasificacion, list):
        return f"{equipo_nombre}: no encontrado en la clasificación."
    def get_pos(t):
        if t.get("position") is not None:
            return t.get("position")
        elif t.get("idx") is not None:
            return t.get("idx") + 1
        else:
            return 999
    tabla_ordenada = sorted(
        [t for t in clasificacion if isinstance(t, dict) and t.get("name")],
        key=get_pos
    )
    equipo = next((e for e in tabla_ordenada if e.get("name") == equipo_nombre), None)
    if not equipo:
        return f"{equipo_nombre}: no encontrado en la clasificación."
    pos = equipo.get("position")
    if pos is None:
        pos = (equipo.get("idx") + 1) if equipo.get("idx") is not None else (tabla_ordenada.index(equipo) + 1)
    pts = equipo.get("pts") or equipo.get("points")
    played = equipo.get("played", 0)
    zonas = {
        "ascenso": set([p+1 for p in leyenda.get("promotion", [])]),
        "promoción": set([p+1 for p in leyenda.get("promotionqual", [])]),
        "playoff_descenso": set([p+1 for p in leyenda.get("relegationqual", [])]),
        "descenso": set([p+1 for p in leyenda.get("relegation", [])])
    }
    texto_zona = "zona media"
    tipo = ""
    if pos in zonas["ascenso"]:
        texto_zona = "zona de ascenso directo"
        tipo = "ascenso"
    elif pos in zonas["promoción"]:
        texto_zona = "zona de promoción"
        tipo = "promoción"
    elif pos in zonas["playoff_descenso"]:
        texto_zona = "zona de playoff de descenso"
        tipo = "playoff_descenso"
    elif pos in zonas["descenso"]:
        texto_zona = "zona de descenso"
        tipo = "descenso"
    diferencia = ""
    motiv_extra = ""
    def puntos_zona(target_zonas, mayor=True):
        candidatos = [t for t in tabla_ordenada if (t.get("position") or (t.get("idx") + 1 if t.get("idx") is not None else tabla_ordenada.index(t)+1)) in target_zonas]
        if not candidatos:
            return None, None
        if mayor:
            candidato = min(candidatos, key=get_pos)
        else:
            candidato = max(candidatos, key=get_pos)
        return candidato, candidato.get("pts") or candidato.get("points")
    if tipo == "descenso":
        fuera_descenso = set(range(1, len(tabla_ordenada)+1)) - zonas["descenso"] - zonas["playoff_descenso"]
        if fuera_descenso:
            rival, pts_rival = puntos_zona(fuera_descenso)
            if rival and pts_rival is not None and pts is not None:
                diferencia = f"A {abs(pts_rival - pts)} pts de la salvación."
    elif tipo == "playoff_descenso":
        fuera_playoff = set(range(1, len(tabla_ordenada)+1)) - zonas["descenso"] - zonas["playoff_descenso"]
        if fuera_playoff:
            rival, pts_rival = puntos_zona(fuera_playoff)
            if rival and pts_rival is not None and pts is not None:
                diferencia = f"A {abs(pts_rival - pts)} pts de la salvación."
    elif tipo in ["ascenso", "promoción"]:
        fuera_ascenso = set(range(1, len(tabla_ordenada)+1)) - zonas["ascenso"] - zonas["promoción"]
        if fuera_ascenso:
            rival, pts_rival = puntos_zona(fuera_ascenso, mayor=False)
            if rival and pts_rival is not None and pts is not None:
                diferencia = f"A {abs(pts - pts_rival)} pts de perder la plaza de {texto_zona.split()[-1]}."
    else:
        for key, nombre in [("promotion", "promoción"), ("promotionqual", "playoff de promoción"),
                            ("relegationqual", "playoff de descenso"), ("relegation", "descenso")]:
            for ref in leyenda.get(key, []):
                if abs(pos - (ref+1)) <= 2:
                    texto_zona = f"zona media, cerca de {nombre}"
                    break
    jornadas_restantes = total_jornadas - played if total_jornadas else ""
    if jornadas_restantes and jornadas_restantes <= 5:
        motiv_extra = " (tramo final de liga, motivación extra)"
    return f"{equipo_nombre} está en {texto_zona} ({pos}º con {pts} pts). {diferencia}{motiv_extra}".strip()

# --- Función para formatear el archivo combinado ---
def unir_info(cabecera, ultimos, h2h, lesionados, alineaciones, clasificacion, motivacion, insights):
    lines = []
    if cabecera:
        lines.append(f"PARTIDO\n{cabecera.strip()}\n")
    if ultimos:
        lines.append(f"ÚLTIMOS 5 PARTIDOS\n{ultimos.strip()}\n")
    if h2h:
        lines.append(f"ENFRENTAMIENTOS DIRECTOS\n{h2h.strip()}\n")
    if lesionados:
        lines.append(f"LESIONADOS/SUSPENDIDOS\n{lesionados.strip()}\n")
    if alineaciones:
        lines.append(f"ALINEACIONES\n{alineaciones.strip()}\n")
    if clasificacion:
        lines.append(f"CLASIFICACIÓN\n{clasificacion.strip()}\n")
    if motivacion:
        lines.append(f"MOTIVACIÓN\n{motivacion.strip()}\n")
    if insights:
        lines.append(f"INSIGHTS DE APUESTAS\n{insights.strip()}\n")
    return "\n".join(lines)

# --- Buscar y combinar la información ---
for filename in os.listdir(DETALLES_DIR):
    if not filename.endswith('.json'):
        continue

    # --- Leer detalles del partido ---
    detalles_path = os.path.join(DETALLES_DIR, filename)
    try:
        with open(detalles_path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] leyendo detalles: {filename}: {e}")
        continue

    gen = data.get('general', {}) or {}
    home = gen.get('homeTeam', {}).get('name', 'Local')
    away = gen.get('awayTeam', {}).get('name', 'Visitante')
    hora = gen.get('matchTimeUTCDate') or gen.get('matchTimeUTC') or ''
    try:
        dt = datetime.fromisoformat(hora.replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Madrid'))
        hora_str = dt.strftime('%H:%M')
    except Exception:
        hora_str = hora

    # --- Construcción del nombre de la competición completo ---
    league_id = gen.get('leagueId') or gen.get('parentLeagueId')
    league_name = gen.get('leagueName', '') or gen.get('parentLeagueName', '') or 'no disponible'
    country = gen.get('countryCode', 'INT')

    if league_id and isinstance(league_id, int) and league_id in NOMBRES_COPAS:
        competicion = NOMBRES_COPAS[league_id]
    elif league_name.lower() in ['cup', 'playoff', 'play-offs', 'round', 'final']:
        competicion = f"{league_name} ({country})"
    else:
        competicion = league_name

    round_name = gen.get('roundName')
    if not round_name:
        info_box = (data.get('content', {})
                    .get('matchFacts', {})
                    .get('infoBox', {}))
        tournament = info_box.get('Tournament') if isinstance(info_box, dict) else {}
        round_name = tournament.get('roundName') if isinstance(tournament, dict) else None
    if round_name:
        competicion = f"{competicion} ({round_name})"

    partido_cabecera = (
        f"Fecha: {today_str}\n"
        f"Hora: {hora_str}\n"
        f"Partido: {home} vs {away}\n"
        f"Estadio: {gen.get('venue','')}\n"
        f"Árbitro: {gen.get('referee','no disponible')}\n"
        f"Competición: {competicion}"
    )

    # --- Últimos 5 partidos ---
    content = data.get('content', {})
    ult = []
    team_form = content.get('matchFacts', {}).get('teamForm') or []
    for idx, team_name in enumerate([home, away]):
        ult.append(f"{team_name}:")
        if len(team_form) > idx and team_form[idx]:
            for m in team_form[idx]:
                tip = m.get('tooltipText', {}) or {}
                d_raw = tip.get('utcTime') or m.get('date', {}).get('utcTime')
                try:
                    d = datetime.fromisoformat(d_raw.replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Madrid'))
                    date_fmt = d.date().isoformat()
                except Exception:
                    date_fmt = d_raw or ''
                h = tip.get('homeTeam') or m.get('home', {}).get('name', '')
                a = tip.get('awayTeam') or m.get('away', {}).get('name', '')
                score = f"{tip.get('homeScore', '')} - {tip.get('awayScore', '')}".strip()
                ult.append(f"- {date_fmt}: {h} {score} {a}")
        else:
            ult.append("no disponible")
        ult.append('')
    ultimos_partidos = "\n".join(ult)

    # --- Enfrentamientos directos ---
    h2h_lines = []
    h2h_obj = content.get('h2h', {})
    h2h = h2h_obj.get('matches') if isinstance(h2h_obj, dict) else []

    fecha_limite = datetime(2024, 1, 1, tzinfo=ZoneInfo('Europe/Madrid'))
    hoy = datetime.now(ZoneInfo('Europe/Madrid'))

    proximo_partido = None
    for m in h2h or []:
        raw = m.get('time', {}).get('utcTime')
        try:
            dt_h2h = datetime.fromisoformat(raw.replace('Z','+00:00')).astimezone(ZoneInfo('Europe/Madrid'))
            date_str = dt_h2h.date().isoformat()
        except Exception:
            date_str = raw or ''
            dt_h2h = None

        h = m.get('home',{}).get('name','')
        a = m.get('away',{}).get('name','')
        sc = m.get('status',{}).get('scoreStr','')
        league = m.get('league')
        if league and isinstance(league, dict):
            league_name_h2h = league.get('name', 'comp. desconocida')
        else:
            league_name_h2h = "comp. desconocida"

        if dt_h2h:
            if dt_h2h < fecha_limite:
                continue
            elif dt_h2h.date() > hoy.date():
                if not proximo_partido:
                    proximo_partido = f"Próximo partido: {date_str} ({league_name_h2h})"
                continue
            else:
                h2h_lines.append(f"- {date_str}: {h} {sc} {a} ({league_name_h2h})")

    if proximo_partido:
        h2h_lines.append(proximo_partido)
    if not h2h_lines:
        h2h_lines.append('no disponible')
    h2h_txt = "\n".join(h2h_lines)

    # --- Lesionados/suspendidos ---
    lineup = content.get('lineup', {}) or {}
    unavailable = []
    for team in ['homeTeam', 'awayTeam']:
        arr = lineup.get(team, {}).get('unavailable', []) or []
        for p in arr:
            name = p.get('name', '')
            u = p.get('unavailability', {}) or {}
            unavailable.append(f"- {name} ({u.get('type','')}: {u.get('expectedReturn','')})")
    lesionados_txt = "\n".join(unavailable) if unavailable else "no disponible"

    # --- Alineaciones ---
    alineas = []
    for side, name in [('homeTeam', home), ('awayTeam', away)]:
        d = lineup.get(side) or {}
        form = d.get('formation', '')
        stars = d.get('starters') or []
        names = [p.get('name', '') for p in stars if isinstance(p, dict)]
        alineas.append(f"{name} ({form}): {', '.join(names) if names else 'no disponible'}")
    alineaciones_txt = "\n".join(alineas) if alineas else "no disponible"

    # --- Buscar clasificación asociada y leyenda para motivación ---
    league_id_clasif = gen.get('parentLeagueId')
    clasif_txt = None
    motivacion_txt = None
    lines = []
    home_stats = away_stats = None
    table_all = []
    legend_dict = {}
    total_jornadas = 34

    if league_id_clasif:
        clasif_path = os.path.join(CLASIF_DIR, f"clasificacion_{league_id_clasif}.json")
        if os.path.exists(clasif_path):
            try:
                with open(clasif_path, encoding='utf-8') as f:
                    clasif_data = json.load(f)
            except Exception:
                clasif_data = None
            tablas, tabla_general = [], None
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
            table_all = []
            for grupo in tablas:
                table_all.extend(grupo.get('table', {}).get('all', []))
            if tabla_general:
                table_all.extend(tabla_general.get('all', []))
            legend_list = []
            if isinstance(clasif_data, dict) and 'data' in clasif_data:
                legend_list = clasif_data['data'].get('legend', [])
            if legend_list:
                for item in legend_list:
                    legend_dict[item.get('tKey')] = item.get('indices', [])
            def get_team_stats(eq_name):
                for t in table_all:
                    if t.get('name', '') == eq_name:
                        return t
                return {}
            home_stats = get_team_stats(home)
            away_stats = get_team_stats(away)
            def stat_line(eq, d):
                pos = d.get('idx', 'no disp.')
                J = d.get('played', 'no disp.')
                G = d.get('wins', 'no disp.')
                E = d.get('draws', 'no disp.')
                P = d.get('losses', 'no disp.')
                DG = (
                    d.get('gd')
                    or d.get('goalConDiff')
                    or d.get('goalDifference')
                    or d.get('dif')
                    or d.get('difference')
                    or d.get('goal_diff')
                    or "no disp."
                )
                PTS = d.get('pts', 'no disp.')
                return f"{eq}: {pos}º | J: {J} | G: {G} | E: {E} | P: {P} | DG: {DG} | PTS: {PTS}"
            if home_stats: lines.append(stat_line(home, home_stats))
            if away_stats: lines.append(stat_line(away, away_stats))
            if not lines:
                lines.append("no disponible")
            clasif_txt = "\n".join(lines)
            # --- MOTIVACIÓN MEJORADA ---
            if table_all and legend_dict:
                if "rounds" in clasif_data.get("data", {}):
                    total_jornadas = clasif_data["data"]["rounds"]
            mot_home = detectar_motivacion(home, table_all, legend_dict, total_jornadas)
            mot_away = detectar_motivacion(away, table_all, legend_dict, total_jornadas)
            motivacion_txt = f"{mot_home}\n{mot_away}"
        else:
            clasif_txt = "Copa sin clasificación"
    else:
        clasif_txt = "no disponible"

    # --- INSIGHTS DE APUESTAS (al final del archivo) ---
    insights_lines = []
    insights = content.get('insights', [])
    if isinstance(insights, list) and insights:
        for ins in insights:
            txt = ins.get('text')
            if txt:
                insights_lines.append(f"- {txt}")
    poll = content.get('poll', {}).get('options', [])
    if poll:
        for p in poll:
            txt = p.get('text')
            prob = p.get('probability')
            if txt and prob is not None:
                insights_lines.append(f"- Probabilidad de {txt}: {round(prob*100)}%")
    oddspoll = content.get('matchFacts', {}).get('poll', {}).get('oddspoll', {}).get('Facts', [])
    if oddspoll:
        for fact in oddspoll:
            default_text = fact.get('defaultText')
            if default_text:
                insights_lines.append(f"- {default_text}")
    insights_txt = "\n".join(insights_lines) if insights_lines else None

    # --- Generar archivo de salida ---
    safe = lambda s: s.replace(' ', '_').replace(':','')
    mid = gen.get('matchId',filename.replace('.json','')) if gen else filename.replace('.json','')
    fname = f"{mid}_{safe(home)}_vs_{safe(away)}_{hora_str}.txt"
    outpath = os.path.join(OUTPUT_DIR, fname)
    contenido = unir_info(
        partido_cabecera,
        ultimos_partidos,
        h2h_txt,
        lesionados_txt,
        alineaciones_txt,
        clasif_txt,
        motivacion_txt,
        insights_txt
    )
    try:
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"Generado: {outpath}")
    except Exception as e:
        print(f"[ERROR] escribiendo {outpath}: {e}")
