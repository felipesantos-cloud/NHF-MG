# Dados NetCDF

Organize os arquivos assim:

```text
data/
├── Tmax/
│   ├── arquivo_01.nc
│   ├── arquivo_02.nc
│   └── ...
└── Tmin/
    ├── arquivo_01.nc
    ├── arquivo_02.nc
    └── ...
```

O aplicativo usa `xarray.open_mfdataset(..., combine="by_coords")`, então os arquivos devem possuir coordenadas compatíveis e uma dimensão temporal combinável.

## Variáveis

O app tenta identificar automaticamente a primeira variável de dados de cada conjunto, ignorando:

- `crs`
- `spatial_ref`
- `time_bnds`
- `lat_bnds`
- `lon_bnds`

As coordenadas aceitas são `latitude`/`longitude` ou `lat`/`lon`.

## Outra pasta de dados

Você pode apontar o site para outra localização sem editar o código:

```bash
export NHF_DATA_DIR=/caminho/para/dados
streamlit run app.py
```

A pasta indicada deve conter as subpastas `Tmax` e `Tmin`.
