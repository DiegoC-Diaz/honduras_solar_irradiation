"""
Módulo de Extracción de Calidad del Aire y Clima para Cortés, Honduras.
========================================================================
Utiliza los límites geográficos de los municipios de Cortés (desde data/boundaries/)
y consulta la API abierta de Open-Meteo Air Quality (y Open-Meteo Archive/Forecast)
para generar series temporales estructuradas en CSV.

Fuente de Calidad del Aire: Open-Meteo Air Quality API (Copernicus CAMS / GFS)
Límites Geográficos: OCHA HDX COD-AB Honduras (hnd_admin_boundaries.gdb)
"""

import os
import time
import argparse
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

import requests
import pandas as pd

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False


# Endpoints de Open-Meteo (Acceso libre sin API key)
OPEN_METEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Variables de calidad del aire por defecto
DEFAULT_AIR_QUALITY_VARS = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "aerosol_optical_depth",
    "dust",
    "uv_index",
    "us_aqi",
    "european_aqi",
]

# Variables meteorológicas / climáticas complementarias
DEFAULT_WEATHER_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "direct_normal_irradiance",
]

# Fallback con centroides oficiales de los 12 municipios de Cortés (en caso de no tener geopandas instalado)
CORTES_MUNICIPALITIES_FALLBACK = [
    {"adm2_pcode": "HN0501", "adm2_name": "San Pedro Sula", "center_lat": 15.501409, "center_lon": -88.066707},
    {"adm2_pcode": "HN0502", "adm2_name": "Choloma", "center_lat": 15.648904, "center_lon": -87.968027},
    {"adm2_pcode": "HN0503", "adm2_name": "Omoa", "center_lat": 15.658870, "center_lon": -88.199228},
    {"adm2_pcode": "HN0504", "adm2_name": "Pimienta", "center_lat": 15.271921, "center_lon": -87.971545},
    {"adm2_pcode": "HN0505", "adm2_name": "Potrerillos", "center_lat": 15.183437, "center_lon": -87.958566},
    {"adm2_pcode": "HN0506", "adm2_name": "Puerto Cortes", "center_lat": 15.757399, "center_lon": -87.852151},
    {"adm2_pcode": "HN0507", "adm2_name": "San Antonio de Cortes", "center_lat": 15.143341, "center_lon": -88.039312},
    {"adm2_pcode": "HN0508", "adm2_name": "San Francisco de Yojoa", "center_lat": 15.019547, "center_lon": -87.984555},
    {"adm2_pcode": "HN0509", "adm2_name": "San Manuel", "center_lat": 15.375875, "center_lon": -87.898445},
    {"adm2_pcode": "HN0510", "adm2_name": "Santa Cruz de Yojoa", "center_lat": 14.995903, "center_lon": -87.842589},
    {"adm2_pcode": "HN0511", "adm2_name": "Villanueva", "center_lat": 15.322351, "center_lon": -88.044334},
    {"adm2_pcode": "HN0512", "adm2_name": "La Lima", "center_lat": 15.504122, "center_lon": -87.861334},
]


