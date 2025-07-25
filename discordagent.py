#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import requests
import glob
import time
import socket

# === ADICIÓN PDF: import ReportLab ===
# Requiere instalar: pip install reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, PageBreak
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from reportlab.lib.units import cm

# ================= CONFIGURACIÓN =================
# Buscar automáticamente el archivo de log final que cumpla "*_final.txt"
log_files = glob.glob("*_final.txt")
if not log_files:
    print("No se encontró ningún archivo de log final.")
    sys.exit(1)
if len(log_files) > 1:
    print("Se encontraron varios archivos de log final; se usará el primero:", log_files[0])
LOG_FILE_PATH = log_files[0]

# Usar el modelo qwen2.5
MODEL_NAME = "qwen2.5"
# Configuración de Discord
DISCORD_BOT_TOKEN         = "TOKEN"
DISCORD_FORUM_CHANNEL_ID  = "TOKEN"
ADMIN_ID                  = "TOKEN"
API_BASE_URL              = "https://discord.com/api/v9"
# ===================================================

def run_ollama_analysis(model, prompt_text):
    """
    Ejecuta un análisis con ollama y devuelve la salida.
    """
    try:
        p = subprocess.run(
            ["ollama", "run", model, prompt_text],
            capture_output=True, text=True, check=True
        )
        return p.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("Error al ejecutar ollama run:", e)
        return ""

def is_abnormal(text):
    """
    Pregunta al modelo si el análisis contiene una anomalía.
    El modelo debe responder 'ANOMALIA' o 'OK'.
    """
    prompt = (
        "A continuación tienes un fragmento de análisis de resultados de benchmark.\n"
        "¿Este texto indica un error, anomalía o fallo de hardware/configuración?\n"
        "Responde SOLO con ANOMALIA o OK.\n\n"
        f"{text}"
    )
    resp = run_ollama_analysis(MODEL_NAME, prompt).upper()
    return resp.startswith("ANOMALIA")

def generate_pdf_report(serial, analyses):
    """
    Genera un PDF con:
     - Portada con nombre de máquina y fecha
     - Índice automático con hipervínculos
     - Secciones coloreadas: verde si OK, rojo si anomalía
    """
    pdf_filename = f"{serial}_informe.pdf"

    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kw):
            super().__init__(filename, pagesize=A4, **kw)
            frame = Frame(self.leftMargin, self.bottomMargin,
                          self.width, self.height, id='normal')
            tpl = PageTemplate(id='normal', frames=[frame],
                               onPage=self._header_footer)
            self.addPageTemplates([tpl])

        def afterFlowable(self, flowable):
            if isinstance(flowable, Paragraph) and flowable.style.name in ('HeadingOK','HeadingError'):
                text = flowable.getPlainText()
                self.notify('TOCEntry', (0, text, self.page))
                key = text.replace(' ', '_')
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level=0, closed=False)

        def _header_footer(self, canvas, doc):
            page_num = canvas.getPageNumber()
            canvas.setFont('Helvetica', 9)
            canvas.drawRightString(
                A4[0] - doc.rightMargin,
                doc.bottomMargin - 0.5*cm,
                f"Página {page_num} | {serial}"
            )

    doc = MyDocTemplate(pdf_filename)
    styles = getSampleStyleSheet()

    # Portada centrada
    styles.add(ParagraphStyle(
        name='TitleCenter', parent=styles['Title'],
        alignment=1, textColor=colors.HexColor('#2E4053'),
        spaceAfter=12
    ))

    # Modificar Heading1 base
    base_h1 = styles['Heading1']
    base_h1.fontSize = 16
    base_h1.leading = 20
    base_h1.spaceBefore = 12
    base_h1.spaceAfter = 6

    # Heading OK (verde) y Error (rojo)
    styles.add(ParagraphStyle(
        name='HeadingOK', parent=base_h1,
        textColor=colors.green
    ))
    styles.add(ParagraphStyle(
        name='HeadingError', parent=base_h1,
        textColor=colors.red
    ))

    normal = styles['Normal']
    normal.fontSize = 11
    normal.leading = 14
    normal.spaceAfter = 4

    story = []
    # --- Portada ---
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"Informe de Benchmark: {serial}", styles['TitleCenter']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Máquina: {serial}", normal))
    story.append(Paragraph(f"Fecha de generación: {time.strftime('%Y-%m-%d %H:%M:%S')}", normal))
    story.append(PageBreak())

    # --- Índice ---
    story.append(Paragraph("Índice de contenido", styles['Heading1']))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(fontSize=12, name='TOCLevel1',
                       leftIndent=20, firstLineIndent=-20, spaceBefore=5),
    ]
    story.append(toc)
    story.append(PageBreak())

    # --- Secciones ---
    for bench, analysis in analyses.items():
        style_name = 'HeadingError' if is_abnormal(analysis) else 'HeadingOK'
        story.append(Paragraph(bench, styles[style_name]))
        story.append(Spacer(1, 0.2*cm))
        for line in analysis.splitlines():
            story.append(Paragraph(line, normal))
        story.append(Spacer(1, 0.5*cm))

    doc.multiBuild(story)
    return pdf_filename

