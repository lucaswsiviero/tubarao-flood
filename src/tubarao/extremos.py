"""Estatistica de valores extremos (GEV por momentos-L) e tempo de retorno.

Convencao de Hosking (1990): F(x) = exp(-(1 - k (x - xi)/a)^(1/k)).
k < 0  -> cauda pesada (sem limite superior); k > 0 -> cauda limitada.
So depende de numpy e pandas.
"""
from __future__ import annotations

from math import gamma

import numpy as np
import pandas as pd


def maximos_anuais(df: pd.DataFrame, min_dias: int = 300, excluir=()) -> pd.Series:
    """Maximo anual de df (colunas data, valor), so de anos com >= min_dias dias de dado."""
    g = df.groupby(df.data.dt.year)
    tam = g.size()
    ok = (tam >= min_dias) & (~tam.index.isin(list(excluir)))
    return g.valor.max()[ok]


def momentos_l(x):
    """Primeiros momentos-L amostrais: (l1, l2, t3 = l3/l2)."""
    x = np.sort(np.asarray(x, float))
    n = len(x)
    j = np.arange(1, n + 1)
    b0 = x.mean()
    b1 = np.sum((j - 1) / (n - 1) * x) / n
    b2 = np.sum((j - 1) * (j - 2) / ((n - 1) * (n - 2)) * x) / n
    l1, l2, l3 = b0, 2 * b1 - b0, 6 * b2 - 6 * b1 + b0
    return l1, l2, l3 / l2


def gev_ajusta(x, k_lim: float = 0.4):
    """Ajusta a GEV por momentos-L, com a forma k limitada a [-k_lim, k_lim]. Retorna (xi, a, k)."""
    l1, l2, t3 = momentos_l(x)
    c = 2 / (3 + t3) - np.log(2) / np.log(3)
    k = float(np.clip(7.8590 * c + 2.9554 * c ** 2, -k_lim, k_lim))
    if abs(k) < 1e-6:
        a = l2 / np.log(2)
        xi = l1 - 0.5772156649 * a
    else:
        a = l2 * k / ((1 - 2 ** (-k)) * gamma(1 + k))
        xi = l1 + a * (gamma(1 + k) - 1) / k
    return xi, a, k


def gev_nivel(T, par):
    """Valor associado ao tempo de retorno T (anos)."""
    xi, a, k = par
    y = -np.log(1 - 1 / np.asarray(T, float))
    return xi - a * np.log(y) if abs(k) < 1e-6 else xi + a / k * (1 - y ** k)


def gev_cdf(x, par):
    """Funcao de distribuicao acumulada (aceita escalar ou array)."""
    xi, a, k = par
    x = np.asarray(x, float)
    if abs(k) < 1e-6:
        out = np.exp(-np.exp(-(x - xi) / a))
    else:
        y = 1 - k * (x - xi) / a
        pos = y > 0
        with np.errstate(over="ignore", invalid="ignore"):
            out = np.where(pos, np.exp(-np.power(np.where(pos, y, 1.0), 1 / k)), 1.0 if k > 0 else 0.0)
    return float(out) if out.ndim == 0 else out


def tr_de_valores(x, par, tr_max: float = 1e5):
    """Tempo de retorno (anos) equivalente de cada valor em x, segundo a GEV ajustada."""
    p = 1 - gev_cdf(x, par)
    with np.errstate(divide="ignore"):
        tr = 1 / np.maximum(p, 1 / tr_max)
    return np.where(np.isnan(np.asarray(x, float)), np.nan, tr)


def ajusta_gev(x, trs=(2, 5, 10, 25, 50, 100), n_boot: int = 1000, seed: int = 0):
    """Ajuste + intervalo de confianca de 90% por bootstrap. Retorna (par, tabela)."""
    x = np.asarray(x, float)
    par = gev_ajusta(x)
    rng = np.random.default_rng(seed)
    boots = np.array([gev_nivel(trs, gev_ajusta(rng.choice(x, size=len(x), replace=True)))
                      for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [5, 95], axis=0)
    tab = pd.DataFrame({"TR (anos)": trs, "estimado": gev_nivel(trs, par),
                        "IC90% inf": lo, "IC90% sup": hi})
    return par, tab
