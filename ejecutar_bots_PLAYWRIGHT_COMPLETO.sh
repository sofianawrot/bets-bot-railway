#!/bin/bash

# Activar entorno virtual
source venv/bin/activate

# Ir al directorio del bot
cd ~/Desktop/bets-bot || exit

echo "🚀 INICIANDO BOT COMPLETO"
echo "=========================="

echo "==== 1. Extrayendo partidos del día ===="
python3 fotmob_api_playwright.py || exit 1

echo "==== 2. Filtrando partidos válidos ===="
python3 filtrar_partidos_local_v17.py || exit 1

echo "==== 3. Extrayendo URLs de partidos ===="
python3 scraper_fotmob_url_filtrado_actualizado_v3.py || exit 1

echo "==== 4. Scrapeando detalles de cada partido ===="
python3 scrapear_datos_partido.py || exit 1

echo "==== 5. Descargando clasificaciones por liga ===="
python3 descargar_clasificaciones_por_nombre.py || exit 1

echo "==== 6. Extrayendo clasificaciones por partido ===="
python3 extraer_clasificaciones_por_partido.py || exit 1

echo "==== 7. Unificando detalles y clasificación en TXT final ===="
python3 unificar_detalles_y_clasificacion.py || exit 1

echo "==== 8. Analizando partidos con OpenAI (Bets II) ===="
python3 analizar_partido.py || exit 1

echo "==== 9. Enviando resultados a Telegram ===="
python3 enviar_a_telegram.py hora || exit 1

echo "✅ ¡Todo el flujo completado correctamente!"