def send_file_to_channel(channel_id, file_path, content=None):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages"
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
    data = {}
    if content:
        data["content"] = content
    with open(file_path, 'rb') as f:
        files = {"file": (os.path.basename(file_path), f, "application/pdf")}
        resp = requests.post(url, headers=headers, data=data, files=files)
    if resp.status_code in (200,201):
        return resp.json().get("id")
    print("Error al enviar archivo a Discord:", resp.text)
    return None

def create_discord_thread(channel_id, thread_name, auto_archive_duration=1440):
    url = f"{API_BASE_URL}/channels/{channel_id}/threads"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": thread_name,
        "auto_archive_duration": auto_archive_duration,
        "type": 11,
        "message": {"content": "Hilo de análisis generado automáticamente."}
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code in (200,201):
        return resp.json()["id"]
    print("Error al crear hilo:", resp.text)
    return None

def send_message_to_channel(channel_id, content):
    url = f"{API_BASE_URL}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, json={"content": content})
    if resp.status_code in (200,201):
        return resp.json()["id"]
    print("Error al enviar mensaje:", resp.text)
    return None

def send_long_message(channel_id, content, max_length=1900):
    ids = []
    for i in range(0, len(content), max_length):
        chunk = content[i:i+max_length]
        mid = send_message_to_channel(channel_id, chunk)
        if mid:
            ids.append(mid)
        time.sleep(1)
    return ids

def parse_log_sections(log_content):
    benchmarks = {
        "Configuracion":   r"(?i)se van a ejecutar los siguientes scripts en secuencia",
        "Valores":         r"Estadísticas del sistema",
        "Gobernador":      r"Ejecutando Gobernador",
        "Octane":          r"Ejecutando Octane",
        "GeekbenchGPU":    r"Prueba en la GPU",
        "Anchobanda":      r"Ejecutando STREAM Benchmark",
        "Mprime":          r"Ejecutando Mprime",
        "Geekbench":       r"Ejecutando Geekbench",
        "GPU-BURN":        r"Ejecutando GPU-BURN",
        "FIO":             r"Ejecutando FIO",
        "Sectores":        r"Ejecutando Sectores",
        "Resultado":       r"Ejecutando Resultado",
        "Comprobaciones":  r"Ejecutando Comprobaciones"
    }
    sections = {k: "" for k in benchmarks}
    current = None
    for line in log_content.splitlines():
        for b, pat in benchmarks.items():
            if re.search(pat, line):
                current = b
                sections[b] += line + "\n"
                break
        else:
            if current:
                sections[current] += line + "\n"
    return sections

