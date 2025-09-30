import sys
import os
import subprocess
import schedule
import time
import json
from datetime import datetime, timedelta

# Forzar output a stderr para que Railway lo muestre
sys.stdout = sys.stderr

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

# Programar proceso completo diario a las 08:00
schedule.every().day.at("09:45").do(proceso_completo_diario)

# Ejecutar inmediatamente al iniciar (para el primer día)
proceso_completo_diario()

# Loop principal
print("\n🤖 Bot iniciado - Esperando tareas programadas...")
while True:
    schedule.run_pending()
    time.sleep(60)  # Revisar cada minuto
