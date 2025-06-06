import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Cargar los datos
df = pd.read_excel("./files/baseMarketShare2.xlsx")

# Título de la aplicación
st.title("MARKETSHARE")

# Filtros en la barra lateral
st.sidebar.header("Filtros")

# Filtro de Año
anio = st.sidebar.multiselect(
    "Año:",
    options=sorted(df["AÑO"].unique()),
    default=sorted(df["AÑO"].unique()),
    help="Selecciona uno o más años",
)

filtered_df = df.copy()
if anio:
    filtered_df = filtered_df[filtered_df["AÑO"].isin(anio)]

# Filtro de Región
region = st.sidebar.multiselect(
    "Región:",
    options=df["REGION"].unique(),
    default=None,
    help="Selecciona una o más regiones",
)
if region:
    filtered_df = filtered_df[filtered_df["REGION"].isin(region)]

# Filtro de Financiamiento
financiamiento = st.sidebar.multiselect(
    "Financiamiento:",
    options=filtered_df["FINANCIAMIENTO"].unique(),
    default=None,
    help="Selecciona uno o más tipos de financiamiento",
)
if financiamiento:
    filtered_df = filtered_df[filtered_df["FINANCIAMIENTO"].isin(financiamiento)]

# Filtro de Nivel
nivel = st.sidebar.multiselect(
    "Nivel:",
    options=filtered_df["NIVEL"].unique(),
    default=None,
    help="Selecciona uno o más niveles",
)
if nivel:
    filtered_df = filtered_df[filtered_df["NIVEL"].isin(nivel)]

# Filtro de Facultad
facultad = st.sidebar.selectbox(
    "Facultad:",
    options=[None] + filtered_df["FACULTAD"].unique().tolist(),
    index=0,
    help="Selecciona una facultad",
)
if facultad:
    filtered_df = filtered_df[filtered_df["FACULTAD"] == facultad]

# Filtro de Carrera
carrera = st.sidebar.multiselect(
    "Carrera:",
    options=filtered_df["CARRERA"].unique(),
    default=None,
    help="Selecciona una o más carreras",
)
if carrera:
    filtered_df = filtered_df[filtered_df["CARRERA"].isin(carrera)]

# Determinar el rango de años para la escala azul
min_year = min(filtered_df["AÑO"].unique())
max_year = max(filtered_df["AÑO"].unique())

# Agrupar por universidad y año
df_agrupado = (
    filtered_df.groupby(["AÑO", "UNIVERSIDAD"])
    .agg({"MATRICULADOS": "sum"})
    .reset_index()
)

# Verificar que haya datos
if df_agrupado.empty:
    st.write("No hay datos con los filtros seleccionados.")
    st.stop()

# Calcular la participación
df_agrupado["PARTICIPACION"] = df_agrupado.groupby("AÑO")["MATRICULADOS"].transform(
    lambda x: x / x.sum()
)

# Crear la figura
fig = go.Figure()

# Calcular el orden global de universidades (de menor a mayor participación acumulada)
orden_universidades = (
    df_agrupado.groupby("UNIVERSIDAD")["PARTICIPACION"]
    .sum()
    .sort_values()
    .index.tolist()
)

# Obtener los años únicos
años = df_agrupado["AÑO"].unique()


# Función para interpolar de celeste a azul fuerte
def interpolate_blue(intensity):
    r = int(204 + (0 - 204) * intensity)
    g = int(229 + (76 - 229) * intensity)
    b = int(255 + (153 - 255) * intensity)
    return f"rgb({r}, {g}, {b})"


# Dibujar barras para cada año
for i, año in enumerate(años):
    df_year = df_agrupado[df_agrupado["AÑO"] == año]

    # Calcular la intensidad basada en el año (año mayor = azul más fuerte)
    intensity = (año - min_year) / (max_year - min_year) if max_year != min_year else 1
    blue_color = interpolate_blue(intensity)
    colors = [blue_color] * len(df_year)

    fig.add_trace(
        go.Bar(
            x=df_year["PARTICIPACION"],
            y=df_year["UNIVERSIDAD"],
            marker_color=colors,
            orientation="h",
            name=f"Año {año}",
        )
    )


# Configurar el layout aplicando el orden global en el eje Y
fig.update_layout(
    barmode="group",
    title="Participación por Universidad y Año",
    xaxis_title="Participación",
    yaxis_title="Universidades",
    template="plotly_white",
    height=700,
    yaxis=dict(categoryorder="array", categoryarray=orden_universidades),
    legend=dict(traceorder="reversed"),
)

# Mostrar el gráfico en Streamlit
st.plotly_chart(fig)
