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
    # Convertimos horas semanales a mensuales (multiplicar por 4.33 semanas/mes)
    horas_mensuales = horas * 4.33
    horas_mensuales = horas_mensuales.apply(pd.to_numeric, errors='coerce')

    for nombre_rama, df_rama in ramas.items():
        df_rama.index = df_rama['Años']
        df_rama = df_rama.drop(columns='Años')
        # Calculamos salario por hora dividiendo por horas mensuales
        df_salario_por_hora = (df_rama / horas_mensuales)
        # Ajustamos a un número fijo de horas mensuales (usamos el promedio de horas totales por trimestre)
        horas_referencia = horas_mensuales[[
            col for col in horas_mensuales.columns if 'Total' in col]].mean(axis=1)
        df_corregidos[nombre_rama] = pd.DataFrame()
        for col in df_salario_por_hora.columns:
            if 'Total' in col:
                df_corregidos[nombre_rama][col] = df_salario_por_hora[col] * \
                    horas_referencia
            elif 'Varon' in col:
                df_corregidos[nombre_rama][col] = df_salario_por_hora[col] * \
                    horas_referencia
            elif 'Mujer' in col:
                df_corregidos[nombre_rama][col] = df_salario_por_hora[col] * \
                    horas_referencia
        df_corregidos[nombre_rama] = df_corregidos[nombre_rama].reset_index()
        print(f'Rama evaluada: {nombre_rama}')
        print(df_corregidos[nombre_rama])

    return df_corregidos


def graficos_hora(df_unido, nombre_rama):
    x = df_unido['Años']
    plt.plot(x, df_unido['TotalT3'], color='grey',
             label="Total T3", linestyle='dashed')
    plt.plot(x, df_unido['VaronT3'], color='black',
             label="Masculino T3", marker='o', markersize=4)
    plt.plot(x, df_unido['MujerT3'], color='#edbc1c',
             label="Femenino T3", marker='o', markersize=4)
    if nombre_rama == 'Alta_calificación_(profesional_y_técnica)':
        titulo = 'Individuos de alta calificación'
    elif nombre_rama == 'Baja_calificación_(operativa_y_no_calificada)_':
        titulo = 'Individuos de baja calificación'
    else:
        titulo = f'Área de {nombre_rama.replace("_", " ")}'

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xlabel("Tercer Trimestre de cada Año")
    plt.ylabel("Ingreso Mensual Promedio en Dólares (Valor Oficial)")
    plt.xticks(np.arange(2015, 2025, 1))
    plt.title(
        f'{titulo}')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def gap_areas_graf(area):
    dataframes = {}
    df_total = pd.DataFrame()
    for rama, df in area.items():
        if 'Calif' in rama:
            pass
        else:
            df.index = df['Años']
            rama = rama.replace("_", " ")
            df[f'GapT3{rama}'] = df['MujerT3'] - df['VaronT3']
            dataframes[rama] = df[[f'GapT3{rama}']]
            print(df[f'GapT3{rama}'])
    df_total = pd.concat(dataframes.values(), axis=1).reset_index()

    gap_columns = [col for col in df_total.columns if col.startswith('GapT3')]
    df_total['PromedioGap'] = df_total[gap_columns].mean(axis=1)
    prom_gap = (df_total['PromedioGap']).mean()
    prom_gap_serv = (df_total['GapT3Servicios']).mean()
    print(f'El gap mensual promedio es {prom_gap}.')

    x = df_total['Años']
    y1 = df_total['GapT3Servicios']
    y_prom = df_total['PromedioGap']
    fig, ax = plt.subplots()

    ax.set_ylim(-7, 7)
    ax.plot(x, y1, color='#39a4b3', label="GAP Servicios",
            markersize=4, linestyle='dashed', alpha=0.5)
    ax.plot(x, y_prom, color='Black', label="Promedio GAP",
            marker='o', markersize=4)

    ax.axhline(prom_gap, linestyle='dashed',
               linewidth=1, color='red',
               label='GAP Promedio General')
    ax.axhline(prom_gap_serv, linestyle='dashed',
               linewidth=1, color='#39a4b3',
               label='GAP Promedio Servicios', alpha=0.5)

    ax.axhline(0, color='black', linewidth=1)

    ax.fill_between(x, y_prom, 0, where=(y_prom > 0), facecolor='#fcba03',
                    alpha=0.5, interpolate=True)
    ax.fill_between(x, y_prom, 0, where=(y_prom < 0), facecolor='#925bc9',
                    alpha=0.5, interpolate=True)

    ax.set_yticks(np.arange(-200, 201, 40))
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_xlabel("Tercer Trimestre de cada Año")
    ax.set_ylabel("Diferencia Salarial (Mujer - Hombre) Mensual En Dólares")
    ax.set_title('Gap Salarial')
    ax.set_xticks(np.arange(2015, 2025, 1))
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    return df_total

def reg_lineal(df_total):
    X = df_total['Años'].values.reshape(-1, 1)
    y = df_total['PromedioGap'].values.reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    # Predicciones actuales
    y_pred = model.predict(X)

    # Predicciones futuras
    futuros = np.array([[2025], [2026], [2027]])
    pred_fut = model.predict(futuros)

    # Mostrar predicciones futuras
    for año, gap in zip(futuros.flatten(), pred_fut.flatten()):
        print(f"Gap proyectado para {año}: {gap:.2f} dólares")

    # Gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_total['Años'], df_total['PromedioGap'],
            marker='o', label='Gap real', color='black')
    ax.plot(df_total['Años'], y_pred, color='#edbc1c',
            linestyle='--', label='Tendencia lineal')
    ax.set_yticks(np.arange(-200, 201, 40))
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_xlabel("Tercer Trimestre de cada Año")
    ax.set_ylabel("Diferencia Salarial (Mujer - Hombre) Mensual En Dólares")
    ax.set_title('Gap Salarial')
    ax.set_xticks(np.arange(2015, 2025, 1))
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def regresiones_sectores(df_total):
    # Selecciona todas las columnas que contienen 'GapT3'
    gap_columns = [col for col in df_total.columns if col.startswith('GapT3')]

    for col in gap_columns:
        X = df_total['Años'].values.reshape(-1, 1)
        y = df_total[col].values.reshape(-1, 1)

        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        nombre_sector = col.replace('GapT3', '')

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axhline(0, color='black', linewidth=1)
        ax.plot(df_total['Años'], y, marker='o',
                label=f'Área de {nombre_sector}', color='black')
        ax.plot(df_total['Años'], y_pred, color='green',
                label='Tendencia', linestyle='dashed')

        ax.set_yticks(np.arange(-200, 201, 40))
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_xlabel("Tercer Trimestre de cada Año")
        ax.set_ylabel(
            "Diferencia Salarial (Mujer - Hombre) Mensual En Dólares")
        ax.set_title(f'Gap Salarial - {nombre_sector}')
        ax.set_xticks(np.arange(2015, 2025, 1))
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


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

# Concatena las horas trabajadas SEMANALES en un solo dataframe.
correc_horas_dict = correcion_horas(horas_df, ajustados)

for nombre, df in correc_horas_dict.items():
    graficos_hora(df, nombre)

dataframes = gap_areas_graf(correc_horas_dict)

reg_lineal(dataframes)

regresiones_sectores(dataframes)
