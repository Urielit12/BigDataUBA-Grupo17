from math import log as ln
import os
from csv import reader, writer
import numpy as np
import wbdata
import pandas as pd
import matplotlib.pyplot as plt


def limpieza():
    dfs_lim = {}
    for año in range(2015, 2025):
        sheet_name = str(año)
        df = pd.read_excel(
            "OCUP_I_03.xlsx", sheet_name=sheet_name, header=2)
        print(
            f"El año {año} tiene {len(df.columns)} columnas previas")
        df = df.iloc[:19]
        df.index = df['Unnamed: 0']
        df.index = df.index.rename('Mediciones')
        df = df.loc[:, ~df.columns.str.contains("Unnamed")]
        nombres_base = ['Total', 'Varon',
                        'Mujer', 'Distribucion Porcentual']
        if sheet_name == "2024":
            trimestres = ['T1', 'T2', 'T3']
        else:
            trimestres = ['T1', 'T2', 'T3', 'T4']
        nuevos_nombres = [
            f"{nombre}{trim}" for trim in trimestres for nombre in nombres_base]
        df.columns = nuevos_nombres
        df = df.fillna("")
        df = df.apply(pd.to_numeric, errors='coerce').round(2)
        dfs_lim[año] = df
        df.to_excel(f"ExpoOral{año}.xlsx", index=True)
        print(
            f'El año {año} ahora tiene {len(df.columns)} columnas y ha sido limpiado.')

    return dfs_lim


def juntar_fila(row_name, dfs_dict):
    filas = []
    for año, df in dfs_dict.items():
        if row_name in df.index:
            fila = df.loc[row_name].copy()
            fila.name = año
            filas.append(fila)
        else:
            print(f"El año {año} no contiene la fila '{row_name}'")
    resultado = pd.DataFrame(filas)
    resultado.to_excel(f"Servicios.xlsx", index=True)
    return resultado


dfs_lim = limpieza()
datos_servicios = juntar_fila("Servicios", dfs_lim)


def ajuste_dolar():
    df = pd.read_csv("tipos-de-cambio-historicos.csv")
    df = df.set_index('indice_tiempo')
    df.index = pd.to_datetime(df.index)
    df.index.name = "Fecha"
    df = df.fillna("")
    df = df.loc['2015-01-01':'2024-12-31']
    df = df[['dolar_estadounidense']]
    df = df.rename(columns={'dolar_estadounidense': 'Dolar_oficial'})
    df_trimestres = df.resample('QE').last().round(2)
    df_trimestres = df_trimestres.transpose()
    df_trimestres.to_excel(f"DolarOficial.xlsx", index=True)

    return df_trimestres


df = pd.read_excel(
    "Servicios.xlsx")
df.columns = df.columns.astype(str)
df = df.drop(df.columns[df.columns.str.contains("Porcen")], axis=1)
df.index = df['Unnamed: 0']
df = df.drop(['Unnamed: 0'], axis=1)
df.index.name = 'Años'
df = df.fillna('1')
df.to_excel(f"ServiciosDolar.xlsx", index=True)


def limpieza_dolar():
    valoresdolar = []
    df_total = pd.DataFrame()
    for año in range(2015, 2025):
        df_dolar = pd.read_excel("DolarOficial.xlsx")
        df_dolar.columns = df_dolar.columns.astype(str)
        df_dolar = df_dolar.drop(
            df_dolar.columns[~df_dolar.columns.str.contains(f'{año}')], axis=1)
        df_dolar_cnombres = ['T1', 'T2', 'T3', 'T4']
        df_dolar.index = [f'{año}']
        df_dolar.columns = df_dolar_cnombres
        print(df_dolar)
        df_dolar.to_excel(f"DolarValor{año}.xlsx", index=True)
        df_total = pd.concat([df_total, df_dolar])
        valoresdolar.append(df_dolar.iloc[0].tolist())
    df_total.to_excel("DolarValorTrimestres.xlsx", index=True)
    return valoresdolar


df_dolar = pd.read_excel("DolarValorTrimestres.xlsx", index_col=0).round(2)
df_servicios = pd.read_excel("ServiciosDolar.xlsx", index_col=0).astype(int)
df_dolar_ajustado = pd.concat([df_dolar[['T1']], df_dolar[['T1']], df_dolar[['T1']],
                               df_dolar[['T2']], df_dolar[[
                                   'T2']], df_dolar[['T2']],
                               df_dolar[['T3']], df_dolar[['T3']], df_dolar[['T3']], df_dolar[['T4']], df_dolar[['T4']], df_dolar[['T4']]],
                              axis=1)

nombres = df.columns
df_dolar_ajustado.columns = nombres
df_unido = pd.concat([df_servicios, df_dolar_ajustado])

df_unido = (df_servicios / df_dolar_ajustado).round(2)
df_unido.to_excel("archivo_unido.xlsx")

df_unido = df_unido.reset_index()
print(df_unido)

x1 = df_unido['Años']
y1 = df_unido['TotalT1']
x2 = df_unido['Años']
y2 = df_unido['VaronT1']
x3 = df_unido['Años']
y3 = df_unido['MujerT1']

plt.plot(x1, y1, color='grey', label="Total T1")
plt.plot(x2, y2, color='blue', label="Masculino T1")
plt.plot(x3, y3, color='red', label="Femenino")

plt.xlabel("Años")
plt.ylabel("Ingreso Promedio (En dólares)")
plt.title('Ingreso promedio en el área de servicios en dólares (Oficial)')

plt.legend()
plt.show()
