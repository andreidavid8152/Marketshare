import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# --- Lectura de datos ---
df = pd.read_excel("./files/baseMarketShare2.xlsx")

st.title("Matriculados y Número de Instituciones por Carrera")

# --- Filtro NIVEL ---
niveles_disponibles = sorted(df["NIVEL"].unique())
niveles_seleccionados = st.multiselect(
    "Elige uno o varios niveles:",
    options=niveles_disponibles,
    default=niveles_disponibles,
)

# Aplicar filtro por nivel
df = df[df["NIVEL"].isin(niveles_seleccionados)]

# --- Filtro AÑO ---
anios_seleccionados = st.multiselect(
    "Elige uno o varios años:",
    options=sorted(df["AÑO"].unique()),
    default=sorted(df["AÑO"].unique()),
)

# --- Filtro FACULTAD ---

facultades_validas = sorted([f for f in df["FACULTAD"].unique() if isinstance(f, str) and f.strip() != ""])

facultades_seleccionadas = st.multiselect(
    "Elige una o varias facultades:",
    options=facultades_validas,
    default=facultades_validas,
)

# --- Filtro CARRERA (automáticamente todas las relacionadas con las facultades seleccionadas) ---
carreras_filtradas = df[df["FACULTAD"].isin(facultades_seleccionadas)][
    "CARRERA"
].unique()
carreras_seleccionadas = st.multiselect(
    "Elige una o varias carreras:",
    options=sorted(carreras_filtradas),
    default=sorted(carreras_filtradas),
)


# --- Filtrar DataFrame ---
df_filt = df[
    (df["AÑO"].isin(anios_seleccionados))
    & (df["FACULTAD"].isin(facultades_seleccionadas))
    & (df["CARRERA"].isin(carreras_seleccionadas))
].copy()


if df_filt.empty:
    st.warning("No hay datos para la selección actual.")
    st.stop()

# --- Agrupar instituciones y matriculados ---
instituciones = (
    df_filt.groupby(["AÑO", "NIVEL"])["UNIVERSIDAD"]
    .nunique()
    .unstack(fill_value=0)
    .sort_index()
)
matriculados = (
    df_filt.groupby(["AÑO", "NIVEL"])["MATRICULADOS"]
    .sum()
    .unstack(fill_value=0)
    .sort_index()
)

# Años ordenados
anios = instituciones.index.tolist()

# Colores
colors = {
    "TECNICO": {"fill": "#e6e6e6", "line": "#666666"},
    "TERCER NIVEL": {"fill": "#f2cccc", "line": "#990000"},
}

# --- Construir figura Plotly ---
fig = go.Figure()

# Barras apiladas (instituciones)
fig.add_trace(
    go.Bar(
        x=anios,
        y=instituciones.get("TECNICO", pd.Series(0, index=anios)).astype(int),
        name="Institutos Técnicos",
        marker_color=colors["TECNICO"]["fill"],
        marker_line_color=colors["TECNICO"]["line"],
        marker_line_width=1.5,
        hovertemplate="%{y:d}<extra></extra>",
    )
)
fig.add_trace(
    go.Bar(
        x=anios,
        y=instituciones.get("TERCER NIVEL", pd.Series(0, index=anios)).astype(int),
        name="Universidades",
        marker_color=colors["TERCER NIVEL"]["fill"],
        marker_line_color=colors["TERCER NIVEL"]["line"],
        marker_line_width=1.5,
        hovertemplate="%{y:d}<extra></extra>",
    )
)

# Calcular totales de instituciones por año
total_instituciones = (
    instituciones.get("TECNICO", pd.Series(0, index=anios))
    + instituciones.get("TERCER NIVEL", pd.Series(0, index=anios))
).astype(int)

# Texto con totales encima de las barras
fig.add_trace(
    go.Scatter(
        x=anios,
        y=total_instituciones + 0.3,
        text=total_instituciones.map(str),
        mode="text",
        textposition="top center",
        name="Total Instituciones",
        showlegend=False,
        hoverinfo="skip",
    )
)

# Líneas (matriculados) — eje secundario
fig.add_trace(
    go.Scatter(
        x=anios,
        y=matriculados.get("TECNICO", pd.Series(0, index=anios)).astype(int),
        name="Matriculados Técnico",
        mode="lines+markers",
        marker_symbol="circle",
        marker_size=8,
        line=dict(color=colors["TECNICO"]["line"], width=2),
        yaxis="y2",
        hovertemplate="%{y:d}<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=anios,
        y=matriculados.get("TERCER NIVEL", pd.Series(0, index=anios)).astype(int),
        name="Matriculados Universidad",
        mode="lines+markers",
        marker_symbol="square",
        marker_size=8,
        line=dict(color=colors["TERCER NIVEL"]["line"], width=2),
        yaxis="y2",
        hovertemplate="%{y:d}<extra></extra>",
    )
)

# --- Layout ---
fig.update_layout(
    xaxis_title="Año",
    yaxis=dict(
        title="Número de Instituciones",
        showgrid=True,
        gridcolor="lightgrey",
        zeroline=True,
    ),
    yaxis2=dict(title="Número de Matriculados", overlaying="y", side="right"),
    barmode="stack",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=80, b=40, l=60, r=60),
    hovermode="x unified",
)

fig.update_xaxes(type="category")

# --- Mostrar en Streamlit ---
st.plotly_chart(fig, use_container_width=True)
