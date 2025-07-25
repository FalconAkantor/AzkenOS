# 🧠 Sistema Live de Diagnóstico y Benchmark Automatizado con IA
[🎥 Ver video en YouTube AzkenOS KeepCoding DEMO ▶](https://youtu.be/k2700OgdUDM)


Este proyecto proporciona un sistema operativo **Linux Live** con todos los drivers NVIDIA y herramientas preinstaladas para ejecutar automáticamente una batería de **benchmarks avanzados**, monitorear el sistema en tiempo real y analizar los resultados mediante **inteligencia artificial local**.

El sistema operativo tiene un peso total de 30Gb.

---
## 📖 Documentación Adicional

Para más detalles sobre la instalación, configuración y uso, consulta el archivo  
[README_AGENT.md](README_AGENT.md)  
en la raíz de este repositorio. Allí encontrarás instrucciones paso a paso, ejemplos de configuración y referencias completas.  
---

## 🚨 ¿Por qué IA?

El análisis de resultados es una tarea crítica que, realizada manualmente, puede implicar errores humanos, diagnósticos incorrectos o inconsistencias.

Gracias al uso de **modelos de lenguaje locales como Qwen2.5 sobre Ollama**, este sistema:

- 📊 Interpreta automáticamente cada resultado técnico.
- ❗ Detecta anomalías que un técnico podría pasar por alto.
- 📋 Genera informes detallados y visuales (PDF) con secciones coloreadas (verde/rojo).
- 📡 Notifica directamente por Discord en caso de incidencias.

**Evita errores humanos y garantiza una validación precisa, uniforme y trazable.**

---

## 🚀 Funcionalidades principales

- ✅ **Sistema Live Bootable** (sin instalación).
- 🧪 **Ejecución automatizada de benchmarks**: CPU, GPU, memoria, red y disco.
- 📈 **Monitorización en tiempo real**: CPU, RAM, temperatura, GPU, red.
- 📡 **Envío automático a Discord** de logs, métricas e informes.
- 🤖 **Análisis local con IA** (Qwen2.5 + Ollama).
- 🧾 **Generación de PDF profesional** con índice e hipervínculos.
- 🌐 **Interfaz web integrada (Flask + SocketIO)**:
  - Navegador de archivos y carpetas.
  - Editor de scripts `.sh` y `.py`.
  - Terminal interactiva web.
  - Panel de métricas actualizado en vivo.
  - Control de ejecución y parada de procesos.

---

## 🧠 Arquitectura

```plaintext
┌─────────────┐
│  AZKEN OS   │
│  IA QWEN2.5 │
└────┬────────┘
     │
     ▼
 Benchmarks  ─────▶  Monitor         ─────▶   Discord Bot   
 (Bash/Python)      (psutil+GPUtil)            + Webhooks   
                                                    │
                                                    ▼
                                           📊 Análisis con IA
                                           (Qwen2.5 vía Ollama)
```
## 📦 Scripts incluidos

| ID | Nombre                | Función                                    |
|----|------------------------|---------------------------------------------|
| 1  | Automatizado Server    | Diagnóstico completo en servidores          |
| 2  | Automatizado Desktop   | Diagnóstico completo en estaciones de trabajo |
| 3  | Sin GPU Server         | Diagnóstico sin GPU (modo servidor)         |
| 4  | Sin GPU Desktop        | Diagnóstico sin GPU (modo escritorio)       |
| 5  | Individual             | Tests manuales / personalizados             |

---

## 🧪 Benchmarks disponibles

Este sistema ejecuta una batería de pruebas ampliamente utilizadas en validación de hardware:

- **Geekbench 6 (CPU y GPU)**
- **OctaneBench**
- **Mprime**
- **GPU-Burn**
- **FIO (test de disco)**
- **STREAM (benchmark de memoria)**
- **Smartctl + pruebas de sectores**
- **Gobernador y frecuencia base (valida throttling o turbo)**

---

## 🧬 Análisis de logs con IA (Ollama + Qwen2.5)

El componente más crítico del sistema es su capacidad de **análisis automático con IA local**, sin depender de conexión a internet.

Cada sección de log (por ejemplo: `Octane`, `Geekbench`, `GPU-Burn`) se procesa con Qwen2.5 para:

- 🔍 Extraer valores exactos y sin interpretar desde los logs originales.
- 📊 Comparar automáticamente con puntuaciones de referencia según el modelo detectado.
- 🚨 Detectar problemas como:
  - Frecuencias de CPU/GPU por debajo de lo esperado.
  - Rendimiento bajo en benchmarks clave.
  - Inestabilidad térmica o throttling.
- 🧾 Generar informes bien estructurados, destacando secciones problemáticas.
- 📣 Notificar a los administradores si se detecta algún fallo mediante mención automática en Discord.

> Esta capa de IA reduce errores humanos, acelera el diagnóstico y estandariza los informes.

---

## 🖥️ Interfaz Web Integrada

El sistema incluye una interfaz web desarrollada en **Flask + Socket.IO + Xterm.js**, accesible desde navegador local:

- 🗂️ **Explorador de archivos** por carpetas y subdirectorios.
- ✏️ **Editor de scripts** `.sh` y `.py` desde el navegador.
- 💻 **Terminal web interactiva**, con compatibilidad con Bash.
- 📊 **Panel de métricas en vivo**: uso de CPU, RAM, temperatura, GPUs, frecuencia y red.
- 🔌 **Control de ejecución y parada** de scripts en segundo plano.

> Ideal para entornos de validación donde no se quiere abrir una terminal directamente.

---

## 📡 Integración con Discord

Todos los eventos relevantes se notifican automáticamente en Discord:

- 🔍 Logs parciales durante la ejecución, en tiempo real.
- 📦 Logs finales limpios: `*_final.txt`.
- 📁 Carpeta de resultados comprimida: `*_reports.zip`.
- 📄 Informe en PDF autogenerado con índice y formato profesional.
- 🤖 Análisis detallado por IA, publicado como hilos temáticos.
- 👮‍♂️ Menciones automáticas a administradores si se detectan fallos.

---

## 🔧 Requisitos

- GPU **NVIDIA** (para los benchmarks con CUDA)
- Python **3.8+**

### 📦 Dependencias Python

psutil
requests
reportlab
flask
flask-socketio
eventlet
GPUtil

---

## ⚙️ Herramientas del sistema necesarias

El sistema tiene instaladas las siguientes herramientas a nivel de sistema operativo:

- 🧠 `ollama` (con el modelo `qwen2.5` descargado previamente)
- 🖥️ `nvidia-smi` (para monitorización de GPU NVIDIA)
- 💽 `smartctl` (para análisis S.M.A.R.T. de discos)
- 🧪 `fio` (para pruebas de rendimiento de almacenamiento)
- 🔬 `mprime` (para estabilidad y frecuencia de CPU)
- 🧰 Herramientas básicas de entorno:
  - `bash`, `zip`, `curl`, `coreutils`, `procps`, `net-tools`, etc.

> ⚠️ Todos estos paquetes están incluidos en la ISO personalizada del sistema Live.

---

## 📁 Ejemplo de salida

Una vez completada la ejecución, el sistema genera los siguientes archivos:

```text
M1234R24245_ibañez.txt              # Log crudo
M1234R24245_ibañez_final.txt        # Log limpio (sin ruido)
M1234R24245_ibañez_reports.zip      # Carpeta reports comprimida
M1234R24245_ibañez_informe.pdf      # Informe PDF profesional generado por IA
```
Todos estos archivos son enviados automáticamente a Discord y archivados para trazabilidad.

