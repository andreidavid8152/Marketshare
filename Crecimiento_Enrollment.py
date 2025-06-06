import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Título de la aplicación
st.title("Tasas de crecimiento matriculas e ingresos")

# Menú lateral para la navegación
menu = [
    "Crecimiento de los periodos 10",
    "Crecimiento de los periodos 20",
    "Participación Facultades",
    "Participación Carreras",
]
choice = st.sidebar.selectbox("Menú", menu)

# Ruta del archivo Excel
excel_file = "files/baseEnrollment.xlsx"


def aplicar_escala_tres_colores(df, columnas_porcentuales, centro=50):

    formato = {col: "{:.0f}%" for col in columnas_porcentuales if col in df.columns}
    styled = df.style.format(formato)

    for col in columnas_porcentuales:
        if col in df.columns:
            col_min = df[col].min()
            col_max = df[col].max()

            norm = mcolors.TwoSlopeNorm(vmin=col_min, vcenter=centro, vmax=col_max)

            def color_celda(valor):
                if pd.isnull(valor):
                    return ""  
                # Obtenemos un RGBA a partir del colormap 'RdYlGn'
                rgba = plt.cm.RdYlGn(norm(valor))
                # Disminuimos la saturación para lograr un efecto pastel
                pastel_rgba = tuple(0.2 + 0.75 * c for c in rgba[:3])  # Mezcla con blanco
                # Convertimos a rgb(...) para CSS
                return f"background-color: rgba({int(pastel_rgba [0]*255)}, {int(pastel_rgba [1]*255)}, {int(pastel_rgba [2]*255)}, 1); color: #202122"

            # Aplicamos la función anterior a toda la columna col
            styled = styled.map(color_celda, subset=[col])

    return styled


# =============================================================================
# 1. Función para cargar tablas de los Semestres 10 y 20
# =============================================================================
def cargar_tabla_desde_rango(columnas, fila_inicio, num_filas, columnas_porcentuales):
    try:
        # Leer el rango específico de la hoja 'Hoja1'
        df = pd.read_excel(
            excel_file,
            sheet_name="Hoja1",
            usecols=columnas,
            skiprows=fila_inicio - 1,  # Restar 1 porque pandas usa índice base 0
            nrows=num_filas,
            header=0,  # Asegura que se lean los encabezados correctamente
        )
        # Eliminar sufijos como .1, .2 en los encabezados
        df.columns = df.columns.str.replace(r"\.\d+$", "", regex=True)

        # Convertir las columnas porcentuales multiplicando por 100 si existen en los datos
        for col in columnas_porcentuales:
            if col in df.columns:
                df[col] = df[col] * 100

        return df
    except Exception as e:
        st.error(f"Error al cargar el rango '{columnas}' desde 'Hoja1': {e}")
        return pd.DataFrame()


# Definir columnas porcentuales para cada semestre
columnas_porcentuales_sem10 = ["202210", "202310", "202410", "202510"]
columnas_porcentuales_sem20 = ["202220", "202320", "202420", "202520"]

# =============================================================================
# 2. Lógica según la elección del usuario
# =============================================================================
if choice == "Crecimiento de los periodos 10":
    columnas_semestre_10 = "I:O"
    fila_inicio_semestre_10 = 1
    num_filas_semestre_10 = 74
    semestre_10 = cargar_tabla_desde_rango(
        columnas_semestre_10,
        fila_inicio_semestre_10,
        num_filas_semestre_10,
        columnas_porcentuales_sem10,
    )

    if not semestre_10.empty:
        # Aquí sustituimos el uso de background_gradient por nuestra nueva función
        styled_semestre_10 = aplicar_escala_tres_colores(
            semestre_10,
            columnas_porcentuales_sem10,
            centro=50,  # El valor del punto medio donde quieres que sea "amarillo"
        )

        st.dataframe(
            styled_semestre_10,
            use_container_width=True,
            height=800,
            hide_index=True,
        )
    else:
        st.warning("No se pudieron cargar los datos del Semestre 10.")
        st.write(
            "Por favor, verifica que las coordenadas para 'Semestre 10' son correctas."
        )