def load_cortes_boundaries(
    boundaries_path: str = "data/boundaries/raw/hnd_admin_boundaries.gdb",
    layer: str = "hnd_admin2",
    department_name: str = "Cortes",
) -> pd.DataFrame:
    """
    Carga los límites municipales y extrae los municipios del departamento de Cortés.

    Parameters
    ----------
    boundaries_path : str
        Ruta al archivo GDB, GeoJSON o Shapefile de límites de Honduras.
    layer : str
        Nombre de la capa administrativa (nivel 2 = municipios).
    department_name : str
        Nombre del departamento a filtrar (por defecto 'Cortes').

    Returns
    -------
    gpd.GeoDataFrame o pd.DataFrame
        DataFrame o GeoDataFrame con los municipios de Cortés y sus coordenadas.
    """
    path = Path(boundaries_path)

    if not path.exists():
        print(f"⚠️ Archivo no encontrado en '{boundaries_path}'. Usando centroides oficiales de respaldo.")
        return pd.DataFrame(CORTES_MUNICIPALITIES_FALLBACK)

    if not GEOPANDAS_AVAILABLE:
        print("⚠️ GeoPandas no está instalado en este entorno. Usando catálogo de centroides precomputados.")
        return pd.DataFrame(CORTES_MUNICIPALITIES_FALLBACK)

    try:
        if path.suffix == ".gdb" or path.is_dir():
            gdf = gpd.read_file(str(path), layer=layer)
        else:
            gdf = gpd.read_file(str(path))

        # Filtrar por departamento (búsqueda insensible a mayúsculas y acentos)
        dept_col = next((col for col in ["adm1_name", "adm1_es", "departamento", "DEPTO"] if col in gdf.columns), None)
        if dept_col:
            cortes_gdf = gdf[gdf[dept_col].astype(str).str.contains(department_name, case=False, na=False)].copy()
        else:
            cortes_gdf = gdf.copy()

        if cortes_gdf.empty:
            print(f"⚠️ No se encontraron municipios para '{department_name}' en la capa. Usando respaldo.")
            return pd.DataFrame(CORTES_MUNICIPALITIES_FALLBACK)

        # Verificar o calcular center_lat y center_lon
        if "center_lat" not in cortes_gdf.columns or "center_lon" not in cortes_gdf.columns:
            # Calcular centroides geográficos en WGS84
            cortes_wgs = cortes_gdf.to_crs(epsg=4326) if cortes_gdf.crs != "EPSG:4326" else cortes_gdf
            centroids = cortes_wgs.geometry.centroid
            cortes_gdf["center_lon"] = centroids.x
            cortes_gdf["center_lat"] = centroids.y

        return cortes_gdf

    except Exception as e:
        print(f"⚠️ Error al leer capa con GeoPandas ({e}). Usando centroides oficiales de respaldo.")
        return pd.DataFrame(CORTES_MUNICIPALITIES_FALLBACK)


def export_cortes_geojson(
    gdf_or_df: Any,
    output_path: str = "data/boundaries/processed/cortes_municipalities.geojson"
) -> None:
    """
    Exporta los límites de Cortés en formato GeoJSON simplificado para acceso rápido.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if GEOPANDAS_AVAILABLE and isinstance(gdf_or_df, gpd.GeoDataFrame):
        gdf_or_df.to_file(str(out_file), driver="GeoJSON")
        print(f"✅ Exportado GeoJSON de municipios de Cortés a: {out_file}")
    else:
        print("ℹ️ Exportación GeoJSON omitida (se requiere un GeoDataFrame de GeoPandas).")


def fetch_air_quality_point(
    latitude: float,
    longitude: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    hourly_vars: Optional[Union[List[str], str]] = None,
    timezone: str = "America/Tegucigalpa",
    past_days: Optional[int] = None,
    forecast_days: Optional[int] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Realiza una petición a la API de calidad del aire de Open-Meteo para una coordenada.

    Parameters
    ----------
    latitude : float
        Latitud de la ubicación.
    longitude : float
        Longitud de la ubicación.
    start_date : str, optional
        Fecha inicial en formato 'YYYY-MM-DD'.
    end_date : str, optional
        Fecha final en formato 'YYYY-MM-DD'.
    hourly_vars : list or str, optional
        Lista de variables horarias a consultar.
    timezone : str
        Zona horaria (por defecto 'America/Tegucigalpa').
    past_days : int, optional
        Número de días pasados (si no se especifica start_date).
    forecast_days : int, optional
        Número de días de pronóstico (por defecto 0 si se usa rango histórico).
    timeout : int
        Tiempo máximo de espera por petición en segundos.

    Returns
    -------
    dict
        Respuesta JSON procesada de Open-Meteo.
    """
    if hourly_vars is None:
        hourly_vars = DEFAULT_AIR_QUALITY_VARS

    if isinstance(hourly_vars, list):
        hourly_param = ",".join(hourly_vars)
    else:
        hourly_param = str(hourly_vars)

    params: Dict[str, Any] = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_param,
        "timezone": timezone,
    }

    if start_date and end_date:
        params["start_date"] = start_date
        params["end_date"] = end_date
    elif past_days is not None:
        params["past_days"] = past_days
        if forecast_days is not None:
            params["forecast_days"] = forecast_days
    else:
        # Por defecto los últimos 7 días si no se especifican fechas
        params["past_days"] = 7
        params["forecast_days"] = 1

    response = requests.get(
        OPEN_METEO_AIR_QUALITY_URL,
        params=params,
        timeout=timeout
    )
    response.raise_for_status()

    return response.json()