def get_prompt_template(benchmark):
    templates = {
      "Configuracion": (
        "Lee la sección de configuración. Ahí se listan los scripts que se van a ejecutar y sus parámetros "
        "(por ejemplo: num_cpus, mem_reservada_gb, frecuencia_base_mhz, duración, clock base de GPU, Dispositivo PCI). "
        "Extrae textualmente cada script con sus parámetros tal como aparecen, y preséntalo como un bloque ordenado, "
        "cada script en una línea independiente."
      ),
      "Valores": (
        "Lee la sección de configuración y valores iniciales. Extrae textualmente cada uno de los siguientes elementos tal como aparecen en el log, sin omitir ni añadir nada:\n"
        "- GPUs NVIDIA CUDA\n"
        "- CPUs disponibles\n"
        "- Modelo de CPU\n"
        "- BIOS (incluyendo nombre y versión)\n"
        "- Frecuencia actual de CPU\n"
        "- Frecuencia base (mínima)\n"
        "- Frecuencia boost (máxima)\n"
        "- Núcleos físicos\n"
        "- Hilos por núcleo\n"
        "- Caché L1d, L1i, L2 y L3\n"
        "- Memoria RAM total\n"
        "Luego, extrae la sección de Información del BMC exactamente como aparece, incluyendo:\n"
        "- IP del BMC\n"
        "- MAC del BMC\n"
        "- Placa base\n"
        "Preséntalo como un bloque de datos ordenado, cada elemento en una línea independiente."
      ),
      "Gobernador": (
        "Lee cuidadosamente la sección de logs correspondiente al test 'Gobernador'. "
        "Extrae exclusivamente las líneas donde se muestra el cambio de governor y las frecuencias de CPU antes y después. "
        "Incluye textualmente cualquier dato o mensaje que aparezca en los logs (por ejemplo, 'Cambiando el gobernador...' o 'Frecuencia actual: 1500.00 MHz'). "
        "No añadas explicaciones ni datos que no estén en los logs. "
        "Basándote únicamente en la información registrada, analiza si la configuración del modo 'performance' es adecuada para el rendimiento observado y explica brevemente por qué."
      ),
      "Octane": (
        "Lee la sección de logs del test 'Octane' y busca el archivo 'result.csv'.\n\n"
        "1. Extrae la puntuación exacta registrada (línea que contenga 'La puntuación de la tarjeta gráfica es:').\n"
        "2. Compara ese valor con las puntuaciones de referencia:\n"
        "   • RTX PRO 6000 Blackwell Workstation Edition: 1771.0\n"
        "   • RTX 5090: 1743.0\n"
        "   • RTX 5090 D: 1495.0\n"
        "   • RTX 4090: 1304.5\n"
        "   • RTX 6000 Ada Generation: 1196.0\n"
        "   • NVIDIA RTX5880-Ada-48Q: 1194.0\n"
        "   • RTX 4090 D: 1191.0\n"
        "   • RTX 5080: 971.5\n"
        "   • RTX 4080 Super: 948.0\n"
        "   • L40S: 911.0\n"
        "   • RTX 4080: 884.0\n"
        "   • RTX 4070 Ti Super: 869.0\n"
        "   • RTX 5070 Ti: 858.0\n"
        "   • RTX 5090 Laptop GPU: 827.0\n"
        "   • RTX 4090 Laptop GPU: 805.0\n"
        "   • RTX 4070 Ti: 761.5\n"
        "   • RTX 4070 Super: 702.0\n"
        "   • RTX 5070: 696.0\n"
        "   • RTX 5000 Ada Generation: 662.5\n"
        "   • RTX 3090: 651.0\n"
        "   • RTX A6000: 651.5\n"
        "   • RTX 4070: 613.5\n"
        "   • RTX 3090 Ti: 597.0\n"
        "   • RTX A5000: 577.0\n"
        "3. Si tu puntuación coincide o está dentro de un 5 % de la de referencia para tu GPU, indica “resultado correcto”; "
        "   de lo contrario, indica “resultado no correcto” y sugiere verificar configuración o hardware.\n"
        "4. Incluye siempre al final este enlace para consultar más comparativas:\n"
        "   https://render.otoy.com/octanebench/results.php?v=&sort_by=&scale_by=&filter=&singleGPU=1&showRTXOff=0"
      ),
      "GeekbenchGPU": (
        "Procesa los logs del test 'GeekbenchGPU' en GPU. "
        "Extrae textualmente cada uno de los siguientes elementos tal como aparecen en el log, "
        "sin añadir ni omitir nada y sin hacer interpretaciones ni análisis:  \n"
        "  - La línea donde se detecta el número de GPUs (“Se han detectado (X) GPUs…”).  \n"
        "  - Cada línea de inicio de prueba (“Ejecutando Geekbench en la GPU (Y)…”).  \n"
        "  - Todas las URLs que aparezcan después de “Resultado:”.  \n\n"
        "Preséntalo en el mismo orden en que aparecen en el log, preferiblemente como un bloque con cada elemento en línea independiente."
      ),
      "Anchobanda": (
        "Analiza el bloque de logs del STREAM Benchmark (Anchobanda). "
        "Para cada uno de los valores Copy, Scale, Add y Triad, extrae textualmente las velocidades en MB/s. "
        "Evita cualquier cálculo o suposición adicional: usa únicamente los valores presentes. "
        "Resume en una frase si el rendimiento de memoria parece uniforme o si hay variaciones notables según los datos extraídos, determina si encuentras errores en los logs."
      ),
      "Mprime": (
        "Lee los registros del test 'Mprime', centrándote en la evolución de la frecuencia de la CPU y las temperaturas. "
        "Extrae textualmente cualquier valor o mensaje que indique cambios de frecuencia, valores de temperatura o errores. "
        "No añadas estimaciones ni información externa. "
        "Concluye si hubo desviaciones respecto a la frecuencia base indicada y menciona cualquier alerta o comportamiento anómalo reflejado en los logs. "
        "Si la frecuencia observada cae por debajo de la frecuencia base configurada, considera esto como un fallo de hardware no válido para operar y sugiere verificar el equipo, esto se imparte también como Resultado OK o Resultado KO al final del log."
      ),
      "Geekbench": (
        "Procesa los logs del test 'Geekbench' en CPU. "
        "Extrae los puntos clave textuales, como puntuaciones sintéticas o mensajes de resumen. "
        "Si no aparece ninguna puntuación, menciona las URLs registradas que hagan referencia a la prueba de CPU. "
        "No inventes valores: basa tu análisis únicamente en la información disponible y comenta la potencia y eficiencia percibida."
      ),
      "GPU-BURN": (
        "Lee la sección de logs del test 'GPU-BURN'. "
        "Extrae textualmente cualquier dato de estabilidad, mensajes de error o información de temperatura y rendimiento. "
        "No añadas métricas de rendimiento que no estén reguladas. "
        "Analiza, basándote en los mensajes extraídos, la estabilidad térmica y de rendimiento de las GPUs durante la prueba. "
        "Si la velocidad de GPU medida está por debajo del clock base configurado, considera esto un problema crítico, indica que no es un funcionamiento válido y sugiere verificar el equipo."
      ),
      "FIO": (
        "Analiza los logs del test 'FIO'. "
        "Extrae textualmente las velocidades de lectura y escritura que aparezcan (por ejemplo, 'read: 1.2 GB/s'). "
        "No hagas cálculos adicionales ni asumas valores que no estén presentes. "
        "Comenta si el rendimiento de almacenamiento parece acorde a las expectativas según las velocidades informadas."
      ),
      "Sectores": (
        "Procesa los logs del test 'Sectores'. "
        "Extrae cualquier métrica de operación de disco registrada en los logs. "
        "No indagues en datos no presentes ni estimes valores. "
        "Menciona posibles anomalías o errores reflejados en los registros y resume la salud del disco según los datos exactos."
      ),
      "Resultado": (
        "Lee la sección final 'Resultado'. "
        "Recopila textualmente cualquier resumen o valor global que indique el desempeño total de la máquina. "
        "No combines ni modifiques datos: integra lo extraído de cada sección previamente analizada y presenta un resumen global fiel a los logs."
      ),
      "Comprobaciones": (
        "Analiza los logs del test 'Comprobaciones'. "
        "Extrae textualmente la verificación del dispositivo PCI y cualquier mensaje de estado relacionado con el hardware Intel. "
        "No añadas conclusiones que no estén respaldadas por los logs. "
        "Indica si el hardware opera correctamente según los mensajes de verificación encontrados."
      ),
    }
    return templates.get(benchmark, "Analiza los resultados de este test.")

