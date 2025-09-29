import os
import subprocess
import schedule
import time
import json
from datetime import datetime, timedelta

def ejecutar_scraping():
    print("🔄 1. Ejecutando scraping con Playwright...")
    subprocess.run(["python", "fotmob_api_playwright.py"], check=True)

def ejecutar_analisis():
    print("🔄 2. Analizando partidos...")
    subprocess.run(["python", "analizar_partido.py"], check=True)

def ejecutar_envio_completo():
    print("🔄 3. Enviando lista completa a Telegram...")
    subprocess.run(["python", "enviar_a_telegram.py", "hora"], check=True)

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

def enviar_partido_individual(partido):
    """Envía notificación de un partido específico"""
    print(f"⚽ Enviando partido: {partido['local']} vs {partido['visitante']}")
    # Aquí puedes personalizar el envío individual si quieres
    # Por ahora usaremos el script existente
    subprocess.run(["python", "enviar_a_telegram.py", "hora"])

def proceso_completo_diario():
    """Ejecuta el flujo completo una vez al día"""
    print("\n🚀 INICIANDO PROCESO DIARIO")
    print("=" * 50)
    
    try:
        ejecutar_scraping()
        ejecutar_analisis()
        ejecutar_envio_completo()
        programar_partidos_del_dia()
        print("\n✅ Proceso diario completado")
    except Exception as e:
        print(f"❌ Error en proceso diario: {e}")

# Programar proceso completo diario a las 08:00
schedule.every().day.at("19:02").do(proceso_completo_diario)

# Ejecutar inmediatamente al iniciar (para el primer día)
proceso_completo_diario()

# Loop principal
print("\n🤖 Bot iniciado - Esperando tareas programadas...")
while True:
    schedule.run_pending()
    time.sleep(60)  # Revisar cada minuto
