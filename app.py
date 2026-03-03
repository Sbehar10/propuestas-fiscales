import streamlit as st
import pandas as pd
from datetime import datetime
from constantes import LISTA_PUESTOS, PUESTOS_PROFESIONALES, PRIMA_RIESGO
from motor_calculo import (
    calcular_esquema_actual, calcular_esquema_irt, calcular_excedentes,
    calcular_sociedad_civil, calcular_grupo_nomina
)
from generador_word import generar_propuesta_word, fmt_moneda

# === CONFIGURACION DE PAGINA ===
st.set_page_config(
    page_title="Generador de Propuestas Fiscales",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILOS CSS PERSONALIZADOS ===
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1B3A5C 0%, #2C5F8A 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: #C9A962 !important;
        font-size: 2rem !important;
        margin: 0 !important;
    }
    .main-header p {
        color: #FFFFFF !important;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }
    .metric-card {
        background: #1B3A5C;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #C9A962;
    }
    .metric-card h3 {
        color: #C9A962 !important;
        font-size: 0.85rem !important;
        margin: 0 !important;
        text-transform: uppercase;
    }
    .metric-card p {
        color: #FFFFFF !important;
        font-size: 1.8rem !important;
        font-weight: bold !important;
        margin: 0.5rem 0 0 0 !important;
    }
    .ahorro-verde {
        background: linear-gradient(135deg, #27AE60 0%, #2ECC71 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    .ahorro-verde h3 {
        color: #FFFFFF !important;
        font-size: 0.85rem !important;
        margin: 0 !important;
    }
    .ahorro-verde p {
        color: #FFFFFF !important;
        font-size: 2rem !important;
        font-weight: bold !important;
        margin: 0.5rem 0 0 0 !important;
    }
    .stButton>button {
        width: 100%;
    }
    div[data-testid="stSidebar"] {
        background-color: #0E1F33;
    }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown label {
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("""
<div class="main-header">
    <h1>📊 Generador de Propuestas Fiscales</h1>
    <p>Sistema de cotización y generación de propuestas para clientes — Año fiscal 2026</p>
</div>
""", unsafe_allow_html=True)

# === SIDEBAR — DATOS DEL CLIENTE ===
with st.sidebar:
    st.markdown("## 🏢 Datos del Cliente")
    nombre_empresa = st.text_input("Nombre de la empresa", placeholder="Grupo Industrial del Norte")
    contacto = st.text_input("Contacto", placeholder="Lic. Roberto Méndez")
    comision_pct = st.slider("Comisión (%)", min_value=2.0, max_value=8.0, value=5.0, step=0.5)

    st.markdown("---")
    st.markdown("## 📋 Tipo de Servicio")
    tipo_servicio = st.radio(
        "Selecciona el servicio:",
        options=["Nómina completa (IRT)", "Solo excedentes", "Sociedad Civil"],
        index=0
    )

    tipo_map = {
        "Nómina completa (IRT)": "nomina",
        "Solo excedentes": "excedentes",
        "Sociedad Civil": "sc",
    }
    tipo = tipo_map[tipo_servicio]

# === CONTENIDO PRINCIPAL ===

# ============================================================
# NÓMINA COMPLETA (IRT)
# ============================================================
if tipo == "nomina":
    st.markdown("### 👥 Grupos de Empleados")
    st.markdown("Agrega los grupos de empleados con sus puestos y sueldos actuales.")

    # Inicializar estado
    if "grupos" not in st.session_state:
        st.session_state.grupos = []

    # Botón agregar grupo
    with st.expander("➕ Agregar grupo de empleados", expanded=len(st.session_state.grupos) == 0):
        col1, col2 = st.columns(2)
        with col1:
            puesto_sel = st.selectbox("Puesto", options=LISTA_PUESTOS, key="puesto_nuevo")
            if puesto_sel == "Otro (personalizado)":
                puesto_custom = st.text_input("Nombre del puesto", key="puesto_custom")
                min_prof_custom = st.number_input("Salario mínimo profesional", min_value=0, value=10000, step=500, key="min_prof_custom")
            num_empleados = st.number_input("Número de empleados", min_value=1, value=10, step=1, key="num_emp_nuevo")

        with col2:
            sueldo_bruto = st.number_input("Sueldo bruto mensual ($)", min_value=1000, value=15000, step=500, key="sueldo_nuevo")
            clase_riesgo = st.selectbox("Clase de riesgo IMSS", options=["I", "II", "III", "IV", "V"], key="riesgo_nuevo")

            if puesto_sel != "Otro (personalizado)":
                min_prof = PUESTOS_PROFESIONALES.get(puesto_sel, 0)
                st.info(f"📌 Mínimo profesional asignado: **{fmt_moneda(min_prof)}**")
            else:
                min_prof = min_prof_custom if puesto_sel == "Otro (personalizado)" else 0

        if st.button("✅ Agregar grupo", type="primary"):
            puesto_nombre = puesto_custom if puesto_sel == "Otro (personalizado)" else puesto_sel
            min_p = min_prof_custom if puesto_sel == "Otro (personalizado)" else PUESTOS_PROFESIONALES.get(puesto_sel, 0)

            st.session_state.grupos.append({
                "puesto": puesto_nombre,
                "num_empleados": num_empleados,
                "sueldo_bruto": sueldo_bruto,
                "clase_riesgo": clase_riesgo,
                "minimo_profesional": min_p,
            })
            st.rerun()

    # Mostrar grupos capturados
    if st.session_state.grupos:
        st.markdown("#### Grupos capturados:")
        df_grupos = pd.DataFrame(st.session_state.grupos)
        df_grupos.columns = ["Puesto", "# Empleados", "Sueldo Bruto", "Clase Riesgo", "Mín. Profesional"]
        df_grupos["Sueldo Bruto"] = df_grupos["Sueldo Bruto"].apply(lambda x: fmt_moneda(x))
        df_grupos["Mín. Profesional"] = df_grupos["Mín. Profesional"].apply(lambda x: fmt_moneda(x))
        st.dataframe(df_grupos, use_container_width=True, hide_index=True)

        # Botón eliminar último grupo
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🗑️ Eliminar último grupo"):
                st.session_state.grupos.pop()
                st.rerun()
        with col2:
            if st.button("🗑️ Limpiar todos"):
                st.session_state.grupos = []
                st.rerun()

        st.markdown("---")

        # === CALCULAR ===
        if st.button("🔥 CALCULAR PROPUESTA", type="primary", use_container_width=True):
            with st.spinner("Calculando..."):
                resultados_grupos = []
                costo_actual_total = 0
                ahorro_total = 0
                total_empleados = 0
                total_administrado = 0

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
                    costo_actual_total += r["actual"]["costo_total"]
                    ahorro_total += r["ahorro_mensual"]
                    total_empleados += g["num_empleados"]
                    total_administrado += g["sueldo_bruto"] * g["num_empleados"]

                # Métricas principales
                st.markdown("### 📊 Resultados")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Costo Actual Mensual</h3>
                        <p>{fmt_moneda(costo_actual_total)}</p>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Empleados</h3>
                        <p>{total_empleados}</p>
                    </div>""", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="ahorro-verde">
                        <h3>Ahorro Mensual IRT</h3>
                        <p>{fmt_moneda(ahorro_total)}</p>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")
                pct_ahorro = (ahorro_total / costo_actual_total * 100) if costo_actual_total > 0 else 0

                # Tabla resumen — Proyección de Ahorro
                st.markdown("#### Proyección de Ahorro")
                df_ahorro = pd.DataFrame({
                    "Período": ["Mensual", "Anual", "2 Años", "3 Años"],
                    "Ahorro IRT": [fmt_moneda(ahorro_total), fmt_moneda(ahorro_total * 12),
                                    fmt_moneda(ahorro_total * 24), fmt_moneda(ahorro_total * 36)],
                    "% Ahorro": [f"{pct_ahorro:.1f}%"] * 4,
                })
                st.dataframe(df_ahorro, use_container_width=True, hide_index=True)

                # Gráfica comparativa
                st.markdown("#### Comparativo de Costos")
                import altair as alt
                chart_data = pd.DataFrame({
                    "Esquema": ["Actual (100%)", "IRT Propuesto"],
                    "Costo Mensual": [costo_actual_total, costo_actual_total - ahorro_total]
                })
                chart = alt.Chart(chart_data).mark_bar().encode(
                    x=alt.X("Esquema", sort=None),
                    y="Costo Mensual",
                    color=alt.Color("Esquema", scale=alt.Scale(
                        domain=["Actual (100%)", "IRT Propuesto"],
                        range=["#1B3A5C", "#27AE60"]
                    ))
                ).properties(height=350)
                st.altair_chart(chart, use_container_width=True)

                # Detalle por grupo
                st.markdown("#### Detalle por Grupo")
                for r in resultados_grupos:
                    with st.expander(f"📋 {r['puesto']} — {r['num_empleados']} empleados a {fmt_moneda(r['sueldo_bruto'])}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Costo actual/mes", fmt_moneda(r["actual"]["costo_total"]))
                        with col2:
                            st.metric("Ahorro IRT/mes", fmt_moneda(r["ahorro_mensual"]))

                        st.write(f"**Base nómina IRT:** {fmt_moneda(r['irt']['base_nomina'])} | "
                                 f"**Excedente IRT:** {fmt_moneda(r['irt']['excedente_irt'])}")
                        st.write(f"**Neto trabajador actual:** {fmt_moneda(r['actual']['neto_trabajador'])} → "
                                 f"**IRT:** {fmt_moneda(r['irt']['neto_trabajador'])}")

                # === GENERAR WORD ===
                st.markdown("---")
                st.markdown("### 📄 Descargar Propuesta en Word")

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

                buffer = generar_propuesta_word(
                    datos_cliente=datos_cliente,
                    tipo_servicio="nomina",
                    resultados=resultados_word,
                    grupos=resultados_grupos,
                )

                nombre_archivo = f"Propuesta_{nombre_empresa or 'Cliente'}_{datetime.now().strftime('%Y%m%d')}.docx"
                st.download_button(
                    label="⬇️ DESCARGAR PROPUESTA EN WORD",
                    data=buffer,
                    file_name=nombre_archivo,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                )
    else:
        st.info("👆 Agrega al menos un grupo de empleados para generar la propuesta.")


# ============================================================
# SOLO EXCEDENTES
# ============================================================
elif tipo == "excedentes":
    st.markdown("### 💰 Administración de Excedentes")
    st.markdown("Para bonos, comisiones, viáticos y otros conceptos excedentes al salario base.")

    monto_excedente = st.number_input("Monto total de excedentes mensuales ($)",
                                       min_value=1000, value=100000, step=5000)

    if st.button("🔥 CALCULAR PROPUESTA", type="primary", use_container_width=True):
        r = calcular_excedentes(monto_excedente, comision_pct)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Factura Mensual</h3>
                <p>{fmt_moneda(r['total_factura'])}</p>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="ahorro-verde">
                <h3>Ahorro Mensual</h3>
                <p>{fmt_moneda(r['ahorro_mensual'])}</p>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="ahorro-verde">
                <h3>Ahorro Anual</h3>
                <p>{fmt_moneda(r['ahorro_anual'])}</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("#### Desglose")
        df = pd.DataFrame({
            "Concepto": ["Excedente", "Comisión", "IVA", "Total factura",
                         "Costo si pagara por nómina", "Ahorro mensual"],
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
            label="⬇️ DESCARGAR PROPUESTA EN WORD",
            data=buffer,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )


# ============================================================
# SOCIEDAD CIVIL
# ============================================================
elif tipo == "sc":
    st.markdown("### 🏛️ Sociedad Civil — Directivos y Gerenciales")
    st.markdown("Para perfiles que no tienen IMSS: directivos, socios, dueños.")

    if "directivos" not in st.session_state:
        st.session_state.directivos = []

    with st.expander("➕ Agregar directivo/socio", expanded=len(st.session_state.directivos) == 0):
        nombre_dir = st.text_input("Nombre o identificador", placeholder="Director General", key="nombre_dir")
        pct_anticipo = st.radio("% Anticipo por remanente", options=[10, 20], horizontal=True, key="pct_ant")
        piramidar = st.checkbox("¿Pirámidar? (calcular bruto desde neto deseado)", key="piram")

        if piramidar:
            neto_deseado = st.number_input("Neto deseado ($)", min_value=10000, value=100000, step=5000, key="neto_des")
            ingreso_total = 0
        else:
            ingreso_total = st.number_input("Ingreso total mensual ($)", min_value=10000, value=100000, step=5000, key="ing_total")
            neto_deseado = 0

        if st.button("✅ Agregar directivo", type="primary"):
            st.session_state.directivos.append({
                "nombre": nombre_dir or f"Directivo {len(st.session_state.directivos)+1}",
                "ingreso_total": ingreso_total,
                "pct_anticipo": pct_anticipo,
                "piramidar": piramidar,
                "neto_deseado": neto_deseado,
            })
            st.rerun()

    if st.session_state.directivos:
        st.markdown("#### Directivos capturados:")
        for i, d in enumerate(st.session_state.directivos):
            modo = f"Pirámidar → Neto {fmt_moneda(d['neto_deseado'])}" if d["piramidar"] else f"Ingreso {fmt_moneda(d['ingreso_total'])}"
            st.write(f"**{i+1}. {d['nombre']}** — {modo} — Anticipo {d['pct_anticipo']}%")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🗑️ Eliminar último"):
                st.session_state.directivos.pop()
                st.rerun()

        st.markdown("---")

        if st.button("🔥 CALCULAR PROPUESTA", type="primary", use_container_width=True):
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
                st.markdown(f"#### {r['nombre']}")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Ingreso Total</h3>
                        <p>{fmt_moneda(r['ingreso_total'])}</p>
                    </div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Neto Directivo</h3>
                        <p>{fmt_moneda(r['neto_total'])}</p>
                    </div>""", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Total Factura</h3>
                        <p>{fmt_moneda(r['total_factura'])}</p>
                    </div>""", unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div class="ahorro-verde">
                        <h3>Ahorro Mensual</h3>
                        <p>{fmt_moneda(r['ahorro_cliente_mensual'])}</p>
                    </div>""", unsafe_allow_html=True)

                st.markdown("")
                df = pd.DataFrame({
                    "Concepto": ["Anticipo por remanente", "ISR sobre anticipo",
                                 "Renta vitalicia (exenta)", "Neto al directivo",
                                 "Comisión", "IVA", "Total factura",
                                 "VS Nómina 100% (costo empresa)", "VS Nómina 100% (neto directivo)",
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
                label="⬇️ DESCARGAR PROPUESTA EN WORD",
                data=buffer,
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
            )
    else:
        st.info("👆 Agrega al menos un directivo/socio para generar la propuesta.")

# === FOOTER ===
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888; font-size: 0.8rem;'>"
    "Generador de Propuestas Fiscales v2.0 — Año fiscal 2026 — Uso interno exclusivo — "
    f"{datetime.now().strftime('%Y')}</p>",
    unsafe_allow_html=True
)