elif choice == "Crecimiento de los periodos 20":
    columnas_semestre_20 = "R:X"
    fila_inicio_semestre_20 = 1
    num_filas_semestre_20 = 74
    semestre_20 = cargar_tabla_desde_rango(
        columnas_semestre_20,
        fila_inicio_semestre_20,
        num_filas_semestre_20,
        columnas_porcentuales_sem20,
    )

    if not semestre_20.empty:
        styled_semestre_20 = aplicar_escala_tres_colores(
            semestre_20, columnas_porcentuales_sem20, centro=50
        )
        st.dataframe(
            styled_semestre_20,
            use_container_width=True,
            height=800,
            hide_index=True,
        )
    else:
        st.warning("No se pudieron cargar los datos del Semestre 20.")
        st.write(
            "Por favor, verifica que las coordenadas para 'Semestre 20' son correctas."
        )

# =============================================================================
# 3. Nueva opción: Participación Facultades (gráfico de pastel)
# =============================================================================
elif choice == "Participación Facultades":
    # --- Cargar datos de la hoja "PREGRADO" ---
    try:
        df_pregrado = pd.read_excel(excel_file, sheet_name="PREGRADO", header=0)
    except Exception as e:
        st.error(f"Error al leer la hoja 'PREGRADO': {e}")
        st.stop()

    # Convertir ENROLLMENT a numérico
    df_pregrado["ENROLLMENT"] = pd.to_numeric(
        df_pregrado["ENROLLMENT"], errors="coerce"
    )

    # Filtro de selección múltiple de semestres
    semestres_disponibles = sorted(df_pregrado["SEMESTRE"].unique())
    semestres_seleccionados = st.multiselect(
        "Selecciona uno o más semestres:",
        semestres_disponibles,
        default=semestres_disponibles[0] if semestres_disponibles else None,
    )

    # Validar que haya selección
    if not semestres_seleccionados:
        st.warning(
            "Por favor, selecciona al menos un semestre para visualizar los datos."
        )
    else:
        # Filtrar por los semestres seleccionados
        df_filtrado = df_pregrado[df_pregrado["SEMESTRE"].isin(semestres_seleccionados)]

        # Verificamos que haya datos
        if df_filtrado.empty:
            st.warning("No hay datos para los semestres seleccionados.")
        else:
            # Agrupar por FACULTAD
            df_agrupado = df_filtrado.groupby("FACULTAD", as_index=False)[
                "ENROLLMENT"
            ].sum()

            # Identificar la facultad con mayor participación
            max_enrollment = df_agrupado["ENROLLMENT"].max()

            # Definir función para mapear ENROLLMENT a escala de grises
            def map_to_grayscale(value, min_val, max_val):
                if max_val == min_val:
                    gray_level = 169  # Valor por defecto si no hay variación
                else:
                    # Normalizar el valor entre 0 y 1
                    norm = (value - min_val) / (max_val - min_val)
                    # Invertir para que mayor participación sea más oscuro
                    gray_level = (
                        int(255 * (1 - norm) * 0.6) + 50
                    )  # Ajusta según preferencia
                return f"rgb({gray_level}, {gray_level}, {gray_level})"

            # Obtener valores mínimos y máximos de ENROLLMENT (excluyendo el máximo)
            min_enrollment = df_agrupado["ENROLLMENT"].min()
            max_enrollment = df_agrupado["ENROLLMENT"].max()

            # Asignar colores
            colors = []
            for enrollment in df_agrupado["ENROLLMENT"]:
                if enrollment == max_enrollment:
                    colors.append("#8d002e")
                else:
                    colors.append(
                        map_to_grayscale(enrollment, min_enrollment, max_enrollment)
                    )

            # Crear un mapeo de colores para cada facultad
            color_map = {
                facultad: color
                for facultad, color in zip(df_agrupado["FACULTAD"], colors)
            }

            # Crear el gráfico de pastel usando Plotly con colores personalizados
            fig = px.pie(
                df_agrupado,
                values="ENROLLMENT",
                names="FACULTAD",
                hole=0.3,
                color="FACULTAD",
                color_discrete_map=color_map,
                title="Participación por Facultad",
            )

            st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 4. Nueva opción: Participación Carreras (gráfico de pastel)
