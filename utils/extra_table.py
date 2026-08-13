import camelot
import pandas as pd

tables = camelot.read_pdf(
    "output/ICAEH-2022-extract.pdf",
    pages="all",
    flavor="lattice",
)

print(f"Found {tables.n} tables")

dfs = []

for table in tables:
    df = table.df

    # Remove repeated header rows
    df = df[~df.apply(lambda row: row.astype(str).str.contains('DEPARTAMENTO').any(), axis=1)]

    dfs.append(df)

result = pd.concat(dfs, ignore_index=True)

result.columns = [
    "DEPARTAMENTO",
    "MUNICIPIO",
    "VIVIENDAS",
    "COBERTURA",
    "ICE",
    "IAE",
]

result.to_csv("ICAEH_2022.csv", index=False)