def get_octane_prompt(gpu_list):
    referencia = (
        "Las puntuaciones aproximadas por GPU son:\n"
        "RTX PRO 6000 Blackwell Workstation Edition: 1771.0\n"
        "RTX 5090: 1743.0\n"
        "RTX 5090 D: 1495.0\n"
        "RTX 4090: 1304.5\n"
        "RTX 6000 Ada Generation: 1196.0\n"
        "NVIDIA RTX5880-Ada-48Q: 1194.0\n"
        "RTX 4090 D: 1191.0\n"
        "RTX 5080: 971.5\n"
        "RTX 4080 Super: 948.0\n"
        "L40S: 911.0\n"
        "RTX 4080: 884.0\n"
        "RTX 4070 Ti Super: 869.0\n"
        "RTX 5070 Ti: 858.0\n"
        "RTX 5090 Laptop GPU: 827.0\n"
        "RTX 4090 Laptop GPU: 805.0\n"
        "RTX 4070 Ti: 761.5\n"
        "RTX 4070 Super: 702.0\n"
        "RTX 5070: 696.0\n"
        "RTX 5000 Ada Generation: 662.5\n"
        "RTX 3090: 651.0\n"
        "RTX A6000: 651.5\n"
        "RTX 4070: 613.5\n"
        "RTX 3090 Ti: 597.0\n"
        "RTX A5000: 577.0\n"
    )
    gpus_str = ", ".join(gpu_list) if gpu_list else "desconocida(s)"
    return (
        f"Se ha detectado la(s) GPU(s) en el sistema: {gpus_str}.\n"
        f"{referencia}"
        "Extrae únicamente la puntuación exacta correspondiente a la(s) GPU(s) detectada(s). "
        "Si no aparece en la lista, indícalo explícitamente. "
        "Finalmente, indica si el rendimiento te parece aceptable según esa puntuación."
    )

