# ☀️ Honduras Solar Irradiation & Energy Access (ODS 7)

Este repositorio contiene las herramientas de procesamiento de datos, scripts utilitarios, capas geospaciales y cuadernos de análisis enfocados en la evaluación del potencial de irradiación solar, descarbonización de la matriz eléctrica, y el **Índice de Cobertura y Acceso a Energía Eléctrica en Honduras (ICAEH)**, en el marco del **Objetivo de Desarrollo Sostenible 7 (ODS 7: Energía Asequible y No Contaminante)** de las Naciones Unidas.

---

## 📁 Estructura del Proyecto

```text
ods-7/
├── data/                                         # Datasets crudos, procesados y metadatos (Ver data/README.md)
│   ├── EPHM/                                     # Encuesta Permanente de Hogares de Propósitos Múltiples (INE)
│   ├── Edgar/                                    # Emisiones NetCDF mensuales de CO2 sector energía (EDGAR JRC)
│   ├── GIS_Data_SolarPower/                      # Capas raster GeoTIFF y AAIGRID (Global Solar Atlas v2)
│   ├── ICAEH/                                    # Informes y tablas de cobertura eléctrica municipal (SEN / ENEE)
│   ├── air_quality/                              # Series horarias de calidad del aire y clima (Open-Meteo / CAMS)
│   ├── boundaries/                               # Límites administrativos de Honduras en GDB y GeoJSON (OCHA HDX)
│   ├── chile_urban/                              # Benchmark comparativo: Solar, renovables y urbanización en Chile
│   ├── crn_plan_expansion/                       # Anexos generación CREE y series históricas del PIB (Banco Mundial)
│   ├── gbif/                                     # Registros de ocurrencia de biodiversidad (API GBIF)
│   ├── index/                                    # Modelo INFORM Honduras y Preselección Solar Territorial (IPS)
│   ├── nasa_power/                               # Series de radiación solar y meteorología puntual (NASA POWER)
│   ├── owid_ember/                               # Histórico de generación eléctrica por fuente (OWID / Ember)
│   ├── perfil_municipal_cortes/                  # Indicadores IDH, IDS y sociodemográficos de Cortés (PNUD / INE)
│   ├── poblacion_anual_honduras/                 # Serie histórica de población nacional (Banco Mundial WDI)
│   ├── sen_despacho_energia/                     # Despacho horario por tecnología y demanda residencial (CND / ODS)
│   ├── temperature/                              # Serie mensual de temperatura máxima 1901-2025 (CRU TS v4.10)
│   └── README.md                                 # Catálogo Maestro y Diccionario de Datos del proyecto
├── notebooks/                                    # Cuadernos Jupyter para modelado y análisis de datos (Ver notebooks/README.md)
│   ├── 01_cobertura_electrica_icaeh.ipynb        # Análisis Exploratorio (EDA) de Cobertura Eléctrica (ICAEH)
│   ├── 02_generacion_despacho_electrico_honduras.ipynb # Despacho horario y matriz de generación eléctrica (CND / ENEE)
│   ├── 03_diagnostico_solar_municipal_cortes.ipynb # Diagnóstico de Irradiación (GHI/PVOUT) en municipios de Cortés
│   ├── 04_pronostico_demanda_pib_poblacion.ipynb # Modelado econométrico de demanda residencial vs. PIB y población
│   ├── 05_vulnerabilidad_social_cortes.ipynb     # Evaluación de vulnerabilidad social, IDH, IDS y NBI en Cortés
│   ├── 06_indicadores_riesgo_inform_honduras.ipynb # Procesamiento de indicadores de riesgo subnacional INFORM
│   ├── 07_indice_priorizacion_solar_ips_cortes.ipynb # Formulación del Índice de Priorización Solar (IPS) en Cortés
│   ├── 08_emisiones_co2_sector_electrico.ipynb   # Procesamiento de grillas raster NetCDF de emisiones EDGAR
│   ├── 09_benchmark_chile_solar_urbanizacion.ipynb # Estudio comparativo internacional: Transición solar en Chile
│   ├── drafts/                                   # Cuadernos preliminares y pruebas de concepto archivadas
│   │   ├── gda_preliminar.ipynb
│   │   ├── indice_preliminar.ipynb
│   │   └── gbif_preliminar.ipynb
│   ├── media/                                    # Gráficos y figuras exportadas para los cuadernos
│   └── README.md                                 # Guía metodológica y flujo de ejecución de cuadernos
├── outputs/                                      # Figuras, mapas y datasets de salida generados
│   ├── heatmap_correlacion_cortes.png            # Matriz de correlación de variables socioeconómicas y climáticas
│   ├── idh_vs_ips_scatter_cortes.png             # Dispersión IDH vs. Índice de Priorización Solar
│   ├── ivs_ranking_cortes.png                    # Ranking de Vulnerabilidad Social en Cortés
│   ├── ivs_vs_ips_scatter_cortes.png             # Comparativa de Vulnerabilidad Social vs. Priorización Solar
│   ├── perfil_dimensiones_vulnerabilidad.png     # Gráfico de barras de dimensiones de vulnerabilidad
│   ├── vulnerabilidad_social_cortes.csv          # Tabla consolidada del índice de vulnerabilidad social
│   └── municipios_prioritarios_cortes.csv        # Municipios seleccionados para despliegue prioritario
├── utils/                                        # Módulos Python reutilizables de extracción y procesamiento
│   ├── airquality.py                             # Cliente API para Open-Meteo Air Quality y clima horario
│   ├── edgar_process.py                          # Extracción de estadísticas zonales desde rasters NetCDF de EDGAR
│   ├── extra_table.py                            # Extracción y estructuración de tablas PDF con Camelot
│   ├── gbif_process.py                           # Cliente de consulta y paginación para la API de GBIF
│   └── pdf_process.py                            # Extracción automatizada de páginas de informes PDF con PyPDF
├── .gitignore                                    # Exclusiones de control de versiones (datos pesados, cache)
└── README.md                                     # Documentación principal del repositorio
```

