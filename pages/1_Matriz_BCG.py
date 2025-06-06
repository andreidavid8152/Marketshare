import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# Definir la función para generar colores en escala de grises
def generar_grises(num_colores, inicio=211, fin=0):

    if num_colores == 1:
        gris = int((inicio + fin) / 2)
        return [f"#{gris:02X}{gris:02X}{gris:02X}"]

    paso = (inicio - fin) / (num_colores - 1)
    colores = []
    for i in range(num_colores):
        gris = int(inicio - paso * i)
        gris = max(0, min(255, gris))
        colores.append(f"#{gris:02X}{gris:02X}{gris:02X}")
    return colores


# Configuración de la página
st.set_page_config(layout="wide")

# Título de la aplicación
st.title("Tendencias de matriculas e ingresos")


# Cargar los datos desde el archivo Excel
@st.cache_data
def cargar_datos(ruta_archivo):
    try:
        df = pd.read_excel(ruta_archivo, sheet_name="PREGRADO")
        return df
    except FileNotFoundError:
        st.error(
            f"El archivo '{ruta_archivo}' no se encuentra en el directorio actual."
        )
        st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo Excel: {e}")
        st.stop()


# Ruta del archivo Excel
ruta_excel = "./files/baseEnrollment.xlsx"

# Cargar los datos
df = cargar_datos(ruta_excel)

# Convertir 'SEMESTRE' a tipo string para facilitar los filtros
df["SEMESTRE"] = df["SEMESTRE"].astype(str)

# Convertir variaciones a numéricas y manejar errores
df["Variación Enrollment"] = pd.to_numeric(df["Variación Enrollment"], errors="coerce")
df["Variación Ingresos"] = pd.to_numeric(df["Variación Ingresos"], errors="coerce")

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtro por Facultad
facultades = df["FACULTAD"].unique()
facultad_seleccionada = st.sidebar.selectbox(
    "Selecciona la Facultad",
    options=facultades,
    help="Selecciona una facultad para filtrar los datos",
)

# Filtrar por Facultad
df_filtrado = df[df["FACULTAD"] == facultad_seleccionada]

# Obtener las Carreras asociadas a la Facultad seleccionada
carreras_facultad = df_filtrado["CARRERA"].unique()

# Determinar si la Facultad tiene más de una Carrera
tiene_multiples_carreras = len(carreras_facultad) > 1

if tiene_multiples_carreras:
    # Filtro de Carrera
    carreras_seleccionadas = st.sidebar.multiselect(
        "Selecciona la Carrera",
        options=carreras_facultad,
        default=carreras_facultad,
        help="Selecciona una o más carreras para filtrar los datos",
    )
    if carreras_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado["CARRERA"].isin(carreras_seleccionadas)]
    else:
        st.sidebar.warning(
            "No se ha seleccionado ninguna carrera. Mostrando todas las carreras."
        )

    # Filtro de Semestre
    semestres = df_filtrado["SEMESTRE"].unique()
    semestre_seleccionado = st.sidebar.multiselect(
        "Selecciona el Semestre",
        options=semestres,
        default=semestres,
        help="Selecciona uno o más semestres para filtrar los datos",
    )
    if semestre_seleccionado:
        df_filtrado = df_filtrado[df_filtrado["SEMESTRE"].isin(semestre_seleccionado)]
else:
    # Si solo hay una Carrera, deshabilitar el filtro de Carrera y Semestre
    carrera_unica = carreras_facultad[0]
    st.sidebar.info(
        f"La facultad seleccionada tiene una sola carrera: **{carrera_unica}**. Los filtros de Carrera y Semestre están deshabilitados."
    )

# Eliminar filas con datos nulos en las variaciones
df_filtrado = df_filtrado.dropna(subset=["Variación Enrollment", "Variación Ingresos"])

