"""Estacoes-chave da bacia do Rio Tubarao e carregamento (com cache) das series da ANA."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import ana

# nome legivel: (codigo ANA, tipo)
ALVOS = {
    "Tubarão · cota":                 ("84580500", "cota"),
    "Pedras Grandes · vazão":         ("84300000", "vazao"),
    "Pedras Grandes · cota":          ("84300000", "cota"),
    "Orleans II · vazão":             ("84250000", "vazao"),
    "Armazém (Capivari) · vazão":     ("84600000", "vazao"),
    "Gravatal (Capivari) · vazão":    ("84610000", "vazao"),
    "São Ludgero (B. Norte) · vazão": ("84560000", "vazao"),
    "Chuva Tubarão":                  ("2849027", "chuva"),
    "Chuva Pedras Grandes":           ("2849028", "chuva"),
    "Chuva Orleans":                  ("2849093", "chuva"),
    "Chuva Braço do Norte":           ("2849030", "chuva"),
    "Chuva Armazém":                  ("2848000", "chuva"),
}

VAZOES = [n for n in ALVOS if n.endswith("vazão")]
CHUVAS = [n for n in ALVOS if n.startswith("Chuva")]


def carregar(cod: str, tipo: str, data_dir: Path, forcar: bool = False) -> pd.DataFrame:
    """Le do cache (parquet) ou baixa da ANA e grava no cache."""
    arq = Path(data_dir) / "raw" / f"{cod}_{tipo}.parquet"
    if arq.exists() and not forcar:
        return pd.read_parquet(arq)
    df = ana.serie_diaria(cod, tipo)
    if not df.empty:
        arq.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(arq)
    return df


def carregar_todos(data_dir: Path, verbose: bool = True) -> dict[str, pd.DataFrame]:
    """Carrega todas as ALVOS que tiverem dados. Estacoes vazias sao ignoradas."""
    series = {}
    for nome, (cod, tipo) in ALVOS.items():
        df = carregar(cod, tipo, data_dir)
        if df.empty:
            if verbose:
                print(f"⚠️  {nome} ({cod}): sem dados, ignorada")
            continue
        series[nome] = df
        if verbose:
            print(f"✔ {nome:32s} {cod}  {df.data.min().date()} → {df.data.max().date()}  ({len(df):,} dias)")
    return series
