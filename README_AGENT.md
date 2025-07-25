# 🚀 Discord Benchmark Agent (Es el script de generación dentro de la ISO AzkenOS)

_Analiza automáticamente tus logs de benchmark, notifica anomalías en Discord y genera informes PDF interactivos._

---

## 📖 Descripción

`discord-benchmark-agent` es un script en **Python 3** que:

1. **Detecta** tu archivo de log `*_final.txt`.  
2. **Parcela** el log en secciones (Configuración, Octane, Geekbench, FIO, etc.).  
3. **Solicita** análisis detallado a un modelo de IA (qwen2.5 via Ollama).  
4. **Crea** un hilo en un canal de foro de Discord y publica los resultados, mencionando al administrador si hay anomalías.  
5. **Compila** un informe PDF con portada, índice interactivo y secciones coloreadas según “OK” (verde) o “ANOMALÍA” (rojo).

Ideal para equipos de DevOps, QA y soporte que necesitan vigilancia automática de su suite de benchmarks.

---

## ⭐ Características

- **Parsers personalizados** para cada prueba: Octane, STREAM, Geekbench, Mprime, FIO…  
- **IA dinámica** para detectar anomalías (sin depender de regex fijas).  
- **Integración Discord**: creación de hilos, fragmentación de mensajes, subida de archivos.  
- **Informe PDF** con ReportLab: portada, cabecera/pie, índice, marcadores y coloreado.  
- **Configuración mínima**: un único script y tus credenciales (hardcode o entorno).

---

## 📋 Requisitos

- Python 3.8+  
- [Ollama CLI](https://ollama.com/) en tu PATH  
- Paquetes Python:
  ```bash
  pip install requests reportlab
  ```
## Un bot de Discord con permisos
- Ver el canal  
- Enviar mensajes  
- Crear/gestionar hilos  

---

## ⚙️ Configuración
```bash
# Edita discordagent.py y ajusta estas variables:
MODEL_NAME                = "qwen2.5"
DISCORD_BOT_TOKEN         = "<TU_TOKEN_DEL_BOT>"
DISCORD_FORUM_CHANNEL_ID  = "<ID_CANAL_FORO>"
ADMIN_ID                  = "<ID_ADMIN>"
API_BASE_URL              = "https://discord.com/api/v9"
```
## 🏁 Uso

Genera tu log de benchmarks con sufijo `_final.txt`.

Coloca `discordagent.py` en la misma carpeta que el log.

Ejecuta:

```bash
python3 discordagent.py
```
¡Listo! El bot creará un hilo en Discord, publicará análisis por sección y subirá un PDF resumen.

---

## 🛠️ ¿Cómo Funciona?

- **Detección de log**  
  Usa `glob("*_final.txt")` para encontrar tu archivo de log.

- **Parseo**  
  Regex predefinidos separan bloques de cada benchmark.

- **Análisis IA**  
  1. Prompt específico por sección.  
  2. `ollama run qwen2.5 <prompt>`.  
  3. `is_abnormal()` pregunta al modelo “ANOMALIA” u “OK”.

- **Discord**  
  - `create_discord_thread()`: abre un hilo en foro.  
  - `send_long_message()`: publica análisis fragmentados.  
  - `send_file_to_channel()`: sube el PDF.

- **PDF**  
  ReportLab genera portada, índice dinámico y secciones verdes/rojas.
  
  - Verde: No necesita revision
  
  - Roja: Hay alguna anomalia
