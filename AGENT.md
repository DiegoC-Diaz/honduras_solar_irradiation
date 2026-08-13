# 🤖 Directrices del Agente AI (AGENT.md)

Este documento define la estructura del proyecto, convenciones organizativas y directrices estrictas para cualquier asistente AI o desarrollador que trabaje en este repositorio.

---

## 📌 Principios del Proyecto

1. **Objetivo Principal:** Análisis de datos geospaciales y estadísticos del potencial de irradiación solar y del Índice de Cobertura y Acceso a Energía Eléctrica (ICAEH) en Honduras (ODS 7: Energía Asequible y No Contaminante).
2. **Respeto Estricto de Rutas en Notebooks:**
   - **NUNCA** modificar ni corregir rutas internas o código dentro de los cuadernos `.ipynb` en `notebooks/` a menos que el usuario lo solicite explícitamente.

---

## 📁 Estructura Estándar de Datos (`data/`)

Los datos en `data/` están estrictamente organizados **por fuente u origen**. Cada directorio de fuente debe contener la siguiente estructura interna estandarizada:

```text
data/
├── <nombre_fuente>/
│   ├── raw/          # Archivos crudos descargados u obtenidos originalmente
│   ├── processed/    # Archivos transformados, filtrados o derivados para análisis
│   ├── metadata/     # Factsheets, esquemas JSON, encuestas o documentación metodológica
│   └── README.md     # Documentación del dataset (Descripción, Fuente/URL y Licencia)
```

### Fuentes Actuales Registradas:
- `data/GIS_Data_SolarPower/`: Rásters y mapas del Global Solar Atlas (Solargis / Banco Mundial).
- `data/ICAEH/`: Reportes e índices de acceso a la energía (SEN / ENEE / INE).
- `data/boundaries/`: Límites político-administrativos de Honduras (UN OCHA / HDX).
- `data/gbif/`: Datos de biodiversidad y ocurrencias (API de GBIF).
- `data/nasa_power/`: Datos meteorológicos e irradiación solar puntual (NASA POWER).
- `data/owid_ember/`: Generación eléctrica por fuente (Our World in Data / Ember).

---

## 📝 Plantilla Estándar para `README.md` de Datasets

Cada subcarpeta en `data/<fuente>/` debe contar con un archivo `README.md` estructurado de la siguiente manera:

```markdown
# Dataset: [Nombre del Dataset / Fuente]

## 📝 Descripción Breve
[Breve descripción del dataset, sus variables principales y su propósito en el proyecto]

## 🌐 Fuente de Origen
- **Organización / Proveedor:** [Nombre de la organización o plataforma]
- **URL de Descarga / API:** [URL de descarga o endpoint]
- **Fecha de Extracción / Consulta:** [AAAA-MM-DD]

## 📜 Información de Licencia
- **Tipo de Licencia:** [Ej: CC BY 4.0 / Public Domain / Propietaria / Datos Abiertos]
- **Enlace a la Licencia:** [URL a la licencia o términos de uso]
- **Atribución Requerida:** [Texto de atribución requerido por el proveedor]

## 📁 Estructura del Directorio
- `raw/`: Archivos y datos crudos sin modificar.
- `processed/`: Datasets procesados, filtrados o transformados.
- `metadata/`: Documentación adicional, diccionarios de datos o archivos auxiliares.
```

---

## 🐍 Organización de Scripts Utilitarios (`utils/`)

Todos los scripts de Python reutilizables deben residir en `utils/`.
- `gbif_process.py`: Módulo cliente para la API de GBIF.
- `pdf_process.py`: Script para extracción de páginas en archivos PDF.
- `extra_table.py`: Extracción tabular con Camelot.
