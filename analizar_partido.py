import openai
import os
import datetime
import time
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL_ID = "gpt-4o"

PROMPT_INSTRUCCIONES = """
🎯 Rol: Pronosticador profesional
🎯 Objetivo: Analizar el partido y recomendar apuestas con +70% de probabilidad real, siempre usando criterio profesional, contexto y lógica.

🎯 *PIENSA COMO UN PRONOSTICADOR HUMANO:*
- Recomienda únicamente los mercados que tengan valor claro y +70% de probabilidad real. Si solo hay 1, da 1. Si hay 3 o más sólidos, da todos. No asumas que siempre deben ser 2.
- Nunca rellenes por rellenar: solo apuesta cuando realmente haya valor y probabilidad suficiente.
- El porcentaje de probabilidad de cada apuesta debe ser **realista y distinto para cada mercado**: ajusta el % según el riesgo, contexto y estadísticas. No uses el mismo % para todos los picks de un partido, ni pongas más de un pick >90% salvo dominio abrumador.
- Analiza con mentalidad profesional y realista: busca siempre el valor, incluso si el partido no es una final o un derbi.

— FILTRO RIVALIDAD (PRIORIDAD MÁXIMA) —
Descarta cualquier derbi, clásico, o partido de gran rivalidad (misma ciudad/región, histórico tenso, o grandes clásicos nacionales). Si dudas: DESCARTA.
Ejemplos: Real Betis-Sevilla, Celtic-Rangers, Inter-Milan, PSG-Marsella, etc.
➡️ Si es derbi o alta rivalidad, escribe solo: PARTIDO DESCARTADO. [motivo]
➡️ Si no, sigue con el análisis.

— FILTRO DE MOTIVACIÓN Y CONTEXTO —
Descarta el partido solo si ambos equipos no se juegan nada, están 100% salvados o eliminados, o rotan masivamente.
Nunca descartes solo por estar en media tabla.
➡️ Si se cumple, escribe solo: PARTIDO DESCARTADO. [motivo]
➡️ Si no, analiza y recomienda apuestas de valor.

— ANÁLISIS Y REGLAS DE PICKS (usa SOLO los últimos 5 partidos y los H2H recientes) —
Puedes considerar también mercados como “+0.5 goles de [equipo]”, “+1.5 goles de [equipo]” o hándicaps suaves, si el contexto lo respalda claramente. **Si el equipo favorito ha ganado varios partidos recientes por 2+ goles y el rival es claramente inferior, prioriza el Hándicap asiático -1 o -1.5 como mercado principal.**
• Ambos marcan SÍ: Solo si ambos equipos marcan/encajan habitualmente ante rivales de nivel similar, y 2 de los 3 últimos H2H acabaron con ambos marcando, o el contexto favorece (bajas defensivas, urgencia ofensiva, etc). Nunca si hay gran diferencia de nivel o favorito muy superior.
• Ambos marcan NO: Solo si ambos suelen dejar puerta a cero o hay tendencia clara en sus últimos partidos y H2H recientes, o si el rival débil tiene baja producción ofensiva y el fuerte defiende bien.
• +2.5 goles: Solo si al menos 3 de los últimos 5 partidos de cada equipo y 2 de 3 H2H recientes tuvieron +2.5, y contexto ofensivo.
• +1.5 goles: Siempre que ambos promedien al menos 1 gol por partido y el contexto no sea defensivo o partido trampa.
• Win (1/2): Solo si el favorito es muy superior (líder vs. 8º o peor, +10 puntos, >1.5 goles a favor/partido y mínimo 3 victorias últimas 5), juega en casa y sin bajas clave.
• Doble oportunidad (1X/X2): Prioriza siempre que no sea favoritismo claro, rival competitivo o contexto incierto.
• Hándicap asiático -1 o -1.5: Solo si el favorito es claramente superior y en gran forma, ideal en partidos de ida o sin presión excesiva.
• Under 3.5 o Under 4.5: Solo en partidos de vuelta con ventaja clara o contextos de trámite donde se espere poca intensidad ofensiva.
• En caso de duda, elige el mercado más conservador.
• Nunca recomiendes solo por estadísticas si el contexto/motivación sugieren lo contrario.
• Si ningún mercado cumple los filtros: NO HAY APUESTA RECOMENDADA.

⚠️ Revisión final:
Antes de cerrar el análisis, revisa si alguno de estos mercados puede tener valor añadido:
• Hándicap asiático -1 o -1.5 del favorito si el dominio es claro.
• Under 3.5 o Under 4.5 si hay ventaja clara en la ida o contexto de vuelta tranquila.
• Ambos NO marcan, si el rival débil no genera ocasiones y el fuerte defiende bien.

— MATICES ADICIONALES —
- Partido de vuelta/playoff con ventaja clara = prioriza under/conservador.
- Rotaciones/bajas ofensivas: reduce probabilidad de ambos marcan y +2.5.
- Si uno no se juega nada, da peso extra al contexto y motivación.

— SALIDA (NO ESCRIBAS NADA FUERA DE ESTO) —

1. **Bloque para Telegram:**
- Si partido descartado: PARTIDO DESCARTADO. [motivo]
- Si no hay picks: NO HAY APUESTA RECOMENDADA. [motivo]
- Si hay picks con +70%, una línea por apuesta: [Apuesta recomendada] | [porcentaje%]
- Si supera 90%: 🔥 APUESTA RECOMENDADA 🔥 antes de esa apuesta.
- No pongas nombre ni hora en las recomendaciones.

2. **Bloque Justificación**
Justificación: [Motivo breve, máx. 30 palabras, centrado en explicar el contexto, forma y estadísticas recientes, sin repetir el pick ni usar frases como “lo que justifica el %”.]

🔒 NO ESCRIBAS NADA FUERA DE ESTOS BLOQUES.
"""

