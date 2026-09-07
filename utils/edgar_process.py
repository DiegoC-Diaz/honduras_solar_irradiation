"""
Módulo para el procesamiento eficiente y modular de archivos NetCDF (.nc) de emisiones EDGAR.
=============================================================================================
Este módulo extrae estadísticas zonales (media, mediana, min, max, suma) a nivel municipal
en Honduras a partir de rasters NetCDF globales de emisiones EDGAR (ej. sector POWER_INDUSTRY),
optimizando el uso de memoria RAM mediante recorte espacial previo, procesamiento año por año
y escritura incremental (appending) en archivos CSV.

Comandos para entorno Miniforge / Conda:
----------------------------------------
    conda activate spatial
    conda install -c conda-forge -y netcdf4 h5netcdf rioxarray rasterio rasterstats geopandas fiona
"""

from pathlib import Path
import os
import sys
import gc
import time
import re
from typing import List, Dict, Optional, Tuple, Union

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
from rasterstats import zonal_stats
from rasterio.transform import from_origin


# Mapeo estándar de columnas de la capa de límites administrativos
COLUMN_MAPPING_ADMIN2 = {
    "adm1_name": "departamento",
    "adm2_name": "municipio",
    "adm1_pcode": "codigo_departamental",
    "adm2_pcode": "codigo_municipal"
}


def load_and_prepare_boundaries(
    gdb_path: Union[str, Path],
    layer_name: str = "hnd_admin2",
    target_crs: str = "EPSG:4326"
) -> Tuple[gpd.GeoDataFrame, Tuple[float, float, float, float]]:
    """
    Carga y estandariza la capa de límites municipales desde una Geodatabase (GDB).

    Parámetros
    ----------
    gdb_path : str o Path
        Ruta al archivo .gdb de límites administrativos.
    layer_name : str, opcional
        Nombre de la capa municipal dentro del GDB (por defecto "hnd_admin2").
    target_crs : str, opcional
        Sistema de referencia de coordenadas objetivo (por defecto "EPSG:4326").

    Retorna
    -------
    gdf : gpd.GeoDataFrame
        GeoDataFrame con columnas limpias ('departamento', 'municipio',
        'codigo_departamental', 'codigo_municipal', 'geometry').
    bbox : tuple (minx, miny, maxx, maxy)
        Límites geográficos totales de Honduras.
    """
    gdb_path = Path(gdb_path)
    if not gdb_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo GDB en: {gdb_path}")

    gdf = gpd.read_file(gdb_path, layer=layer_name)

    # Asegurar el sistema de coordenadas
    if gdf.crs is None:
        gdf.set_crs(target_crs, inplace=True)
    elif str(gdf.crs).upper() != target_crs.upper():
        gdf = gdf.to_crs(target_crs)

    # Filtrar y renombrar columnas relevantes
    available_cols = [c for c in COLUMN_MAPPING_ADMIN2.keys() if c in gdf.columns]
    gdf_clean = gdf[available_cols + ["geometry"]].copy()
    gdf_clean.rename(columns=COLUMN_MAPPING_ADMIN2, inplace=True)

    # Normalizar formato de texto (quitar espacios redundantes y capitalizar)
    for col in ["departamento", "municipio"]:
        if col in gdf_clean.columns:
            gdf_clean[col] = (
                gdf_clean[col]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
                .str.title()
            )

    for col in ["codigo_departamental", "codigo_municipal"]:
        if col in gdf_clean.columns:
            gdf_clean[col] = gdf_clean[col].astype(str).str.strip()

    bbox = tuple(gdf_clean.total_bounds)  # (minx, miny, maxx, maxy)
    return gdf_clean, bbox