# =============================================================================
elif choice == "Participación Carreras":
    # --- Cargar datos de la hoja "PREGRADO" ---
    try:
        df_pregrado = pd.read_excel(excel_file, sheet_name="PREGRADO", header=0)
    except Exception as e:
        st.error(f"Error al leer la hoja 'PREGRADO': {e}")
        st.stop()

    # Convertir ENROLLMENT a numérico
    df_pregrado["ENROLLMENT"] = pd.to_numeric(
        df_pregrado["ENROLLMENT"], errors="coerce"
    )

    # Filtro de selección múltiple de facultades
    facultades_disponibles = sorted(df_pregrado["FACULTAD"].unique())
    facultades_seleccionadas = st.multiselect(
        "Selecciona una o más facultades:",
        facultades_disponibles,
        default=facultades_disponibles[0] if facultades_disponibles else None,
    )

    # Validar selección de facultades
    if not facultades_seleccionadas:
        st.warning(
            "Por favor, selecciona al menos una facultad para visualizar los datos."
        )
    else:
        # Filtrar por facultades seleccionadas
        df_filtrado_facultad = df_pregrado[
            df_pregrado["FACULTAD"].isin(facultades_seleccionadas)
        ]

        # Filtro de selección múltiple de semestres
        semestres_disponibles = sorted(df_filtrado_facultad["SEMESTRE"].unique())
        semestres_seleccionados = st.multiselect(
            "Selecciona uno o más semestres:",
            semestres_disponibles,
            default=semestres_disponibles[0] if semestres_disponibles else None,
        )

        # Validar selección de semestres
        if not semestres_seleccionados:
            st.warning(
                "Por favor, selecciona al menos un semestre para visualizar los datos."
            )
        else:
            # Filtrar por los semestres seleccionados
            df_filtrado = df_filtrado_facultad[
                df_filtrado_facultad["SEMESTRE"].isin(semestres_seleccionados)
            ]

            # Verificamos que haya datos
            if df_filtrado.empty:
                st.warning(
                    "No hay datos para las facultades y semestres seleccionados."
                )
            else:
                # Agrupar por CARRERA
                df_agrupado = df_filtrado.groupby("CARRERA", as_index=False)[
                    "ENROLLMENT"
                ].sum()

                # Identificar la carrera con mayor participación
                max_enrollment_carrera = df_agrupado["ENROLLMENT"].max()

                # Definir función para mapear ENROLLMENT a escala de grises
                def map_to_grayscale(value, min_val, max_val):
                    if max_val == min_val:
                        gray_level = 169  # Valor por defecto si no hay variación
                    else:
                        # Normalizar el valor entre 0 y 1
                        norm = (value - min_val) / (max_val - min_val)
                        # Invertir para que mayor participación sea más oscuro
                        gray_level = (
                            int(255 * (1 - norm) * 0.6) + 50
                        )  # Ajusta según preferencia
                    return f"rgb({gray_level}, {gray_level}, {gray_level})"

                # Obtener valores mínimos y máximos de ENROLLMENT (excluyendo el máximo)
                min_enrollment_carrera = df_agrupado["ENROLLMENT"].min()
                max_enrollment_carrera = df_agrupado["ENROLLMENT"].max()

                # Asignar colores
                colors = []
                for enrollment in df_agrupado["ENROLLMENT"]:
                    if enrollment == max_enrollment_carrera:
                        colors.append("#8d002e")
                    else:
                        colors.append(
                            map_to_grayscale(
                                enrollment,
                                min_enrollment_carrera,
                                max_enrollment_carrera,
                            )
                        )

                # Crear un mapeo de colores para cada carrera
                color_map = {
                    carrera: color
                    for carrera, color in zip(df_agrupado["CARRERA"], colors)
                }

                # Crear el gráfico de pastel usando Plotly con colores personalizados
                fig = px.pie(
                    df_agrupado,
                    values="ENROLLMENT",
                    names="CARRERA",
                    hole=0.3,
                    color="CARRERA",
                    color_discrete_map=color_map,
                    title="Participación por Carrera",
                )

                st.plotly_chart(fig, use_container_width=True)
