import sys
import os

# Forzar output a stderr para que Railway lo muestre
sys.stdout = sys.stderr

# Capturar cualquier error de importación
try:
    print("=== INICIANDO BOT ===")
    print("Importando subprocess...")
    import subprocess
    print("Importando schedule...")
    import schedule
    print("Importando time...")
    import time
    print("Importando json...")
    import json
    print("Importando datetime...")
    from datetime import datetime, timedelta
    print("=== TODAS LAS IMPORTACIONES EXITOSAS ===")
except Exception as e:
    print(f"ERROR EN IMPORTACIONES: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def programar_partidos_del_dia():
    """Lee los partidos del día y programa envíos individuales"""
    if not os.path.exists("partidos_hoy.json"):
        print("⚠️ No hay partidos para programar")
        return
    
    with open("partidos_hoy.json", "r", encoding="utf-8") as f:
        partidos = json.load(f)
    
    # Limpiar tareas programadas del día anterior
    schedule.clear('partidos')
    
    for partido in partidos:
        hora = partido.get("hora", "")
        if hora and hora != "por_definir":
            # Programar envío individual a esa hora
            schedule.every().day.at(hora).do(
                enviar_partido_individual, 
                partido=partido
            ).tag('partidos')
            print(f"⏰ Programado: {partido['local']} vs {partido['visitante']} a las {hora}")

def proceso_completo_diario():
    """Ejecuta el flujo completo una vez al día"""
    print("\n🚀 INICIANDO PROCESO DIARIO")
    print("=" * 50)
    
    try:
        print("🔄 1. Scraping de partidos...")
        subprocess.run(["python", "fotmob_api_playwright.py"], check=True)
        
        print("🔄 2. Filtrando partidos...")
        subprocess.run(["python", "filtrar_partidos_local_v17.py"], check=True)
        
        print("🔄 3. Scrapeando detalles...")
        subprocess.run(["python", "scrapear_datos_partido.py"], check=True)
        
        print("🔄 4. Descargando clasificaciones...")
        subprocess.run(["python", "descargar_clasificaciones_por_nombre.py"], check=True)
        
        print("🔄 5. Extrayendo clasificaciones...")
        subprocess.run(["python", "extraer_clasificaciones_por_partido.py"], check=True)
        
        print("🔄 6. Unificando datos...")
        subprocess.run(["python", "unificar_detalles_y_clasificacion.py"], check=True)
        
        print("🔄 7. Analizando partidos...")
        subprocess.run(["python", "analizar_partido.py"], check=True)
        
        print("🔄 8. Enviando a Telegram...")
        subprocess.run(["python", "enviar_a_telegram.py", "hora"], check=True)
        
        print("\n✅ Proceso diario completado")
    except Exception as e:
        print(f"❌ Error en proceso diario: {e}")

print("Programando tarea...")
schedule.every().day.at("10:30").do(proceso_completo_diario)
print("Tarea programada para las 10:05")

print("\n🤖 Bot iniciado - Esperando tareas programadas...")
while True:
    schedule.run_pending()
    time.sleep(60)