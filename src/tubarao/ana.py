"""Acesso aos dados hidrologicos da ANA (servico HidroWeb legado, sem login).

Funcoes principais:
    inventario(tipo, estado)  -> DataFrame com as estacoes
    serie_diaria(codigo, tipo) -> DataFrame diario (data, valor, consistencia, status)

Observacao: este e o servico SOAP/HTTP "ServiceANA.asmx", ainda ativo em 2026 e
que nao exige cadastro. A API nova (HidroWebService) exige credenciais pedidas
por e-mail a ANA. Se o servico legado sair do ar, trocar apenas este modulo.
"""
from __future__ import annotations

import io
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests

BASE = "https://telemetriaws1.ana.gov.br/ServiceANA.asmx"

# tipoDados do servico: 1 = cotas (cm), 2 = chuvas (mm), 3 = vazoes (m3/s)
TIPOS = {"cota": (1, "Cota"), "chuva": (2, "Chuva"), "vazao": (3, "Vazao")}


def _get(endpoint: str, params: dict, tentativas: int = 4, timeout: int = 180) -> bytes:
    """GET com tentativas, porque o servidor da ANA oscila."""
    ultimo = None
    for i in range(tentativas):
        try:
            r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=timeout)
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:  # noqa: PERF203
            ultimo = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"Falha ao consultar {endpoint}: {ultimo}")


def _tag(el: ET.Element) -> str:
    """Nome do elemento sem namespace."""
    return el.tag.rsplit("}", 1)[-1]


def inventario(tipo: str = "fluviometrica", estado: str = "SANTA CATARINA") -> pd.DataFrame:
    """Lista as estacoes de um estado. tipo: 'fluviometrica' ou 'pluviometrica'."""
    tp = {"fluviometrica": 1, "pluviometrica": 2}[tipo]
    params = dict(codEstDE="", codEstATE="", tpEst=tp, nmEst="", nmRio="", codSubBacia="",
                  codBacia="", nmMunicipio="", nmEstado=estado, sgResp="", sgOper="",
                  telemetrica="")
    raiz = ET.fromstring(_get("HidroInventario", params))
    linhas = []
    for el in raiz.iter():
        if _tag(el) == "Table":
            linhas.append({_tag(c): (c.text or "").strip() for c in el})
    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    for c in ("Latitude", "Longitude", "Altitude", "AreaDrenagem"):
        if c in df:
            df[c] = pd.to_numeric(df[c].str.replace(",", "."), errors="coerce")
    df["tipo"] = tipo
    return df


def serie_diaria(codigo: str, tipo: str, consistencia: str = "melhor") -> pd.DataFrame:
    """Baixa a serie diaria de uma estacao.

    tipo: 'cota' | 'chuva' | 'vazao'.
    consistencia: 'melhor' (usa o dado consistido, nivel 2, quando existe; senao o bruto),
                  'bruto' ou 'consistido'.
    Retorna colunas: data, valor, consistencia, status.
    """
    cod_tipo, prefixo = TIPOS[tipo]
    conteudo = _get("HidroSerieHistorica", dict(
        codEstacao=codigo, dataInicio="", dataFim="", tipoDados=cod_tipo, nivelConsistencia=""))
    raiz = ET.fromstring(conteudo)
    linhas = []
    for el in raiz.iter():
        if _tag(el) != "SerieHistorica":
            continue
        campos = {_tag(c): (c.text or "").strip() for c in el}
        mes = pd.to_datetime(campos.get("DataHora"), errors="coerce")
        if pd.isna(mes):
            continue
        mes = mes.to_period("M").to_timestamp()
        nivel = int(campos.get("NivelConsistencia") or 0)
        for d in range(1, 32):
            bruto = campos.get(f"{prefixo}{d:02d}", "")
            if bruto == "":
                continue
            try:
                data = mes + pd.Timedelta(days=d - 1)
                if data.month != mes.month:  # dia que nao existe (ex.: 31 de abril)
                    continue
                linhas.append((data, float(bruto), nivel, campos.get(f"{prefixo}{d:02d}Status", "")))
            except ValueError:
                continue
    df = pd.DataFrame(linhas, columns=["data", "valor", "consistencia", "status"])
    if df.empty:
        return df
    if consistencia == "bruto":
        df = df[df.consistencia == 1]
    elif consistencia == "consistido":
        df = df[df.consistencia == 2]
    # 'melhor': para cada dia, preferir o maior nivel de consistencia
    df = (df.sort_values(["data", "consistencia"])
            .drop_duplicates("data", keep="last")
            .reset_index(drop=True))
    return df


def cobertura_anual(df: pd.DataFrame) -> pd.Series:
    """Numero de dias com dado por ano (para avaliar falhas)."""
    return df.groupby(df.data.dt.year).size()
