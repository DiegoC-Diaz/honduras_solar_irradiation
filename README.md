# ☀️ Honduras Solar Irradiation & Energy Access (ODS 7)

Este repositorio contiene las herramientas de procesamiento de datos, scripts utilitarios y cuadernos de análisis geospacial enfocados en la evaluación del potencial de irradiación solar y el **Índice de Cobertura y Acceso a Energía Eléctrica en Honduras (ICAEH)**, en el marco del **Objetivo de Desarrollo Sostenible 7 (ODS 7: Energía Asequible y No Contaminante)**.

---

## 📁 Estructura del Proyecto

```text
ods-7/
├── data/                                         # Datasets crudos y procesados
│   ├── boundaries/                               # Límites administrativos (GDB, GeoJSON)
│   ├── ICAEH/ & ICAE_municipal/                  # Reportes de cobertura eléctrica por municipio
│   ├── Honduras_GISdata_LTAy_*                   # Capas raster GeoTIFF y AAIGRID del Global Solar Atlas
│   ├── POWER_Point_Monthly_*                     # Datos meteorológicos y de radiación solar (NASA POWER)
│   ├── electricity-prod-source-stacked.csv       # Generación eléctrica por fuente (OWID / Ember)
│   └── gbif/                                     # Datos de biodiversidad extraídos de la API de GBIF
├── notebooks/                                    # Cuadernos Jupyter para análisis de datos
│   ├── icae_eda.ipynb                            # Análisis Exploratorio de Datos (EDA) de Cobertura Eléctrica (ICAEH)
│   ├── gda.ipynb                                 # Análisis de Datos Geospaciales (GDA) e Irradiación Solar
│   └── gbif.ipynb                                # Integración de ocurrencias de biodiversidad GBIF
├── utils/                                        # Scripts Python utilitarios y de procesamiento
│   ├── gbif_process.py                           # Cliente de consulta y paginación para la API de GBIF
│   ├── pdf_process.py                            # Extracción automatizada de páginas PDF con PyPDF
│   └── extra_table.py                            # Extracción y estructuración de tablas desde PDF con Camelot
├── .gitignore                                    # Exclusiones de Git (datos pesados, cache, binarios)
└── README.md                                     # Documentación principal del proyecto
```

---

## 📓 Descripción de Cuadernos (`notebooks/`)

| Cuaderno | Descripción |
| :--- | :--- |
| [`notebooks/icae_eda.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/icae_eda.ipynb) | **Análisis Exploratorio del ICAEH:** Procesamiento de series temporales de acceso a la energía a nivel municipal y departamental en Honduras. Incluye visualización de brechas de cobertura (< 50%) y comparativas regionales. |
| [`notebooks/gda.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/gda.ipynb) | **Análisis Geospacial:** Procesamiento de datos de radiación solar en formato raster/vectorial, intersección de geometrías (WKT) con límites departamentales y cálculo de estadísticas zonales de irradiación. |
| [`notebooks/gbif.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/gbif.ipynb) | **Biodiversidad y Entorno:** Integración de registros de especies y biodiversidad en zonas de estudio georreferenciadas. |

---

## 🛠️ Módulos y Utilitarios (`utils/`)

| Script | Descripción |
| :--- | :--- |
| [`utils/gbif_process.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/gbif_process.py) | Proporciona funciones reutilizables (`gbif_occurrence_search`, `gbif_fetch_all`, `gbif_to_csv`) para consultar registros de la API de GBIF dentro de un polígono WKT con paginación automática. |
| [`utils/pdf_process.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/pdf_process.py) | Automatiza la lectura y extracción de rangos de páginas específicos de informes en PDF (como reportes del ICAEH) usando `pypdf`. |
| [`utils/extra_table.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/extra_table.py) | Extrae tablas tabulares formateadas desde documentos PDF usando `camelot-py` y exporta los resultados limpios en formato CSV. |

---

## 📊 Fuentes de Datos (`data/`)

1. **Global Solar Atlas (v2):** Datos de Potencial Fotovoltaico (PVOUT) e Irradiación Horizontal Global (GHI) para Honduras en GeoTIFF y AAIGRID.
2. **NASA POWER:** Registro puntual mensual de radiación solar e indicadores climáticos (2000–2025).
3. **ICAEH (Índice de Cobertura y Acceso a Energía Eléctrica Honduras):** Indicadores de electrificación por municipio y departamento.
4. **Our World in Data (OWID) / Ember:** Producción histórica de electricidad por fuente (solar, eólica, hidroeléctrica, térmica).
5. **GBIF (Global Biodiversity Information Facility):** Datos de presencia de especies biológicas para evaluaciones socio-ambientales.

---

## 🚀 Requisitos e Instalación

Para ejecutar los scripts y cuadernos del proyecto, se recomienda un entorno Python 3.10+ con las siguientes dependencias principales:

```bash
# Dependencias geospaciales y analíticas
pip install pandas geopandas rasterio shapely requests pypdf camelot-py[cv] matplotlib seaborn
```

---

## 📜 Licencia y Créditos
Proyecto desarrollado para el análisis de desarrollo sostenible e irradiación solar en Honduras (ODS 7).
