import subprocess
import schedule
import time
import sys

sys.stdout = sys.stderr

def ejecutar_bot():
    print("🚀 Ejecutando bot completo...")
    subprocess.run(["bash", "ejecutar_bots_PLAYWRIGHT_COMPLETO.sh"], check=True)
    print("✅ Bot completado")

schedule.every().day.at("12:45").do(ejecutar_bot)

print("🤖 Bot iniciado - esperando 12:45...")
while True:
    schedule.run_pending()
    time.sleep(60)