# Crear la Matriz BCG
if not df_filtrado.empty:
    fig = go.Figure()

    # Obtener la lista de semestres únicos
    semestres_unicos = df_filtrado["SEMESTRE"].unique()

    # Definir el color vino para el semestre "202510"
    color_vino = "#800020"  # Código hexadecimal para un color vino oscuro

    # Generar colores en escala de grises para los demás semestres
    semestres_grises = [s for s in semestres_unicos if s != "202520"]
    num_grises = len(semestres_grises)

    if num_grises > 0:
        # Generar una lista de colores en escala de grises
        # Desde '#D3D3D3' (lightgray) hasta '#000000' (black)
        grises = generar_grises(num_grises, inicio=211, fin=0)
    else:
        grises = []

    # Crear el mapa de colores
    colores_semestre = {}
    for i, semestre in enumerate(semestres_unicos):
        if semestre == "202520":
            colores_semestre[semestre] = color_vino
        else:
            colores_semestre[semestre] = grises[i] if i < num_grises else "#808080"

    # Calcular los límites de los ejes con padding proporcional
    def calcular_paddings(df_col):
        min_val = df_col.min()
        max_val = df_col.max()
        rango = max_val - min_val
        if rango == 0:
            rango = abs(max_val) if max_val != 0 else 1  # Evitar división por cero
        padding = rango * 0.1  # 10% del rango
        return min_val - padding, max_val + padding

    # Aplicar la escala multiplicando por 100
    variacion_enrollment_scaled = df_filtrado["Variación Enrollment"] * 100
    variacion_ingresos_scaled = df_filtrado["Variación Ingresos"] * 100

    x_min, x_max = calcular_paddings(variacion_enrollment_scaled)
    y_min, y_max = calcular_paddings(variacion_ingresos_scaled)

    # Añadir puntos al gráfico con tooltips formateados y colores por semestre
    for semestre in semestres_unicos:
        df_semestre = df_filtrado[df_filtrado["SEMESTRE"] == semestre]
        fig.add_trace(
            go.Scatter(
                x=df_semestre["Variación Enrollment"] * 100,
                y=df_semestre["Variación Ingresos"] * 100,
                mode="markers+text",
                marker=dict(
                    size=df_semestre["ENROLLMENT"],  # Tamaño según Enrollment
                    sizemode="area",
                    sizeref=2.0
                    * max(df["ENROLLMENT"])
                    / (40.0**2),  # Ajusta el tamaño de referencia según los datos
                    sizemin=4,
                    color=colores_semestre[semestre],  # Color por semestre
                    line=dict(width=1, color="DarkSlateGrey"),
                ),
                text=df_semestre["CARRERA"],  # Solo la carrera en el texto
                textposition="top center",
                customdata=df_semestre[
                    "SEMESTRE"
                ],  # Agregar el semestre como customdata
                hovertemplate=(
                    "<b>Carrera:</b> %{text}<br>"
                    "<b>Semestre:</b> %{customdata}<br>"
                    "<b>Variación de Enrollment:</b> %{x:.2f}%<br>"
                    "<b>Variación de Ingresos:</b> %{y:.2f}%<br>"
                    "<extra></extra>"
                ),
                name=f"Semestre {semestre}",
            )
        )

    # Añadir líneas para dividir los cuadrantes
    fig.add_shape(
        type="line",
        x0=0,
        y0=y_min,
        x1=0,
        y1=y_max,
        line=dict(color="Black", dash="dash"),
    )
    fig.add_shape(
        type="line",
        x0=x_min,
        y0=0,
        x1=x_max,
        y1=0,
        line=dict(color="Black", dash="dash"),
    )

    # Configurar el layout del gráfico
    fig.update_layout(
        xaxis_title="Variación de Enrollment (%)",
        yaxis_title="Variación de Ingresos (%)",
        showlegend=True,
        legend_title="Semestre",
        template="plotly_white",
        width=1000,
        height=700,
        xaxis=dict(
            range=[x_min, x_max],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="White",
        ),
        yaxis=dict(
            range=[y_min, y_max],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="White",
        ),
    )

    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