def extract_spatial_slice_and_affine(
    ds: xr.Dataset,
    bbox: Tuple[float, float, float, float],
    buffer: float = 0.2
) -> Tuple[xr.Dataset, object]:
    """
    Recorta el dataset global NetCDF al bounding box de Honduras con un buffer,
    y construye la transformación afín correspondiente para rasterstats.

    Parámetros
    ----------
    ds : xr.Dataset
        Dataset global abierto con xarray.
    bbox : tuple (minx, miny, maxx, maxy)
        Límites geográficos de la región de interés.
    buffer : float, opcional
        Margen adicional en grados para asegurar cobertura completa (por defecto 0.2).

    Retorna
    -------
    ds_sliced : xr.Dataset
        Dataset recortado espacialmente.
    transform : rasterio.transform.Affine
        Matriz de transformación afín para la cuadrícula recortada.
    """
    minx, miny, maxx, maxy = bbox

    # Identificar nombres de coordenadas latitud y longitud
    lat_name = "lat" if "lat" in ds.coords else "latitude"
    lon_name = "lon" if "lon" in ds.coords else "longitude"

    # Determinar si latitud está ordenada de forma ascendente o descendente
    lat_vals = ds[lat_name].values
    if lat_vals[0] < lat_vals[-1]:
        lat_slice = slice(miny - buffer, maxy + buffer)
    else:
        lat_slice = slice(maxy + buffer, miny - buffer)

    lon_slice = slice(minx - buffer, maxx + buffer)

    ds_sliced = ds.sel({lat_name: lat_slice, lon_name: lon_slice})

    # Extraer coordenadas del recorte
    sub_lat = ds_sliced[lat_name].values
    sub_lon = ds_sliced[lon_name].values

    if len(sub_lat) < 2 or len(sub_lon) < 2:
        raise ValueError("El recorte espacial no contiene suficientes píxeles para calcular la transformación afín.")

    dlat = abs(float(sub_lat[1] - sub_lat[0]))
    dlon = abs(float(sub_lon[1] - sub_lon[0]))

    west = float(np.min(sub_lon) - dlon / 2.0)
    north = float(np.max(sub_lat) + dlat / 2.0)

    transform = from_origin(west, north, dlon, dlat)

    return ds_sliced, transform


def compute_zonal_stats_for_slice(
    data_2d: np.ndarray,
    transform: object,
    boundaries_gdf: gpd.GeoDataFrame,
    lat_ascending: bool = True,
    stats: Tuple[str, ...] = ("mean", "median", "min", "max", "sum"),
    all_touched: bool = True,
    nodata_val: float = np.nan
) -> pd.DataFrame:
    """
    Calcula estadísticas zonales para una matriz 2D sobre los polígonos municipales.

    Parámetros
    ----------
    data_2d : np.ndarray
        Matriz 2D de valores de emisión.
    transform : rasterio.transform.Affine
        Transformación afín del raster.
    boundaries_gdf : gpd.GeoDataFrame
        Límites municipales en formato GeoDataFrame.
    lat_ascending : bool, opcional
        Si True, invierte el eje 0 (flipud) para que la fila 0 corresponda al norte (convención raster).
    stats : tuple de str, opcional
        Estadísticas a calcular (ej. 'mean', 'median', 'min', 'max', 'sum').
    all_touched : bool, opcional
        Si True, incluye todos los píxeles que intersecten el polígono municipal.
    nodata_val : float, opcional
        Valor para indicar ausencia de datos.

    Retorna
    -------
    pd.DataFrame con las estadísticas asociadas a cada municipio.
    """
    # Si las latitudes en xarray son ascendentes (-90 a 90), volteamos verticalmente
    # para que la primera fila del array sea la fila superior (Norte).
    raster_array = np.flipud(data_2d) if lat_ascending else data_2d

    # Ejecutar rasterstats
    results = zonal_stats(
        vectors=boundaries_gdf,
        raster=raster_array,
        affine=transform,
        stats=list(stats),
        nodata=nodata_val,
        all_touched=all_touched
    )

    # Construir DataFrame con columnas descriptivas
    attr_cols = ["departamento", "municipio", "codigo_departamental", "codigo_municipal"]
    attr_cols = [c for c in attr_cols if c in boundaries_gdf.columns]
    
    df_out = boundaries_gdf[attr_cols].copy()
    for stat_name in stats:
        df_out[stat_name] = [r.get(stat_name, np.nan) for r in results]

    return pd.DataFrame(df_out)