---

## 📓 Cuadernos de Análisis (`notebooks/`)

Para la guía detallada de la secuencia metodológica, consulte [`notebooks/README.md`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/README.md).

| # | Cuaderno | Descripción y Objetivo Analítico |
| :---: | :--- | :--- |
| **01** | [`notebooks/01_cobertura_electrica_icaeh.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/01_cobertura_electrica_icaeh.ipynb) | **Análisis Exploratorio del ICAEH:** Diagnóstico de las brechas de cobertura eléctrica a nivel municipal y departamental en Honduras. Identifica municipios en rezago crítico (< 50% de cobertura) para priorización de proyectos autónomos. |
| **02** | [`notebooks/02_generacion_despacho_electrico_honduras.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/02_generacion_despacho_electrico_honduras.ipynb) | **Matriz Energética y Despacho:** Análisis horario del despacho eléctrico del CND/ENEE, estacionalidad de fuentes renovables (solar, hidro, eólica, biomasa) y variabilidad diurna de la curva de demanda. |
| **03** | [`notebooks/03_diagnostico_solar_municipal_cortes.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/03_diagnostico_solar_municipal_cortes.ipynb) | **Diagnóstico Solar Municipal (Cortés):** Procesamiento de capas raster del Global Solar Atlas (GHI, PVOUT), intersección espacial con geometrías administrativas (GDB) y cálculo de potencial fotovoltaico en los 12 municipios. |
| **04** | [`notebooks/04_pronostico_demanda_pib_poblacion.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/04_pronostico_demanda_pib_poblacion.ipynb) | **Proyección Econométrica de Demanda:** Modelado de la elasticidad de la demanda eléctrica residencial en función del crecimiento del PIB constante y la evolución demográfica del Banco Mundial. |
| **05** | [`notebooks/05_vulnerabilidad_social_cortes.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/05_vulnerabilidad_social_cortes.ipynb) | **Vulnerabilidad Social y Pobreza Multidimensional:** Integración de la EPHPM, IDH, IDS y NBI a escala municipal para identificar sectores con mayor necesidad de acceso energético subsidiado o comunitario. |
| **06** | [`notebooks/06_indicadores_riesgo_inform_honduras.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/06_indicadores_riesgo_inform_honduras.ipynb) | **Riesgo y Capacidad de Afrontamiento:** Depuración y análisis del modelo subnacional INFORM para Honduras (amenazas climáticas, vulnerabilidad socioeconómica y falta de infraestructura). |
| **07** | [`notebooks/07_indice_priorizacion_solar_ips_cortes.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/07_indice_priorizacion_solar_ips_cortes.ipynb) | **Índice de Priorización Solar (IPS):** Formulación multicriterio que pondera potencial solar, seguridad climática, infraestructura de red y capacidad adaptativa para priorizar municipios receptores en Cortés. |
| **08** | [`notebooks/08_emisiones_co2_sector_electrico.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/08_emisiones_co2_sector_electrico.ipynb) | **Emisiones del Sector Eléctrico:** Procesamiento espacial de las grillas globales NetCDF de EDGAR v8 para cuantificar las emisiones locales de dióxido de carbono por generación termoeléctrica. |
| **09** | [`notebooks/09_benchmark_chile_solar_urbanizacion.ipynb`](file:///Users/diegocarcamo/Documents/ods-7/notebooks/09_benchmark_chile_solar_urbanizacion.ipynb) | **Benchmark Regional (Chile):** Estudio empírico de la curva de adopción fotovoltaica a gran escala en Chile y su relación con la urbanización, como lección aprendida para la política energética de Honduras. |

---

## Datos:
Archivo .zip

## 🛠️ Módulos Utilitarios (`utils/`)

| Módulo | Funcionalidad Principal |
| :--- | :--- |
| [`utils/airquality.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/airquality.py) | Consulta automatizada por lotes a la API abierta de Open-Meteo para extraer contaminantes atmosféricos (PM2.5, PM10, CO, NO2, O3, AQI) y meteorología complementaria de los municipios de Cortés. |
| [`utils/edgar_process.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/edgar_process.py) | Pipeline de procesamiento zonal de alto rendimiento para archivos NetCDF (.nc) de EDGAR. Optimiza la memoria RAM mediante recorte espacial de geometrías municipales hondureñas y escritura incremental a CSV. |
| [`utils/gbif_process.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/gbif_process.py) | Extracción de ocurrencias de biodiversidad desde la API REST de GBIF mediante polígonos espaciales WKT, gestionando paginación automática y exportación estructurada. |
| [`utils/extra_table.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/extra_table.py) | Extracción automatizada de matrices y tablas tabulares complejas incrustadas en informes PDF del sector energético mediante `camelot-py`. |
| [`utils/pdf_process.py`](file:///Users/diegocarcamo/Documents/ods-7/utils/pdf_process.py) | Utilidad con `pypdf` para extraer y ensamblar rangos específicos de páginas de informes gubernamentales voluminosos. |

---

## 📊 Catálogo de Datos (`data/`)

Para consultar el inventario detallado de los 16 conjuntos de datos, sus fuentes oficiales, licencias de uso, periodicidades y diccionarios de variables, consulte el **[Catálogo Maestro de Datos (`data/README.md`)](file:///Users/diegocarcamo/Documents/ods-7/data/README.md)**.

---

## 🚀 Requisitos e Instalación

Se recomienda utilizar un entorno Python 3.10+ (preferiblemente vía Conda / Miniforge para dependencias geoespaciales y NetCDF):

```bash
# Crear y activar entorno virtual
conda create -n ods7 python=3.10 -y
conda activate ods7

# Dependencias geoespaciales, raster y NetCDF
conda install -c conda-forge geopandas rasterio rioxarray netcdf4 rasterstats shapely -y

# Dependencias de análisis y visualización
pip install pandas numpy matplotlib seaborn requests pypdf camelot-py[cv] openpyxl
```

---

## 📜 Licencia y Créditos
Proyecto desarrollado para el análisis de desarrollo sostenible, transición energética e irradiación solar en Honduras (ODS 7). Consulte la licencia específica de cada conjunto de datos en su respectiva carpeta.
