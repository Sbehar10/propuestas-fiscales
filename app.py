import streamlit as st
import pandas as pd
import io
import constantes
from datetime import datetime
from constantes import (
    LISTA_PUESTOS, PUESTOS_PROFESIONALES, PRIMA_RIESGO,
    SALARIO_MINIMO_MENSUAL, ISN_TASAS_ESTADO,
)
from motor_calculo import (
    calcular_esquema_actual, calcular_esquema_irt, calcular_excedentes,
    calcular_sociedad_civil, calcular_grupo_nomina, neto_a_bruto
)
from procesador_nomina import (
    detectar_columnas, detectar_bruto_neto, mapear_puestos, validar_datos
)
from generador_word import generar_propuesta_word, fmt_moneda

# === CONFIGURACION DE PAGINA ===
st.set_page_config(
    page_title="Sistema de Cotizacion Fiscal 2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILOS CSS ===
st.markdown("""
<style>
    /* --- Base: fondo blanco, tipografia limpia --- */
    .stApp {
        background-color: #FFFFFF !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .stApp [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
    }
    .stApp [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }
    .block-container {
        background-color: #FFFFFF !important;
    }
    .stMarkdown p, .stMarkdown li {
        color: #2D3748 !important;
    }
    h1, h2, h3, h4 {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* --- Header banner --- */
    .main-header {
        background: linear-gradient(135deg, #1B3A5C 0%, #2C5F8A 100%);
        padding: 2.2rem 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(27,58,92,0.15);
    }
    .main-header h1 {
        color: #FFFFFF !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: 0.3px;
    }
    .main-header .accent {
        color: #C9A962 !important;
    }
    .main-header p {
        color: rgba(255,255,255,0.75) !important;
        font-size: 0.9rem;
        font-weight: 400;
        margin: 0.4rem 0 0 0;
    }

    /* --- Section headers --- */
    .section-header {
        background: transparent;
        padding: 0 0 0.5rem 0;
        border-radius: 0;
        border-left: none;
        border-bottom: 2px solid #E2E8F0;
        margin: 1.8rem 0 1rem 0;
    }
    .section-header h3 {
        color: #1B3A5C !important;
        margin: 0 !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px;
    }

    /* --- Metric cards (white, clean) --- */
    .metric-card {
        background: #FFFFFF;
        padding: 1.4rem 1.2rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        margin-bottom: 0.5rem;
    }
    .metric-card h3 {
        color: #718096 !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .metric-card p {
        color: #1B3A5C !important;
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        margin: 0.4rem 0 0 0 !important;
    }
    .metric-card .sub {
        color: #A0AEC0 !important;
        font-size: 0.72rem !important;
        font-weight: 400 !important;
        margin: 0.15rem 0 0 0 !important;
    }

    /* --- Ahorro cards (soft green) --- */
    .ahorro-verde {
        background: #E8F5E9;
        padding: 1.4rem 1.2rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #C8E6C9;
        box-shadow: 0 1px 4px rgba(39,174,96,0.08);
        margin-bottom: 0.5rem;
    }
    .ahorro-verde h3 {
        color: #2E7D32 !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .ahorro-verde p {
        color: #1B5E20 !important;
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        margin: 0.4rem 0 0 0 !important;
    }
    .ahorro-verde .sub {
        color: #4CAF50 !important;
        font-size: 0.72rem !important;
        font-weight: 400 !important;
    }

    /* --- Estado badge --- */
    .estado-badge {
        display: inline-block;
        background: #F7F1E0;
        color: #8B6914 !important;
        padding: 0.25rem 0.7rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 0.3rem;
        border: 1px solid #E8D9A8;
    }

    /* --- Progress bar (cotizador) --- */
    .progress-bar {
        display: flex;
        justify-content: space-between;
        margin: 0.8rem 0 1.5rem 0;
        padding: 0;
        background: #F7FAFC;
        border-radius: 6px;
    }
    .progress-step {
        flex: 1;
        text-align: center;
        padding: 0.55rem 0.3rem;
        font-size: 0.73rem;
        font-weight: 600;
        color: #CBD5E0;
        border-bottom: 3px solid #E2E8F0;
        transition: all 0.2s ease;
    }
    .progress-step.active {
        color: #1B3A5C;
        border-bottom-color: #C9A962;
    }
    .progress-step.done {
        color: #2E7D32;
        border-bottom-color: #27AE60;
    }

    /* --- Buttons --- */
    .stButton>button {
        width: 100%;
    }
    .stButton>button[kind="primary"] {
        background-color: #1B3A5C !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #C9A962 !important;
        color: #1B3A5C !important;
    }

    /* --- Sidebar (light gray) --- */
    div[data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E2E8F0;
    }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown label,
    div[data-testid="stSidebar"] .stMarkdown h3 {
        color: #2D3748 !important;
    }
    div[data-testid="stSidebar"] hr {
        border-color: #E2E8F0 !important;
    }

    /* --- Dataframes / tables --- */
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        overflow: hidden;
    }

    /* --- Expanders --- */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #1B3A5C !important;
        background-color: #F7FAFC !important;
        border-radius: 6px !important;
    }

    /* --- Divider lines --- */
    hr {
        border-color: #EDF2F7 !important;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("""
<div class="main-header">
    <h1>Sistema de Cotizacion <span class="accent">Fiscal</span></h1>
    <p>Cotizacion y generacion de propuestas para clientes &mdash; Ano fiscal 2026</p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def _set_isn(tasa_isn):
    """Set ISN_TASA globally before calculations (single-threaded Streamlit).
    Must patch both constantes AND motor_calculo since motor_calculo uses 'from constantes import *'
    which copies values at import time."""
    import motor_calculo
    constantes.ISN_TASA = tasa_isn
    motor_calculo.ISN_TASA = tasa_isn


def generar_excel_resultados(resultados_grupos, nombre_empresa, estado_nombre, tasa_isn):
    """Generate Excel workbook with summary + detail sheets using openpyxl."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()

    # -- Hoja Resumen --
    ws = wb.active
    ws.title = "Resumen"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1B3A5C", end_color="1B3A5C", fill_type="solid")
    gold_font = Font(bold=True, color="C9A962", size=12)
    border = Border(
        bottom=Side(style="thin", color="CCCCCC"),
    )

    # Title
    ws.merge_cells("A1:F1")
    ws["A1"] = f"Propuesta Fiscal — {nombre_empresa or 'Cliente'}"
    ws["A1"].font = Font(bold=True, size=14, color="1B3A5C")
    ws["A2"] = f"Estado: {estado_nombre} (ISN {tasa_isn*100:.1f}%)"
    ws["A2"].font = Font(size=10, color="666666")
    ws["A3"] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
    ws["A3"].font = Font(size=10, color="666666")

    # Summary table
    row = 5
    headers = ["Puesto", "Empleados", "Sueldo Bruto", "Costo Actual", "Costo IRT", "Ahorro Mensual"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    total_actual = 0
    total_irt = 0
    total_ahorro = 0

    for r in resultados_grupos:
        row += 1
        ws.cell(row=row, column=1, value=r["puesto"])
        ws.cell(row=row, column=2, value=r["num_empleados"]).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=3, value=round(r["sueldo_bruto"], 2)).number_format = '$#,##0.00'
        ws.cell(row=row, column=4, value=round(r["actual"]["costo_total"], 2)).number_format = '$#,##0.00'
        costo_irt = r["irt"]["subtotal_factura"] * r["num_empleados"]
        ws.cell(row=row, column=5, value=round(costo_irt, 2)).number_format = '$#,##0.00'
        ws.cell(row=row, column=6, value=round(r["ahorro_mensual"], 2)).number_format = '$#,##0.00'
        for c in range(1, 7):
            ws.cell(row=row, column=c).border = border

        total_actual += r["actual"]["costo_total"]
        total_irt += costo_irt
        total_ahorro += r["ahorro_mensual"]

    # Totals row
    row += 1
    ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=row, column=4, value=round(total_actual, 2)).number_format = '$#,##0.00'
    ws.cell(row=row, column=4).font = Font(bold=True)
    ws.cell(row=row, column=5, value=round(total_irt, 2)).number_format = '$#,##0.00'
    ws.cell(row=row, column=5).font = Font(bold=True)
    ws.cell(row=row, column=6, value=round(total_ahorro, 2)).number_format = '$#,##0.00'
    ws.cell(row=row, column=6).font = gold_font

    # Projection
    row += 2
    ws.cell(row=row, column=1, value="Proyeccion de Ahorro").font = Font(bold=True, size=12)
    row += 1
    for label, mult in [("Mensual", 1), ("Anual", 12), ("2 Anos", 24), ("3 Anos", 36)]:
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=2, value=round(total_ahorro * mult, 2)).number_format = '$#,##0.00'
        row += 1

    # Column widths
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 18

    # -- Hoja Detalle --
    ws2 = wb.create_sheet("Detalle por Grupo")
    detail_row = 1
    for r in resultados_grupos:
        ws2.cell(row=detail_row, column=1, value=r["puesto"]).font = Font(bold=True, size=11)
        ws2.cell(row=detail_row, column=2, value=f"{r['num_empleados']} empleados")
        detail_row += 1

        detail_items = [
            ("Sueldo bruto", r["sueldo_bruto"]),
            ("Base nomina IRT", r["irt"]["base_nomina"]),
            ("Excedente IRT", r["irt"]["excedente_irt"]),
            ("IMSS patronal", r["irt"]["imss_patronal"]["total"]),
            ("INFONAVIT", r["irt"]["infonavit"]),
            ("ISN", r["irt"]["isn"]),
            ("Costo social", r["irt"]["costo_social"]),
            ("Comision", r["irt"]["comision"]),
            ("IVA", r["irt"]["iva"]),
            ("Total factura (por emp)", r["irt"]["total_factura"]),
            ("Costo actual (total grupo)", r["actual"]["costo_total"]),
            ("Ahorro mensual", r["ahorro_mensual"]),
        ]
        for label, val in detail_items:
            ws2.cell(row=detail_row, column=1, value=label)
            ws2.cell(row=detail_row, column=2, value=round(val, 2)).number_format = '$#,##0.00'
            detail_row += 1
        detail_row += 1

    ws2.column_dimensions["A"].width = 28
    ws2.column_dimensions["B"].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Datos del Cliente")
    nombre_empresa = st.text_input("Nombre de la empresa", placeholder="Grupo Industrial del Norte")
    contacto = st.text_input("Contacto", placeholder="Lic. Roberto Mendez")
    comision_pct = st.slider("Comision (%)", min_value=2.0, max_value=8.0, value=5.0, step=0.5)

    st.markdown("---")

    # Selector de estado para ISN
    st.markdown("### Estado (ISN)")
    estados_lista = sorted(ISN_TASAS_ESTADO.keys())
    idx_cdmx = next((i for i, e in enumerate(estados_lista) if "Ciudad" in e), 0)
    estado_sel = st.selectbox(
        "Estado donde opera la empresa",
        options=estados_lista,
        index=idx_cdmx,
        key="estado_isn"
    )
    tasa_isn = ISN_TASAS_ESTADO[estado_sel]
    st.markdown(
        f'<span class="estado-badge">{estado_sel} — ISN {tasa_isn*100:.2f}%</span>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Tipo de Servicio")
    tipo_servicio = st.radio(
        "Selecciona el servicio:",
        options=[
            "Cotizador (Subir nomina)",
            "Nomina completa (IRT)",
            "Solo excedentes",
            "Sociedad Civil",
        ],
        index=0
    )

    tipo_map = {
        "Cotizador (Subir nomina)": "cotizador",
        "Nomina completa (IRT)": "nomina",
        "Solo excedentes": "excedentes",
        "Sociedad Civil": "sc",
    }
    tipo = tipo_map[tipo_servicio]

# Set ISN for all calculations
_set_isn(tasa_isn)


# ============================================================
# HELPER: MOSTRAR RESULTADOS DE NOMINA IRT
# ============================================================
def mostrar_resultados_nomina(resultados_grupos, comision_pct, nombre_empresa, contacto):
    """Muestra metricas, proyeccion, grafica, detalle y descargas Word+Excel para resultados IRT."""
    import altair as alt

    costo_actual_total = 0
    ahorro_total = 0
    total_empleados = 0
    total_administrado = 0

    for r in resultados_grupos:
        costo_actual_total += r["actual"]["costo_total"]
        ahorro_total += r["ahorro_mensual"]
        total_empleados += r["num_empleados"]
        total_administrado += r["irt"]["total_administrado"] * r["num_empleados"]

    pct_ahorro = (ahorro_total / costo_actual_total * 100) if costo_actual_total > 0 else 0

    # Metricas principales
    st.markdown('<div class="section-header"><h3>Resultados del Analisis</h3></div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Costo Actual Mensual</h3>
            <p>{fmt_moneda(costo_actual_total)}</p>
            <p class="sub">Nomina 100%</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Costo IRT Propuesto</h3>
            <p>{fmt_moneda(costo_actual_total - ahorro_total)}</p>
            <p class="sub">Pre-IVA (acreditable)</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Empleados</h3>
            <p>{total_empleados}</p>
            <p class="sub">{len(resultados_grupos)} grupo(s)</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="ahorro-verde">
            <h3>Ahorro Mensual</h3>
            <p>{fmt_moneda(ahorro_total)}</p>
            <p class="sub">{pct_ahorro:.1f}% de ahorro</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Proyeccion de Ahorro
    st.markdown('<div class="section-header"><h3>Proyeccion de Ahorro</h3></div>', unsafe_allow_html=True)
    df_ahorro = pd.DataFrame({
        "Periodo": ["Mensual", "Anual", "2 Anos", "3 Anos"],
        "Ahorro IRT": [fmt_moneda(ahorro_total * m) for m in [1, 12, 24, 36]],
        "% Ahorro": [f"{pct_ahorro:.1f}%"] * 4,
    })
    st.dataframe(df_ahorro, use_container_width=True, hide_index=True)

    # Grafica comparativa
    st.markdown('<div class="section-header"><h3>Comparativo de Costos</h3></div>', unsafe_allow_html=True)
    chart_data = pd.DataFrame({
        "Esquema": ["Actual (100%)", "IRT Propuesto"],
        "Costo Mensual": [costo_actual_total, costo_actual_total - ahorro_total]
    })
    chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X("Esquema:N", sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Costo Mensual:Q", axis=alt.Axis(format="$,.0f")),
        color=alt.Color("Esquema:N", scale=alt.Scale(
            domain=["Actual (100%)", "IRT Propuesto"],
            range=["#1B3A5C", "#27AE60"]
        ), legend=None),
        tooltip=[
            alt.Tooltip("Esquema:N"),
            alt.Tooltip("Costo Mensual:Q", format="$,.2f")
        ]
    ).properties(height=350)
    st.altair_chart(chart, use_container_width=True)

    # Detalle por grupo
    st.markdown('<div class="section-header"><h3>Detalle por Grupo</h3></div>', unsafe_allow_html=True)
    for r in resultados_grupos:
        with st.expander(f"{r['puesto']} — {r['num_empleados']} emp. a {fmt_moneda(r['sueldo_bruto'])}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Costo Actual / mes</h3>
                    <p>{fmt_moneda(r["actual"]["costo_total"])}</p>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>Base Nomina IRT</h3>
                    <p>{fmt_moneda(r["irt"]["base_nomina"])}</p>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="ahorro-verde">
                    <h3>Ahorro / mes</h3>
                    <p>{fmt_moneda(r["ahorro_mensual"])}</p>
                </div>""", unsafe_allow_html=True)

            st.write(f"**Excedente IRT:** {fmt_moneda(r['irt']['excedente_irt'])} | "
                     f"**Neto actual:** {fmt_moneda(r['actual']['neto_trabajador'])} → "
                     f"**Neto IRT:** {fmt_moneda(r['irt']['neto_trabajador'])}")

    # === DESCARGAS ===
    st.markdown("---")
    st.markdown('<div class="section-header"><h3>Descargar Propuesta</h3></div>', unsafe_allow_html=True)

    datos_cliente = {
        "nombre_empresa": nombre_empresa or "Cliente",
        "contacto": contacto or "Sin especificar",
        "comision_pct": comision_pct,
    }
    resultados_word = {
        "total_empleados": total_empleados,
        "costo_actual_total": costo_actual_total,
        "ahorro_total_mensual": ahorro_total,
        "total_administrado": total_administrado,
    }

    buffer_word = generar_propuesta_word(
        datos_cliente=datos_cliente,
        tipo_servicio="nomina",
        resultados=resultados_word,
        grupos=resultados_grupos,
    )
    buffer_excel = generar_excel_resultados(resultados_grupos, nombre_empresa, estado_sel, tasa_isn)

    nombre_base = f"{nombre_empresa or 'Cliente'}_{datetime.now().strftime('%Y%m%d')}"

    col_w, col_e = st.columns(2)
    with col_w:
        st.download_button(
            label="DESCARGAR WORD",
            data=buffer_word,
            file_name=f"Propuesta_{nombre_base}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )
    with col_e:
        st.download_button(
            label="DESCARGAR EXCEL",
            data=buffer_excel,
            file_name=f"Propuesta_{nombre_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary",
            use_container_width=True,
        )


# ============================================================
# COTIZADOR (SUBIR NOMINA)
# ============================================================
if tipo == "cotizador":
    st.markdown('<div class="section-header"><h3>Cotizador — Subir Nomina</h3></div>', unsafe_allow_html=True)
    st.markdown("Sube un archivo Excel o CSV con la nomina del cliente para generar la propuesta automaticamente.")

    # Progress bar
    step = 1
    archivo = st.file_uploader(
        "Sube el archivo de nomina",
        type=["xlsx", "xls", "csv"],
        key="archivo_nomina"
    )
    if archivo:
        step = 2

    steps_html = ""
    step_labels = ["1. Subir archivo", "2. Mapear columnas", "3. Calcular", "4. Resultados"]
    for i, lbl in enumerate(step_labels, 1):
        cls = "done" if i < step else ("active" if i == step else "")
        steps_html += f'<div class="progress-step {cls}">{lbl}</div>'
    st.markdown(f'<div class="progress-bar">{steps_html}</div>', unsafe_allow_html=True)

    if archivo is not None:
        # Leer archivo
        try:
            if archivo.name.endswith(".csv"):
                try:
                    df_raw = pd.read_csv(archivo, encoding="utf-8")
                except UnicodeDecodeError:
                    archivo.seek(0)
                    df_raw = pd.read_csv(archivo, encoding="latin-1")
            else:
                df_raw = pd.read_excel(archivo)
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()

        st.markdown("#### Vista previa del archivo")
        st.dataframe(df_raw.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_raw)} filas x {len(df_raw.columns)} columnas")

        # --- Column mapping ---
        st.markdown("#### Mapeo de columnas")
        cols_detectadas = detectar_columnas(df_raw)
        columnas_df = list(df_raw.columns)

        col1, col2, col3 = st.columns(3)
        with col1:
            idx_puesto = columnas_df.index(cols_detectadas["puesto"]) if cols_detectadas["puesto"] in columnas_df else 0
            col_puesto = st.selectbox("Columna de Puesto", options=columnas_df, index=idx_puesto, key="col_puesto")
        with col2:
            idx_sueldo = columnas_df.index(cols_detectadas["sueldo"]) if cols_detectadas["sueldo"] in columnas_df else 0
            col_sueldo = st.selectbox("Columna de Sueldo", options=columnas_df, index=idx_sueldo, key="col_sueldo")
        with col3:
            opciones_emp = ["(ninguna — cada fila = 1 empleado)"] + columnas_df
            if cols_detectadas["num_empleados"] and cols_detectadas["num_empleados"] in columnas_df:
                idx_emp = columnas_df.index(cols_detectadas["num_empleados"]) + 1
            else:
                idx_emp = 0
            col_empleados = st.selectbox("Columna de # Empleados", options=opciones_emp, index=idx_emp, key="col_emp")

        cada_fila_un_empleado = col_empleados == "(ninguna — cada fila = 1 empleado)"

        # --- Bruto / Neto ---
        st.markdown("#### Tipo de sueldo")
        tipo_sueldo_detectado = detectar_bruto_neto(df_raw, col_sueldo)

        col1, col2 = st.columns(2)
        with col1:
            opciones_bn = ["Bruto", "Neto"]
            idx_bn = 1 if tipo_sueldo_detectado == "neto" else 0
            tipo_sueldo = st.radio(
                "El sueldo del archivo es:",
                options=opciones_bn,
                index=idx_bn,
                horizontal=True,
                key="tipo_sueldo"
            )
            if tipo_sueldo_detectado != "desconocido":
                st.caption(f"Auto-detectado: **{tipo_sueldo_detectado}**")
        with col2:
            clase_riesgo_cot = st.selectbox(
                "Clase de riesgo IMSS",
                options=["I", "II", "III", "IV", "V"],
                key="riesgo_cotizador"
            )

        # --- Puesto mapping ---
        st.markdown("#### Mapeo de puestos al catalogo")

        df_trabajo = df_raw[[col_puesto, col_sueldo] + ([col_empleados] if not cada_fila_un_empleado else [])].copy()
        df_trabajo[col_sueldo] = pd.to_numeric(df_trabajo[col_sueldo], errors="coerce")
        df_trabajo = df_trabajo.dropna(subset=[col_sueldo])

        if not cada_fila_un_empleado:
            df_trabajo[col_empleados] = pd.to_numeric(df_trabajo[col_empleados], errors="coerce").fillna(1).astype(int)

        df_mapeo = mapear_puestos(df_trabajo[col_puesto])

        opciones_catalogo = sorted([p for p in PUESTOS_PROFESIONALES.keys()])

        df_editor = df_mapeo[["puesto_original", "puesto_catalogo", "minimo_profesional", "confianza"]].copy()
        df_editor.columns = ["Puesto Original", "Puesto Catalogo", "Min. Profesional", "Confianza"]

        baja_confianza = (df_editor["Confianza"] < 0.7).sum()
        if baja_confianza > 0:
            st.warning(f"Se encontraron **{baja_confianza}** puestos con baja confianza de mapeo. Revisa y corrige si es necesario.")

        df_editado = st.data_editor(
            df_editor,
            column_config={
                "Puesto Original": st.column_config.TextColumn("Puesto Original", disabled=True),
                "Puesto Catalogo": st.column_config.SelectboxColumn(
                    "Puesto Catalogo",
                    options=opciones_catalogo,
                    required=True,
                ),
                "Min. Profesional": st.column_config.NumberColumn("Min. Profesional", format="$%d"),
                "Confianza": st.column_config.ProgressColumn("Confianza", min_value=0, max_value=1, format="%.0f%%"),
            },
            use_container_width=True,
            hide_index=True,
            key="editor_puestos",
        )

        mapeo_final = {}
        for _, row in df_editado.iterrows():
            puesto_cat = row["Puesto Catalogo"]
            min_prof = PUESTOS_PROFESIONALES.get(puesto_cat, SALARIO_MINIMO_MENSUAL)
            mapeo_final[row["Puesto Original"]] = {
                "puesto_catalogo": puesto_cat,
                "minimo_profesional": min_prof,
            }

        # --- Validacion ---
        cols_val = {"puesto": col_puesto, "sueldo": col_sueldo,
                    "num_empleados": col_empleados if not cada_fila_un_empleado else None}
        warnings = validar_datos(df_raw, cols_val)
        if warnings:
            for w in warnings:
                st.warning(w)

        # --- Calcular ---
        st.markdown("---")
        if st.button("CALCULAR PROPUESTA", type="primary", use_container_width=True, key="calc_cotizador"):
            with st.spinner("Calculando propuesta..."):
                if cada_fila_un_empleado:
                    df_agrupado = df_trabajo.groupby([col_puesto, col_sueldo]).size().reset_index(name="num_empleados")
                else:
                    df_agrupado = df_trabajo.rename(columns={col_empleados: "num_empleados"})

                es_neto = tipo_sueldo == "Neto"

                resultados_grupos = []
                for _, fila in df_agrupado.iterrows():
                    puesto_orig = fila[col_puesto]
                    sueldo = fila[col_sueldo]
                    n_emp = int(fila["num_empleados"])

                    if n_emp <= 0:
                        continue

                    if es_neto:
                        sueldo_bruto = neto_a_bruto(sueldo, clase_riesgo_cot)
                    else:
                        sueldo_bruto = sueldo

                    info_puesto = mapeo_final.get(puesto_orig, {
                        "puesto_catalogo": "Otro (personalizado)",
                        "minimo_profesional": SALARIO_MINIMO_MENSUAL,
                    })

                    r = calcular_grupo_nomina(
                        puesto=info_puesto["puesto_catalogo"],
                        num_empleados=n_emp,
                        sueldo_bruto=sueldo_bruto,
                        clase_riesgo=clase_riesgo_cot,
                        minimo_profesional=info_puesto["minimo_profesional"],
                        comision_pct=comision_pct,
                    )
                    resultados_grupos.append(r)

                if resultados_grupos:
                    mostrar_resultados_nomina(resultados_grupos, comision_pct, nombre_empresa, contacto)
                else:
                    st.warning("No se encontraron datos validos para calcular.")


# ============================================================
# NOMINA COMPLETA (IRT) — Manual con base IMSS libre
# ============================================================
elif tipo == "nomina":
    st.markdown('<div class="section-header"><h3>Nomina IRT — Grupos de Empleados</h3></div>', unsafe_allow_html=True)
    st.markdown("Agrega los grupos de empleados con sus puestos, sueldos actuales y base IMSS deseada.")

    if "grupos" not in st.session_state:
        st.session_state.grupos = []

    with st.expander("Agregar grupo de empleados", expanded=len(st.session_state.grupos) == 0):
        col1, col2 = st.columns(2)
        with col1:
            puesto_sel = st.selectbox("Puesto (referencia)", options=LISTA_PUESTOS, key="puesto_nuevo")
            if puesto_sel == "Otro (personalizado)":
                puesto_custom = st.text_input("Nombre del puesto", key="puesto_custom")
            num_empleados = st.number_input("Numero de empleados", min_value=1, value=10, step=1, key="num_emp_nuevo")

        with col2:
            sueldo_bruto = st.number_input("Sueldo bruto mensual ($)", min_value=1000, value=15000, step=500, key="sueldo_nuevo")
            clase_riesgo = st.selectbox("Clase de riesgo IMSS", options=["I", "II", "III", "IV", "V"], key="riesgo_nuevo")

        # Base IMSS libre
        if puesto_sel != "Otro (personalizado)":
            min_prof_default = PUESTOS_PROFESIONALES.get(puesto_sel, SALARIO_MINIMO_MENSUAL)
        else:
            min_prof_default = SALARIO_MINIMO_MENSUAL

        st.markdown("---")
        st.markdown(f"**Base IMSS mensual** — Minimo profesional de referencia: **{fmt_moneda(min_prof_default)}**")
        base_imss_libre = st.number_input(
            "Base IMSS mensual ($)",
            min_value=float(SALARIO_MINIMO_MENSUAL),
            value=float(min_prof_default),
            step=500.0,
            key="base_imss_libre",
            help="Puedes poner cualquier monto >= salario minimo. El minimo profesional del puesto se muestra como referencia."
        )

        if st.button("Agregar grupo", type="primary", use_container_width=True):
            puesto_nombre = puesto_custom if puesto_sel == "Otro (personalizado)" else puesto_sel

            st.session_state.grupos.append({
                "puesto": puesto_nombre,
                "num_empleados": num_empleados,
                "sueldo_bruto": sueldo_bruto,
                "clase_riesgo": clase_riesgo,
                "minimo_profesional": base_imss_libre,
            })
            st.rerun()

    if st.session_state.grupos:
        st.markdown('<div class="section-header"><h3>Grupos capturados</h3></div>', unsafe_allow_html=True)
        df_grupos = pd.DataFrame(st.session_state.grupos)
        df_grupos.columns = ["Puesto", "# Empleados", "Sueldo Bruto", "Clase Riesgo", "Base IMSS"]
        df_display = df_grupos.copy()
        df_display["Sueldo Bruto"] = df_display["Sueldo Bruto"].apply(lambda x: fmt_moneda(x))
        df_display["Base IMSS"] = df_display["Base IMSS"].apply(lambda x: fmt_moneda(x))
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Eliminar ultimo grupo"):
                st.session_state.grupos.pop()
                st.rerun()
        with col2:
            if st.button("Limpiar todos"):
                st.session_state.grupos = []
                st.rerun()

        st.markdown("---")

        if st.button("CALCULAR PROPUESTA", type="primary", use_container_width=True):
            with st.spinner("Calculando propuesta..."):
                resultados_grupos = []
                for g in st.session_state.grupos:
                    r = calcular_grupo_nomina(
                        puesto=g["puesto"],
                        num_empleados=g["num_empleados"],
                        sueldo_bruto=g["sueldo_bruto"],
                        clase_riesgo=g["clase_riesgo"],
                        minimo_profesional=g["minimo_profesional"],
                        comision_pct=comision_pct,
                    )
                    resultados_grupos.append(r)

                mostrar_resultados_nomina(resultados_grupos, comision_pct, nombre_empresa, contacto)
    else:
        st.info("Agrega al menos un grupo de empleados para generar la propuesta.")


# ============================================================
# SOLO EXCEDENTES
# ============================================================
elif tipo == "excedentes":
    st.markdown('<div class="section-header"><h3>Administracion de Excedentes</h3></div>', unsafe_allow_html=True)
    st.markdown("Para bonos, comisiones, viaticos y otros conceptos excedentes al salario base.")

    monto_excedente = st.number_input("Monto total de excedentes mensuales ($)",
                                       min_value=1000, value=100000, step=5000)

    if st.button("CALCULAR PROPUESTA", type="primary", use_container_width=True):
        r = calcular_excedentes(monto_excedente, comision_pct)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Factura Mensual</h3>
                <p>{fmt_moneda(r['total_factura'])}</p>
                <p class="sub">Incluye IVA</p>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="ahorro-verde">
                <h3>Ahorro Mensual</h3>
                <p>{fmt_moneda(r['ahorro_mensual'])}</p>
                <p class="sub">vs nomina 100%</p>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="ahorro-verde">
                <h3>Ahorro Anual</h3>
                <p>{fmt_moneda(r['ahorro_anual'])}</p>
                <p class="sub">Proyeccion 12 meses</p>
            </div>""", unsafe_allow_html=True)

        # Comparativo visual
        import altair as alt
        st.markdown('<div class="section-header"><h3>Comparativo Excedentes vs Nomina</h3></div>', unsafe_allow_html=True)
        chart_data = pd.DataFrame({
            "Esquema": ["Costo Nomina Hipotetico", "Total Factura Excedentes"],
            "Monto": [r["costo_hipotetico_nomina"], r["total_factura"]]
        })
        chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Esquema:N", sort=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Monto:Q", axis=alt.Axis(format="$,.0f")),
            color=alt.Color("Esquema:N", scale=alt.Scale(
                domain=["Costo Nomina Hipotetico", "Total Factura Excedentes"],
                range=["#1B3A5C", "#27AE60"]
            ), legend=None),
            tooltip=[alt.Tooltip("Esquema:N"), alt.Tooltip("Monto:Q", format="$,.2f")]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

        st.markdown('<div class="section-header"><h3>Desglose</h3></div>', unsafe_allow_html=True)
        df = pd.DataFrame({
            "Concepto": ["Excedente", "Comision", "IVA", "Total factura",
                         "Costo si pagara por nomina", "Ahorro mensual"],
            "Monto": [fmt_moneda(r["monto_excedente"]), fmt_moneda(r["comision"]),
                      fmt_moneda(r["iva"]), fmt_moneda(r["total_factura"]),
                      fmt_moneda(r["costo_hipotetico_nomina"]), fmt_moneda(r["ahorro_mensual"])]
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Generar Word
        st.markdown("---")
        datos_cliente = {
            "nombre_empresa": nombre_empresa or "Cliente",
            "contacto": contacto or "Sin especificar",
            "comision_pct": comision_pct,
        }
        buffer = generar_propuesta_word(datos_cliente, "excedentes", r)
        nombre_archivo = f"Propuesta_Excedentes_{nombre_empresa or 'Cliente'}_{datetime.now().strftime('%Y%m%d')}.docx"
        st.download_button(
            label="DESCARGAR PROPUESTA EN WORD",
            data=buffer,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )


# ============================================================
# SOCIEDAD CIVIL — Piramidacion como modo default
# ============================================================
elif tipo == "sc":
    st.markdown('<div class="section-header"><h3>Sociedad Civil — Directivos y Gerenciales</h3></div>', unsafe_allow_html=True)
    st.markdown("Para perfiles que no cotizan en IMSS: directivos, socios, duenos.")

    if "directivos" not in st.session_state:
        st.session_state.directivos = []

    with st.expander("Agregar directivo/socio", expanded=len(st.session_state.directivos) == 0):
        nombre_dir = st.text_input("Nombre o identificador", placeholder="Director General", key="nombre_dir")

        col_sc1, col_sc2 = st.columns(2)
        with col_sc1:
            st.markdown("**Retencion ISR**")
            pct_anticipo = st.radio("% Anticipo por remanente", options=[10, 20], horizontal=True, key="pct_ant")
        with col_sc2:
            st.markdown("**Modo de captura**")
            modo_sc = st.radio(
                "Como quieres capturar?",
                options=["Piramidar (neto → bruto)", "Ingreso bruto directo"],
                index=0,
                key="modo_sc",
                horizontal=True,
            )

        piramidar = modo_sc == "Piramidar (neto → bruto)"

        if piramidar:
            neto_deseado = st.number_input("Neto deseado ($)", min_value=10000, value=100000, step=5000, key="neto_des")
            ingreso_total = 0
        else:
            ingreso_total = st.number_input("Ingreso total mensual ($)", min_value=10000, value=100000, step=5000, key="ing_total")
            neto_deseado = 0

        if st.button("Agregar directivo", type="primary", use_container_width=True):
            st.session_state.directivos.append({
                "nombre": nombre_dir or f"Directivo {len(st.session_state.directivos)+1}",
                "ingreso_total": ingreso_total,
                "pct_anticipo": pct_anticipo,
                "piramidar": piramidar,
                "neto_deseado": neto_deseado,
            })
            st.rerun()

    if st.session_state.directivos:
        st.markdown('<div class="section-header"><h3>Directivos capturados</h3></div>', unsafe_allow_html=True)
        for i, d in enumerate(st.session_state.directivos):
            modo = f"Piramidar → Neto {fmt_moneda(d['neto_deseado'])}" if d["piramidar"] else f"Ingreso {fmt_moneda(d['ingreso_total'])}"
            st.write(f"**{i+1}. {d['nombre']}** — {modo} — Anticipo {d['pct_anticipo']}%")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Eliminar ultimo"):
                st.session_state.directivos.pop()
                st.rerun()

        st.markdown("---")

        if st.button("CALCULAR PROPUESTA", type="primary", use_container_width=True):
            resultados_sc = []
            for d in st.session_state.directivos:
                r = calcular_sociedad_civil(
                    ingreso_total=d["ingreso_total"],
                    pct_anticipo=d["pct_anticipo"],
                    comision_pct=comision_pct,
                    piramidar=d["piramidar"],
                    neto_deseado=d["neto_deseado"],
                )
                r["nombre"] = d["nombre"]
                resultados_sc.append(r)

            for r in resultados_sc:
                st.markdown(f'<div class="section-header"><h3>{r["nombre"]}</h3></div>', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Ingreso Total</h3>
                        <p>{fmt_moneda(r['ingreso_total'])}</p>
                        <p class="sub">Bruto calculado</p>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Neto Directivo</h3>
                        <p>{fmt_moneda(r['neto_total'])}</p>
                        <p class="sub">Anticipo + Renta</p>
                    </div>""", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Total Factura</h3>
                        <p>{fmt_moneda(r['total_factura'])}</p>
                        <p class="sub">Con IVA</p>
                    </div>""", unsafe_allow_html=True)
                with col4:
                    pct_ahorro_sc = (r['ahorro_cliente_mensual'] / r['costo_nomina_100'] * 100) if r['costo_nomina_100'] > 0 else 0
                    st.markdown(f"""
                    <div class="ahorro-verde">
                        <h3>Ahorro Mensual</h3>
                        <p>{fmt_moneda(r['ahorro_cliente_mensual'])}</p>
                        <p class="sub">{pct_ahorro_sc:.1f}% vs nomina</p>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")

                # Comparativo visual SC vs Nomina
                import altair as alt
                chart_sc = pd.DataFrame({
                    "Esquema": ["Nomina 100%", "Sociedad Civil"],
                    "Costo": [r["costo_nomina_100"], r["ingreso_total"] + r["comision"]],
                    "Neto": [r["neto_nomina"], r["neto_total"]],
                })
                c_cost = alt.Chart(chart_sc).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X("Esquema:N", sort=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Costo:Q", axis=alt.Axis(format="$,.0f"), title="Costo Empresa (pre-IVA)"),
                    color=alt.Color("Esquema:N", scale=alt.Scale(
                        domain=["Nomina 100%", "Sociedad Civil"],
                        range=["#1B3A5C", "#27AE60"]
                    ), legend=None),
                    tooltip=[alt.Tooltip("Esquema:N"), alt.Tooltip("Costo:Q", format="$,.2f")]
                ).properties(height=280, title="Costo Empresa")

                c_neto = alt.Chart(chart_sc).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                    x=alt.X("Esquema:N", sort=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Neto:Q", axis=alt.Axis(format="$,.0f"), title="Neto Directivo"),
                    color=alt.Color("Esquema:N", scale=alt.Scale(
                        domain=["Nomina 100%", "Sociedad Civil"],
                        range=["#1B3A5C", "#C9A962"]
                    ), legend=None),
                    tooltip=[alt.Tooltip("Esquema:N"), alt.Tooltip("Neto:Q", format="$,.2f")]
                ).properties(height=280, title="Neto Directivo")

                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.altair_chart(c_cost, use_container_width=True)
                with chart_col2:
                    st.altair_chart(c_neto, use_container_width=True)

                df = pd.DataFrame({
                    "Concepto": ["Anticipo por remanente", "ISR sobre anticipo",
                                 "Renta vitalicia (exenta)", "Neto al directivo",
                                 "Comision", "IVA", "Total factura",
                                 "VS Nomina 100% (costo empresa)", "VS Nomina 100% (neto directivo)",
                                 "Ahorro mensual", "Ahorro anual"],
                    "Monto": [fmt_moneda(r["anticipo"]), fmt_moneda(r["isr_anticipo"]["isr_neto"]),
                              fmt_moneda(r["renta"]), fmt_moneda(r["neto_total"]),
                              fmt_moneda(r["comision"]), fmt_moneda(r["iva"]),
                              fmt_moneda(r["total_factura"]),
                              fmt_moneda(r["costo_nomina_100"]), fmt_moneda(r["neto_nomina"]),
                              fmt_moneda(r["ahorro_cliente_mensual"]), fmt_moneda(r["ahorro_cliente_anual"])]
                })
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.markdown("---")

            # Generar Word
            datos_cliente = {
                "nombre_empresa": nombre_empresa or "Cliente",
                "contacto": contacto or "Sin especificar",
                "comision_pct": comision_pct,
            }
            buffer = generar_propuesta_word(datos_cliente, "sc", resultados_sc)
            nombre_archivo = f"Propuesta_SC_{nombre_empresa or 'Cliente'}_{datetime.now().strftime('%Y%m%d')}.docx"
            st.download_button(
                label="DESCARGAR PROPUESTA EN WORD",
                data=buffer,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
            )
    else:
        st.info("Agrega al menos un directivo/socio para generar la propuesta.")

# === FOOTER ===
st.markdown("---")
st.markdown(
    f'<p style="text-align: center; color: #A0AEC0; font-size: 0.75rem; margin-top: 1rem;">'
    f'Sistema de Cotizacion Fiscal v3.0 &middot; Ano fiscal 2026 &middot; {estado_sel} (ISN {tasa_isn*100:.2f}%) &middot; '
    f'Uso interno exclusivo &middot; {datetime.now().strftime("%Y")}</p>',
    unsafe_allow_html=True
)