def main():
    if not os.path.exists(LOG_FILE_PATH):
        print(f"No existe '{LOG_FILE_PATH}'."); sys.exit(1)
    with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    basename = os.path.basename(LOG_FILE_PATH)
    serial = basename[:-len("_final.txt")] if basename.endswith("_final.txt") else os.path.splitext(basename)[0]

    thread_id = create_discord_thread(DISCORD_FORUM_CHANNEL_ID, f"Análisis {serial}")
    if not thread_id:
        sys.exit(1)

    sections = parse_log_sections(content)
    valores = sections.get("Valores", "")
    m = re.search(r"- GPUs NVIDIA CUDA\s*:\s*\d+\s*\(([^)]+)\)", valores)
    gpu_list = [g.strip() for g in m.group(1).split(",")] if m else []

    analyses = {}
    for bench, text in sections.items():
        if not text.strip():
            continue
        tpl = get_octane_prompt(gpu_list) if bench == "Octane" else get_prompt_template(bench)
        prompt = (
            f"{tpl}\n\n"
            f"Sección '{bench}':\n\n{text}\n\n"
            "Proporciona un análisis detallado, razonado y bien estructurado en español."
        )
        analysis = run_ollama_analysis(MODEL_NAME, prompt) or f"Error al analizar {bench}."
        analyses[bench] = analysis

        if is_abnormal(analysis):
            msg = f"<@{ADMIN_ID}> posible incidencia en **{bench}**:\n{analysis}"
        else:
            msg = f"**{bench}:**\n{analysis}"
        send_long_message(thread_id, msg)
        time.sleep(2)

    try:
        pdf_path = generate_pdf_report(serial, analyses)
        send_file_to_channel(thread_id, pdf_path, content="Adjunto informe completo en PDF.")
    except Exception as e:
        print("Error generando/enviando PDF:", e)

if __name__ == "__main__":
    main()