def fetch_weather_point(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    hourly_vars: Optional[Union[List[str], str]] = None,
    timezone: str = "America/Tegucigalpa",
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Consulta variables climáticas/meteorológicas complementarias desde el archivo histórico de Open-Meteo.
    """
    if hourly_vars is None:
        hourly_vars = DEFAULT_WEATHER_VARS

    if isinstance(hourly_vars, list):
        hourly_param = ",".join(hourly_vars)
    else:
        hourly_param = str(hourly_vars)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_param,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone,
    }

    response = requests.get(
        OPEN_METEO_ARCHIVE_URL,
        params=params,
        timeout=timeout
    )
    response.raise_for_status()

    return response.json()


def fetch_air_quality_cortes(
    boundaries_path: str = "data/boundaries/raw/hnd_admin_boundaries.gdb",
    layer: str = "hnd_admin2",
    start_date: Optional[str] = "2023-01-01",
    end_date: Optional[str] = "2023-12-31",
    air_quality_vars: Optional[List[str]] = None,
    include_weather: bool = False,
    weather_vars: Optional[List[str]] = None,
    timezone: str = "America/Tegucigalpa",
    delay_between_requests: float = 0.2,
) -> pd.DataFrame:
    """
    Descarga los datos de calidad del aire (y opcionalmente clima) para todos los municipios de Cortés.

    Parameters
    ----------
    boundaries_path : str
        Ruta a los límites administrativos.
    layer : str
        Nombre de la capa de municipios.
    start_date : str, optional
        Fecha de inicio 'YYYY-MM-DD'.
    end_date : str, optional
        Fecha de fin 'YYYY-MM-DD'.
    air_quality_vars : list, optional
        Variables de calidad del aire.
    include_weather : bool
        Si True, adjunta variables climáticas históricas (temperatura, precipitación, radiación).
    weather_vars : list, optional
        Variables meteorológicas si include_weather=True.
    timezone : str
        Zona horaria.
    delay_between_requests : float
        Pausa en segundos entre llamadas para respetar límites de tasa.

    Returns
    -------
    pd.DataFrame
        DataFrame consolidado con todas las observaciones y metadatos de los municipios.
    """
    cortes_df = load_cortes_boundaries(boundaries_path, layer=layer)

    print(f"🚀 Iniciando extracción para {len(cortes_df)} municipios de Cortés...")
    print(f"📅 Rango de fechas: {start_date} a {end_date}")

    municipality_dfs = []

    for idx, row in cortes_df.iterrows():
        muni_name = row.get("adm2_name", row.get("adm2_es", f"Municipio_{idx}"))
        pcode = row.get("adm2_pcode", f"HN05{idx:02d}")
        lat = float(row["center_lat"])
        lon = float(row["center_lon"])

        print(f"  📍 Descargando: {muni_name} ({pcode}) [Lat: {lat:.4f}, Lon: {lon:.4f}]...", end=" ")

        try:
            # 1. Calidad del Aire
            aq_data = fetch_air_quality_point(
                latitude=lat,
                longitude=lon,
                start_date=start_date,
                end_date=end_date,
                hourly_vars=air_quality_vars,
                timezone=timezone
            )

            hourly_dict = aq_data.get("hourly", {})
            if not hourly_dict or "time" not in hourly_dict:
                print("⚠️ Sin datos.")
                continue

            df_muni = pd.DataFrame(hourly_dict)

            # 2. Clima / Meteorología (Opcional)
            if include_weather and start_date and end_date:
                try:
                    w_data = fetch_weather_point(
                        latitude=lat,
                        longitude=lon,
                        start_date=start_date,
                        end_date=end_date,
                        hourly_vars=weather_vars,
                        timezone=timezone
                    )
                    w_hourly = w_data.get("hourly", {})
                    if w_hourly and "time" in w_hourly:
                        df_weather = pd.DataFrame(w_hourly)
                        df_muni = pd.merge(df_muni, df_weather, on="time", how="left")
                except Exception as we:
                    print(f"(Aviso: clima no disponible: {we})", end=" ")

            # Añadir metadatos geográficos y administrativos
            df_muni["departamento"] = "Cortes"
            df_muni["adm2_pcode"] = pcode
            df_muni["municipio"] = muni_name
            df_muni["latitude"] = lat
            df_muni["longitude"] = lon

            # Reorganizar columnas principales al inicio
            front_cols = ["departamento", "adm2_pcode", "municipio", "latitude", "longitude", "time"]
            other_cols = [c for c in df_muni.columns if c not in front_cols]
            df_muni = df_muni[front_cols + other_cols]

            municipality_dfs.append(df_muni)
            print(f"✅ ({len(df_muni):,} registros)")

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(delay_between_requests)

    if not municipality_dfs:
        print("⚠️ No se obtuvieron registros de la API.")
        return pd.DataFrame()

    final_df = pd.concat(municipality_dfs, ignore_index=True)
    print(f"\n🎉 Extracción completada: {len(final_df):,} registros en total para Cortés.")
    return final_df


def save_air_quality_to_csv(
    df: pd.DataFrame,
    output_path: str = "data/air_quality/processed/cortes_air_quality_hourly.csv",
    index: bool = False,
) -> pd.DataFrame:
    """
    Guarda el DataFrame de calidad del aire en un archivo CSV asegurando los directorios requeridos.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame a guardar.
    output_path : str
        Ruta destino del archivo CSV.
    index : bool
        Si True, incluye el índice de pandas en el CSV.

    Returns
    -------
    pd.DataFrame
    """
    if df.empty:
        print("⚠️ DataFrame vacío. No se generó archivo CSV.")
        return df

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(out_file, index=index, encoding="utf-8")
    print(f"💾 Archivo CSV guardado exitosamente en: {out_file.resolve()}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Descarga datos de calidad del aire y clima para los municipios de Cortés, Honduras."
    )
    parser.add_argument(
        "--boundaries",
        type=str,
        default="data/boundaries/raw/hnd_admin_boundaries.gdb",
        help="Ruta al archivo GDB o GeoJSON de límites de Honduras.",
    )
    parser.add_argument(
        "--layer",
        type=str,
        default="hnd_admin2",
        help="Nombre de la capa de municipios dentro del GDB.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2023-01-01",
        help="Fecha inicial (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2023-01-07",
        help="Fecha final (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--include-weather",
        action="store_true",
        help="Incluir variables climáticas (temperatura, precipitación, radiación, etc.).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/air_quality/processed/cortes_air_quality.csv",
        help="Ruta destino del archivo CSV resultante.",
    )
    parser.add_argument(
        "--export-geojson",
        action="store_true",
        help="Exportar además los polígonos de Cortés a data/boundaries/processed/cortes_municipalities.geojson",
    )

    args = parser.parse_args()

    # Si se solicitó exportar GeoJSON de límites de Cortés
    if args.export_geojson:
        gdf = load_cortes_boundaries(args.boundaries, layer=args.layer)
        export_cortes_geojson(gdf)

    # Extraer y guardar
    df = fetch_air_quality_cortes(
        boundaries_path=args.boundaries,
        layer=args.layer,
        start_date=args.start_date,
        end_date=args.end_date,
        include_weather=args.include_weather,
    )

    save_air_quality_to_csv(df, output_path=args.output)


if __name__ == "__main__":
    main()