def extract_nc_metadata(ds: xr.Dataset, file_path: Union[str, Path]) -> Dict[str, str]:
    """
    Extrae metadatos descriptivos (año, sustancia, sector, unidades) desde los atributos del NetCDF
    o a partir del nombre del archivo.

    Parámetros
    ----------
    ds : xr.Dataset
        Dataset xarray.
    file_path : str o Path
        Ruta del archivo .nc.

    Retorna
    -------
    dict con 'year', 'substance', 'sector', 'units'.
    """
    filename = Path(file_path).name
    attrs = ds.attrs

    # Detectar variable principal de datos
    data_vars = list(ds.data_vars.keys())
    primary_var = data_vars[0] if data_vars else None
    var_attrs = ds[primary_var].attrs if primary_var else {}

    # Extraer año (de atributos o regex en el nombre de archivo)
    year = var_attrs.get("year", attrs.get("year", ""))
    if not year:
        match = re.search(r"_(19\d\d|20\d\d)_", filename)
        if match:
            year = match.group(1)

    substance = var_attrs.get("substance", attrs.get("substance", "CO2"))
    sector = var_attrs.get("long_name", var_attrs.get("description", attrs.get("title", "Power industry")))
    units = var_attrs.get("units", attrs.get("units", "Tonnes"))

    return {
        "year": str(year),
        "substance": str(substance),
        "sector": str(sector),
        "units": str(units),
        "primary_var": primary_var
    }


