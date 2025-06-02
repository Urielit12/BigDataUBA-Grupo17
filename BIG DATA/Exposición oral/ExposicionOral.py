import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Creamos una función que limpia automaticamente cada año de la base de datos, eliminando columnas vacias y dejando solamente las importantes.os.


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
            # El año 2024 tiene solamente 3 Trimestres cargados, así que usamos solo 3 columnas para dicho año.
            trimestres = ['T1', 'T2', 'T3']
        else:
            trimestres = ['T1', 'T2', 'T3', 'T4']
        nuevos_nombres = [
            f"{nombre}{trim}" for trim in trimestres for nombre in nombres_base]
        df.columns = nuevos_nombres
        df = df.fillna("")
        df = df.apply(pd.to_numeric, errors='coerce').round(2)
        dfs_lim[año] = df
        print(
            f'El año {año} ahora tiene {len(df.columns)} columnas y ha sido limpiado.')

    return dfs_lim

# Creamos una funcion que itera en cada fila de servicios de todos los años, y las junta en un solo archivo de excel.


def juntar_varias_filas(row_names, dfs_dict):
    resultados = {}
    for row_name in row_names:
        filas = []
        for año, df in dfs_dict.items():
            if row_name in df.index:
                fila = df.loc[row_name].copy()
                fila.name = año
                filas.append(fila)
            else:
                print(f"El año {año} no contiene la fila '{row_name}'")
        if filas:
            # Reemplaza caracteres no válidos para nombres de archivo
            safe_name = row_name.replace("/", "-").replace(" ", "_")
            resultados[safe_name] = pd.DataFrame(filas)
            print(f"Fila '{safe_name}' aislada.")
        else:
            print(f"No se encontró la fila '{row_name}'")
    return resultados


# Cargamos una base de datos auxiliar, que es el valor del dolar oficial para cada día desde 1970.
# Limpiamos los datos así me devuelve el valor por cuatrimestre


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
    # La base de datos previamente limpiada del Dólar Oficial, la ordenamos por año, así comparte cant. de filas y nombre de índices con la ramaa elegir.

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
            df_total = pd.concat([df_total, df_dolar])
            valoresdolar.append(df_dolar.iloc[0].tolist())
        df_total.to_excel("DolarValorTrimestres.xlsx", index=True)
        return valoresdolar
    limpieza_dolar()

# Del excel de la rama, limpiamos para que solamente me diga el ingreso promedio. Y llenamos los NaN con un valor.


def ajuste_rama(datos_rama):
    # Traemos la base de datos del dolar.
    df_dolar = pd.read_excel("DolarValorTrimestres.xlsx", index_col=0).round(2)
    resultados = {}
    for rama, df in datos_rama.items():
        df = df.copy()
        df.columns = df.columns.astype(str)
        df = df.drop(df.columns[df.columns.str.contains("Porcen")], axis=1)
        df.index.name = 'Años'
        df = df.fillna('1')
        df = df.astype(int)
        # Repetimos columnas así hay misma cantidad de filas y columnas en ambos archivos excel.
        df_dolar_ajustado = pd.concat([df_dolar[['T1']], df_dolar[['T1']], df_dolar[['T1']],
                                       df_dolar[['T2']], df_dolar[[
                                           'T2']], df_dolar[['T2']],
                                       df_dolar[['T3']], df_dolar[['T3']], df_dolar[['T3']], df_dolar[['T4']], df_dolar[['T4']], df_dolar[['T4']]],
                                      axis=1)
        # Dividimos los ingresos por el dólar
        nombres = df.columns
        df_dolar_ajustado.columns = nombres
        df_ajustado = (df / df_dolar_ajustado).round(2)
        # Guardamos resultado
        df_ajustado = df_ajustado.reset_index()
        nombre_archivo = f"{rama}_AJ_DOLAR.xlsx"
        df_ajustado.to_excel(nombre_archivo, index=False)

        resultados[rama] = df_ajustado

    return resultados


def graficos(df_unido, nombre_rama):
    x = df_unido['Años']
    plt.plot(x, df_unido['TotalT1'], color='grey', label="Total T1")
    plt.plot(x, df_unido['VaronT1'], color='blue', label="Masculino T1")
    plt.plot(x, df_unido['MujerT1'], color='red', label="Femenino T1")

    if nombre_rama == 'Alta_calificación_(profesional_y_técnica)':
        titulo = 'Ingreso promedio de individuos de alta calificación'
    elif nombre_rama == 'Baja_calificación_(operativa_y_no_calificada)_':
        titulo = 'Ingreso promedio de individuos de baja calificación'
    else:
        titulo = f'Ingreso promedio en el área de {nombre_rama.replace("_", " ")}'
    plt.xlabel("Años")
    plt.ylabel("Ingreso promedio en Dólares (Valor Oficial)")
    plt.title(
        f'{titulo}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def horas_trab(limpiado):
    horas = []
    df_total = pd.DataFrame()
    for año, df in limpiado.items():
        df.index.name = año
        df = df.loc[df.index.str.contains("Horas")]
        df = df.drop(df.columns[df.columns.str.contains("Porcen")], axis=1)
        if año == 2024:
            trimestres = ['T1_Total', 'T1_Varon', 'T1_Mujer',
                          'T2_Total', 'T2_Varon', 'T2_Mujer',
                          'T3_Total', 'T3_Varon', 'T3_Mujer']

        else:
            trimestres = ['T1_Total', 'T1_Varon', 'T1_Mujer',
                          'T2_Total', 'T2_Varon', 'T2_Mujer',
                          'T3_Total', 'T3_Varon', 'T3_Mujer', 'T4_Total', 'T4_Varon', 'T4_Mujer']
        df.index = ({año})
        df.index.name = 'Años'
        df.columns = trimestres
        df_total = pd.concat([df_total, df])
        horas.append(df.iloc[0].tolist())
    df_total = df_total.apply(pd.to_numeric, errors='coerce').fillna(1)
    df_total.columns = ['TotalT1', 'VaronT1', 'MujerT1', 'TotalT2', 'VaronT2',
                        'MujerT2', 'TotalT3', 'VaronT3', 'MujerT3', 'TotalT4', 'VaronT4', 'MujerT4']
    df_total.to_excel("HorasTrimestres.xlsx", index=True)
    return df_total


def correcion_horas(horas, ramas):
    df_corregidos = {}
    horas = horas.apply(pd.to_numeric, errors='coerce')
    for nombre_rama, df_rama in ramas.items():
        df_rama.index = df_rama['Años']
        print(df_rama)
        print(horas)
        df_corregidos[nombre_rama] = (df_rama / horas)
        df_corregidos[nombre_rama] = df_corregidos[nombre_rama]
        print(df_corregidos[nombre_rama])

    return df_corregidos

# Ejecutamos la limpieza y elegimos las filas a limpiar.
dfs_lim = limpieza()
filas_a_juntar = ["Servicios", "Industria y construcción", "Comercio",
                  "Alta calificación (profesional y técnica)", "Baja calificación (operativa y no calificada) "]
datos_ramas = juntar_varias_filas(filas_a_juntar, dfs_lim)

# Ajusta la base de dolar para que quede con iguales columnas y filas.
ajuste_dolar()

# Ajusta las ramas elegidas por el dolar oficial.
ajustados = ajuste_rama(datos_ramas)

# Deja listo las filas de horas trabajadas por año para ser concatenadas.
horas_df = horas_trab(dfs_lim)

# Concatena las horas trabajadas en un solo dataframe.
correc_horas_dict = correcion_horas(horas_df, ajustados)

for nombre, df in correc_horas_dict.items():
    graficos(df, nombre)
