import requests
import pandas as pd


GBIF_URL = "https://api.gbif.org/v1/occurrence/search"


def gbif_occurrence_search(wkt, limit=300, offset=0, **kwargs):
    """
    Query GBIF occurrence/search using a WKT geometry.
    """

    params = {
        "geometry": wkt,
        "limit": limit,
        "offset": offset,
        **kwargs
    }

    response = requests.get(
        GBIF_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def gbif_fetch_all(
    wkt,
    page_size=300,
    max_records=None,
    **kwargs
):
    """
    Retrieve GBIF occurrence records using pagination.

    Parameters
    ----------
    wkt : str
        Polygon or MultiPolygon in WKT format.

    page_size : int
        Number of records per API request.

    max_records : int or None
        Maximum number of records to retrieve.
        None means retrieve all available records.

    **kwargs
        Additional GBIF API filters.
    """

    records = []
    offset = 0

    while True:

        data = gbif_occurrence_search(
            wkt=wkt,
            limit=page_size,
            offset=offset,
            **kwargs
        )

        results = data.get("results", [])

        if not results:
            break

        records.extend(results)

        total = data.get("count", 0)

        print(
            f"Downloaded {len(records):,} / "
            f"{total:,} records"
        )

        # Stop if we reached the requested limit
        if max_records is not None:
            if len(records) >= max_records:
                records = records[:max_records]
                break

        # Stop if there are no more records
        if len(results) < page_size:
            break

        offset += page_size

    return records


def gbif_to_dataframe(records):
    """
    Convert GBIF occurrence records to a pandas DataFrame.
    """

    if not records:
        return pd.DataFrame()

    df = pd.json_normalize(records)

    return df


def gbif_to_csv(
    records,
    output_path,
    index=False
):
    """
    Store GBIF occurrence records as CSV.
    """

    df = gbif_to_dataframe(records)

    if df.empty:
        print("No GBIF records found.")
        return df

    df.to_csv(
        output_path,
        index=index,
        encoding="utf-8"
    )

    print(
        f"Saved {len(df):,} records to {output_path}"
    )

    return df