def process_single_nc_file(
    file_path: Union[str, Path],
    boundaries_gdf: gpd.GeoDataFrame,
    bbox: Tuple[float, float, float, float],
    stats: Tuple[str, ...] = ("mean", "median", "min", "max", "sum"),
    all_touched: bool = True,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Abre y procesa un archivo NetCDF (.nc), calcula estadísticas zonales para cada mes
    (o período disponible), y libera explícitamente la memoria RAM.

    Parámetros
    ----------
    file_path : str o Path
        Ruta al archivo NetCDF.
    boundaries_gdf : gpd.GeoDataFrame
        Límites municipales preparados.
    bbox : tuple (minx, miny, maxx, maxy)
        Límites geográficos de Honduras.
    stats : tuple de str
        Estadísticas a calcular.
    all_touched : bool
        Precisión de intersección en rasterstats.
    verbose : bool
        Si True, imprime detalles de depuración.

    Retorna
    -------
    pd.DataFrame con los datos procesados para todos los meses del archivo.
    """
    file_path = Path(file_path)
    t0 = time.time()

    if verbose:
        print(f"  -> Abriendo: {file_path.name}...")

    # Abrir dataset
    ds = xr.open_dataset(file_path)

    try:
        metadata = extract_nc_metadata(ds, file_path)
        primary_var = metadata["primary_var"]
        if primary_var is None:
            raise ValueError(f"No se encontraron variables de datos en {file_path.name}")

        # Recorte espacial inmediato a Honduras
        ds_sliced, transform = extract_spatial_slice_and_affine(ds, bbox)

        lat_name = "lat" if "lat" in ds_sliced.coords else "latitude"
        lat_vals = ds_sliced[lat_name].values
        lat_ascending = bool(lat_vals[0] < lat_vals[-1])

        var_data = ds_sliced[primary_var]
        records_list = []

        # Determinar si el archivo tiene dimensión temporal (ej. mensual)
        has_time = "time" in var_data.dims

        if has_time:
            num_times = len(var_data["time"])
            time_coords = var_data["time"].values

            for t_idx in range(num_times):
                t_val = time_coords[t_idx]
                t_str = pd.to_datetime(t_val).strftime("%Y-%m-%d")
                month_num = pd.to_datetime(t_val).month
                year_num = pd.to_datetime(t_val).year if not metadata["year"] else int(metadata["year"])

                data_2d = var_data.isel(time=t_idx).values.astype(np.float64)

                # Calcular estadísticas zonales para el mes
                df_month = compute_zonal_stats_for_slice(
                    data_2d=data_2d,
                    transform=transform,
                    boundaries_gdf=boundaries_gdf,
                    lat_ascending=lat_ascending,
                    stats=stats,
                    all_touched=all_touched
                )

                # Agregar columnas de metadatos temporales y sectoriales
                df_month["anio"] = year_num
                df_month["mes"] = month_num
                df_month["fecha"] = t_str
                df_month["sector"] = metadata["sector"]
                df_month["sustancia"] = metadata["substance"]
                df_month["unidad"] = metadata["units"]

                records_list.append(df_month)
        else:
            # Archivo anual (sin dimensión time)
            year_num = int(metadata["year"]) if metadata["year"] else np.nan
            data_2d = var_data.values.astype(np.float64)

            df_year = compute_zonal_stats_for_slice(
                data_2d=data_2d,
                transform=transform,
                boundaries_gdf=boundaries_gdf,
                lat_ascending=lat_ascending,
                stats=stats,
                all_touched=all_touched
            )

            df_year["anio"] = year_num
            df_year["mes"] = 0
            df_year["fecha"] = f"{year_num}-01-01" if pd.notna(year_num) else ""
            df_year["sector"] = metadata["sector"]
            df_year["sustancia"] = metadata["substance"]
            df_year["unidad"] = metadata["units"]

            records_list.append(df_year)

        df_result = pd.concat(records_list, ignore_index=True)

        # Reordenar columnas para una estructura clara y limpia
        lead_cols = [
            "anio", "mes", "fecha", "codigo_departamental", "departamento",
            "codigo_municipal", "municipio"
        ]
        stat_cols = list(stats)
        trail_cols = ["sector", "sustancia", "unidad"]

        final_cols = [c for c in lead_cols if c in df_result.columns] + \
                     [c for c in stat_cols if c in df_result.columns] + \
                     [c for c in trail_cols if c in df_result.columns]

        df_result = df_result[final_cols]

        elapsed = time.time() - t0
        if verbose:
            print(f"  [OK] {file_path.name} procesado: {len(df_result)} registros en {elapsed:.2f} s")

        return df_result

    finally:
        # Liberación estricta de memoria
        ds.close()
        del ds
        gc.collect()


def append_records_to_csv(df: pd.DataFrame, output_csv_path: Union[str, Path]) -> None:
    """
    Escribe o agrega (append) un bloque de datos al archivo CSV de destino.

    Parámetros
    ----------
    df : pd.DataFrame
        DataFrame a escribir.
    output_csv_path : str o Path
        Ruta del archivo CSV de destino.
    """
    out_path = Path(output_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Si el archivo no existe o está vacío, escribimos el encabezado
    write_header = not out_path.exists() or out_path.stat().st_size == 0

    df.to_csv(
        out_path,
        mode="a",
        header=write_header,
        index=False,
        encoding="utf-8-sig"
    )


def process_edgar_directory(
    raw_dir: Union[str, Path],
    output_csv: Union[str, Path] = "data/Edgar/processed/edgar_power_industry_monthly.csv",
    gdb_path: Union[str, Path] = "data/boundaries/raw/hnd_admin_boundaries.gdb",
    layer_name: str = "hnd_admin2",
    stats: Tuple[str, ...] = ("mean", "median", "min", "max", "sum"),
    all_touched: bool = True,
    overwrite: bool = False,
    verbose: bool = True
) -> Path:
    """
    Función orquestadora principal para procesar una serie temporal de archivos NetCDF (.nc)
    de emisiones EDGAR y consolidarlos incrementalmente en un archivo CSV.

    Diseñada para ser ejecutada directamente desde scripts o Jupyter Notebooks.

    Parámetros
    ----------
    raw_dir : str o Path
        Directorio que contiene los archivos .nc a procesar.
    output_csv : str o Path, opcional
        Ruta del archivo CSV resultante.
    gdb_path : str o Path, opcional
        Ruta al Geodatabase de límites administrativos de Honduras.
    layer_name : str, opcional
        Nombre de la capa municipal (por defecto "hnd_admin2").
    stats : tuple de str, opcional
        Estadísticas zonales a calcular (por defecto 'mean', 'median', 'min', 'max', 'sum').
    all_touched : bool, opcional
        Si True, incluye píxeles que toquen el límite municipal.
    overwrite : bool, opcional
        Si True, sobreescribe el CSV de salida si ya existe. Si False, continúa agregando o respeta el existente.
    verbose : bool, opcional
        Si True, muestra mensajes de depuración detallados con tiempos y avance.

    Retorna
    -------
    Path
        Ruta del archivo CSV consolidado generado.
    """
    raw_path = Path(raw_dir)
    out_csv = Path(output_csv)
    gdb_file = Path(gdb_path)

    if not raw_path.exists() or not raw_path.is_dir():
        raise NotADirectoryError(f"El directorio especificado no existe: {raw_path}")

    # Encontrar y ordenar archivos .nc
    nc_files = sorted(list(raw_path.glob("*.nc")))
    if not nc_files:
        raise FileNotFoundError(f"No se encontraron archivos .nc en: {raw_path}")

    if verbose:
        print("=" * 70)
        print(" INICIANDO PROCESAMIENTO DE EMISIONES EDGAR (.nc)")
        print("=" * 70)
        print(f"  Directorio de entrada:  {raw_path}")
        print(f"  Archivos encontrados:   {len(nc_files)} archivos .nc")
        print(f"  Capa de municipios:     {gdb_file} [{layer_name}]")
        print(f"  Archivo CSV de salida:  {out_csv}")
        print(f"  Estadísticas zonales:   {list(stats)}")
        print(f"  all_touched:            {all_touched}")
        print("-" * 70)

    # Manejo de sobreescritura
    if overwrite and out_csv.exists():
        if verbose:
            print(f"  [AVISO] Eliminando archivo previo para reiniciar: {out_csv}")
        out_csv.unlink()

    # 1. Cargar límites administrativos
    if verbose:
        print("  [1/2] Cargando y preparando capas de límites municipales...")
    boundaries_gdf, bbox = load_and_prepare_boundaries(gdb_file, layer_name=layer_name)
    num_munis = len(boundaries_gdf)
    if verbose:
        print(f"        -> {num_munis} municipios cargados exitosamente.")
        print(f"        -> Bounding box Honduras: {bbox}")
        print("  [2/2] Procesando archivos NetCDF año por año...")

    total_records = 0
    start_total_time = time.time()

    # 2. Iterar por archivo .nc
    for idx, file_nc in enumerate(nc_files, start=1):
        if verbose:
            print(f"\n[{idx}/{len(nc_files)}] Procesando {file_nc.name}...")

        try:
            df_year = process_single_nc_file(
                file_path=file_nc,
                boundaries_gdf=boundaries_gdf,
                bbox=bbox,
                stats=stats,
                all_touched=all_touched,
                verbose=verbose
            )

            # Escribir incrementalmente al CSV
            append_records_to_csv(df_year, out_csv)
            total_records += len(df_year)

        except Exception as e:
            print(f"  [ERROR] Falló el procesamiento de {file_nc.name}: {e}", file=sys.stderr)
            raise

    total_elapsed = time.time() - start_total_time
    if verbose:
        print("\n" + "=" * 70)
        print(" PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"  Total archivos procesados: {len(nc_files)}")
        print(f"  Total registros escritos:  {total_records:,}")
        print(f"  Tiempo total transcurrido: {total_elapsed:.2f} segundos")
        print(f"  Archivo guardado en:       {out_csv.resolve()}")
        print("=" * 70)

    return out_csv