hoy = datetime.date.today().strftime('%Y-%m-%d')
input_folder = f"inputs_gpt_completo/{hoy}/"
output_folder = f"respuestas_gpt/{hoy}/"

# Crea la carpeta de salida si no existe
os.makedirs(output_folder, exist_ok=True)

if not os.path.isdir(input_folder):
    print(f"❌ La carpeta {input_folder} no existe. ¿Has generado ya los TXT para hoy?")
    exit(1)

# Contadores y log de errores
total = 0
exitos = 0
fallos = 0
errores = []

for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        total += 1
        ruta_txt_partido = os.path.join(input_folder, filename)
        with open(ruta_txt_partido, 'r', encoding='utf-8') as f:
            datos_partido = f.read()

        # Enviamos PROMPT + datos del partido
        prompt_completo = PROMPT_INSTRUCCIONES + "\n\n" + datos_partido
        output_path = os.path.join(output_folder, filename.replace('.txt', '_output.txt'))

        try:
            response = openai.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "user", "content": prompt_completo}
                ],
                max_tokens=720,
                temperature=0.27
            )
            respuesta = response.choices[0].message.content
            exitos += 1
        except Exception as e:
            fallos += 1
            error_msg = f"❌ Error al analizar {filename}: {str(e)}"
            errores.append(error_msg)
            respuesta = error_msg
            print(error_msg)
            if "rate limit" in str(e).lower() or "429" in str(e):
                time.sleep(10)

        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(respuesta)

        print(f"✅ {filename} analizado y guardado como: {os.path.basename(output_path)} en {output_folder}")

# ---- RESUMEN FINAL ----
print("\nResumen del análisis:")
print(f"  Total de partidos: {total}")
print(f"  Analizados con éxito: {exitos}")
print(f"  Fallidos: {fallos}")
if errores:
    print("\nErrores encontrados:")
    for err in errores:
        print("   -", err)
else:
    print("  Sin errores.")

print("\n¡Todos los partidos del día han sido analizados!")
