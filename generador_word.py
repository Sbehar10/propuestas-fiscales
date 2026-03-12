# generador_word.py — Generador de documentos Word profesionales
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
import io
from datetime import datetime


# Colores corporativos
AZUL_OSCURO = RGBColor(0x1B, 0x3A, 0x5C)
DORADO = RGBColor(0xC9, 0xA9, 0x62)
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
GRIS_CLARO = RGBColor(0xF2, 0xF2, 0xF2)
VERDE = RGBColor(0x27, 0xAE, 0x60)
NEGRO = RGBColor(0x33, 0x33, 0x33)


def fmt_moneda(valor):
    """Formatea número como moneda mexicana"""
    if valor is None:
        return "$0.00"
    return f"${valor:,.2f}"


def fmt_pct(valor):
    """Formatea porcentaje"""
    return f"{valor:.2f}%"


def set_cell_shading(cell, color_hex):
    """Aplica sombreado a celda"""
    shading = cell._element.get_or_add_tcPr()
    shading_elem = shading.makeelement(qn('w:shd'), {
        qn('w:fill'): color_hex,
        qn('w:val'): 'clear'
    })
    shading.append(shading_elem)


def agregar_tabla_estilizada(doc, headers, rows, col_widths=None):
    """Crea tabla profesional con estilo corporativo"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    # Header
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(header)
        run.bold = True
        run.font.color.rgb = BLANCO
        run.font.size = Pt(9)
        run.font.name = 'Arial'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_shading(cell, "1B3A5C")

    # Rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, value in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(value))
            run.font.size = Pt(8.5)
            run.font.name = 'Arial'
            run.font.color.rgb = NEGRO
            if c_idx > 0:  # Columnas numéricas alineadas a la derecha
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if r_idx % 2 == 1:
                set_cell_shading(cell, "F7F7F7")

    # Última fila en bold si es TOTAL
    if rows and "TOTAL" in str(rows[-1][0]).upper():
        for c_idx in range(len(headers)):
            cell = table.rows[len(rows)].cells[c_idx]
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
            set_cell_shading(cell, "E8E8E8")

    if col_widths:
        for i, width in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(width)

    return table


def generar_propuesta_word(datos_cliente, tipo_servicio, resultados, grupos=None):
    """
    Genera documento Word con la propuesta completa.

    datos_cliente: dict con nombre_empresa, contacto, comision_pct
    tipo_servicio: "nomina", "excedentes", "sc"
    resultados: dict con los cálculos según el tipo de servicio
    grupos: lista de dicts para nómina completa
    """
    doc = Document()

    # Configurar márgenes
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # === PORTADA ===
    _generar_portada(doc, datos_cliente, tipo_servicio)

    # === RESUMEN EJECUTIVO ===
    doc.add_page_break()
    _generar_resumen_ejecutivo(doc, datos_cliente, tipo_servicio, resultados)

    # === CONTENIDO SEGÚN TIPO DE SERVICIO ===
    if tipo_servicio == "nomina" and grupos:
        _generar_seccion_diagnostico(doc, grupos)
        _generar_seccion_propuesta_irt(doc, grupos)
        _generar_seccion_ahorro(doc, resultados, tipo_servicio)
        _generar_seccion_facturacion(doc, datos_cliente, resultados, tipo_servicio)

    elif tipo_servicio == "excedentes":
        _generar_seccion_excedentes(doc, resultados)

    elif tipo_servicio == "sc":
        _generar_seccion_sc(doc, resultados)

    # === FUNDAMENTO LEGAL ===
    doc.add_page_break()
    _generar_fundamento_legal(doc, tipo_servicio)

    # === PLAN DE IMPLEMENTACIÓN ===
    _generar_plan_implementacion(doc, tipo_servicio)

    # === FOOTER ===
    _agregar_footer(doc, datos_cliente["nombre_empresa"])

    # Guardar a buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def _generar_portada(doc, datos_cliente, tipo_servicio):
    """Genera página de portada"""
    # Espacio superior
    for _ in range(4):
        doc.add_paragraph("")

    # Logo placeholder
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("■ LOGO EMPRESA ■")
    run.font.size = Pt(24)
    run.font.color.rgb = AZUL_OSCURO
    run.bold = True

    doc.add_paragraph("")

    # Línea dorada
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("━" * 50)
    run.font.color.rgb = DORADO
    run.font.size = Pt(12)

    doc.add_paragraph("")

    # Título
    titulos = {
        "nomina": "Propuesta de Servicios Especializados\nde Administración de Nómina",
        "excedentes": "Propuesta de Administración\nde Excedentes",
        "sc": "Propuesta de Optimización Fiscal\nvía Sociedad Civil",
    }
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(titulos.get(tipo_servicio, "Propuesta de Servicios"))
    run.font.size = Pt(26)
    run.font.color.rgb = AZUL_OSCURO
    run.bold = True
    run.font.name = 'Arial'

    doc.add_paragraph("")

    # Datos del cliente
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Preparada para:\n{datos_cliente['nombre_empresa']}")
    run.font.size = Pt(16)
    run.font.color.rgb = NEGRO
    run.font.name = 'Arial'

    doc.add_paragraph("")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Atención: {datos_cliente['contacto']}")
    run.font.size = Pt(12)
    run.font.color.rgb = NEGRO

    doc.add_paragraph("")

    # Fecha
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(datetime.now().strftime("%d de %B de %Y"))
    run.font.size = Pt(11)
    run.font.color.rgb = AZUL_OSCURO

    # Línea dorada inferior
    doc.add_paragraph("")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("━" * 50)
    run.font.color.rgb = DORADO

    # Confidencial
    doc.add_paragraph("")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("CONFIDENCIAL")
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    run.bold = True


def _generar_resumen_ejecutivo(doc, datos_cliente, tipo_servicio, resultados):
    """Sección de resumen ejecutivo"""
    h = doc.add_heading("1. Resumen Ejecutivo", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    if tipo_servicio == "nomina":
        total_empleados = resultados.get("total_empleados", 0)
        ahorro_mensual = resultados.get("ahorro_total_mensual", 0)
        es_neto = resultados.get("es_neto", False)

        doc.add_paragraph(
            f"La presente propuesta contempla la administración de nómina para "
            f"{total_empleados} colaboradores mediante un esquema de servicios especializados "
            f"con REPSE vigente, optimizando la carga fiscal y patronal de su empresa."
        )

        if es_neto:
            p = doc.add_paragraph()
            run = p.add_run(
                "Sus empleados siguen recibiendo el mismo neto. "
                "Lo que cambia es el costo patronal."
            )
            run.bold = True
            run.font.color.rgb = VERDE

        # Tabla resumen de ahorro
        headers = ["Concepto", "IRT Propuesto"]
        rows = [
            ["Empleados administrados", str(total_empleados)],
            ["Ahorro mensual", fmt_moneda(ahorro_mensual)],
            ["Ahorro anual", fmt_moneda(ahorro_mensual * 12)],
            ["Ahorro a 3 años", fmt_moneda(ahorro_mensual * 36)],
        ]
        agregar_tabla_estilizada(doc, headers, rows)

    elif tipo_servicio == "excedentes":
        doc.add_paragraph(
            f"La presente propuesta contempla la administración de excedentes salariales "
            f"(bonos, comisiones, viáticos) a través de un esquema exento, generando un "
            f"ahorro significativo para su empresa."
        )
        ahorro = resultados.get("ahorro_mensual", 0)
        headers = ["Concepto", "Monto"]
        rows = [
            ["Excedente mensual administrado", fmt_moneda(resultados.get("monto_excedente", 0))],
            ["Ahorro mensual", fmt_moneda(ahorro)],
            ["Ahorro anual", fmt_moneda(ahorro * 12)],
        ]
        agregar_tabla_estilizada(doc, headers, rows)

    elif tipo_servicio == "sc":
        doc.add_paragraph(
            f"La presente propuesta contempla la optimización fiscal para perfiles directivos "
            f"y gerenciales a través de una Sociedad Civil, donde el ingreso se divide entre "
            f"anticipo por remanente (gravado) y renta vitalicia (exenta al 100%)."
        )
        if isinstance(resultados, list):
            for r in resultados:
                _tabla_resumen_sc(doc, r)
        else:
            _tabla_resumen_sc(doc, resultados)


def _tabla_resumen_sc(doc, r):
    """Mini tabla resumen para un directivo SC"""
    headers = ["Concepto", "Esquema Actual (Nómina)", "Esquema SC"]
    rows = [
        ["Ingreso total", fmt_moneda(r["ingreso_total"]), fmt_moneda(r["ingreso_total"])],
        ["ISR retenido", fmt_moneda(r["isr_nomina"]["isr_neto"]), fmt_moneda(r["isr_anticipo"]["isr_neto"])],
        ["Neto al directivo", fmt_moneda(r["neto_nomina"]), fmt_moneda(r["neto_total"])],
        ["Costo total empresa", fmt_moneda(r["costo_nomina_100"]), fmt_moneda(r["total_factura"])],
        ["Ahorro mensual", "—", fmt_moneda(r["ahorro_cliente_mensual"])],
    ]
    agregar_tabla_estilizada(doc, headers, rows)
    doc.add_paragraph("")


def _generar_seccion_diagnostico(doc, grupos):
    """Sección 2: Diagnóstico fiscal actual"""
    doc.add_page_break()
    h = doc.add_heading("2. Diagnóstico Fiscal Actual", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    doc.add_paragraph(
        "A continuación se presenta el costo actual que representa la nómina "
        "de los colaboradores bajo un esquema 100% formal ante el IMSS."
    )

    headers = ["Puesto", "Cant.", "Sueldo Bruto", "ISR", "IMSS Pat.", "IMSS Obr.",
               "Infonavit", "ISN", "Costo Total/Mes"]
    rows = []
    totales = {"isr": 0, "imss_pat": 0, "imss_obr": 0, "info": 0, "isn": 0, "costo": 0}

    for g in grupos:
        a = g["actual"]
        n = g["num_empleados"]
        row = [
            g["puesto"],
            str(n),
            fmt_moneda(a["sueldo_bruto"]),
            fmt_moneda(a["isr"]["isr_neto"] * n),
            fmt_moneda(a["imss_patronal"]["total"] * n),
            fmt_moneda(a["imss_obrero"]["total"] * n),
            fmt_moneda(a["infonavit"] * n),
            fmt_moneda(a["isn"] * n),
            fmt_moneda(a["costo_total"]),
        ]
        rows.append(row)
        totales["isr"] += a["isr"]["isr_neto"] * n
        totales["imss_pat"] += a["imss_patronal"]["total"] * n
        totales["imss_obr"] += a["imss_obrero"]["total"] * n
        totales["info"] += a["infonavit"] * n
        totales["isn"] += a["isn"] * n
        totales["costo"] += a["costo_total"]

    rows.append([
        "TOTAL", "",  "",
        fmt_moneda(totales["isr"]),
        fmt_moneda(totales["imss_pat"]),
        fmt_moneda(totales["imss_obr"]),
        fmt_moneda(totales["info"]),
        fmt_moneda(totales["isn"]),
        fmt_moneda(totales["costo"]),
    ])

    agregar_tabla_estilizada(doc, headers, rows)


def _generar_seccion_propuesta_irt(doc, grupos):
    """Sección 3: Propuesta IRT con comparativo Actual vs IRT"""
    doc.add_page_break()
    h = doc.add_heading("3. Propuesta de Optimización — IRT", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    doc.add_paragraph(
        "Se propone optimizar la carga fiscal y patronal mediante un esquema de "
        "Indemnización por Riesgo de Trabajo (IRT), donde se cotiza al colaborador "
        "con el salario mínimo profesional correspondiente a su puesto según la tabla "
        "del IMSS, y el excedente se paga como concepto exento conforme al Art. 93 "
        "fracción III de la LISR."
    )

    for g in grupos:
        neto_orig = g.get("sueldo_neto_original")
        h2 = doc.add_heading(f"{g['puesto']} ({g['num_empleados']} empleados)", level=2)
        for run in h2.runs:
            run.font.color.rgb = AZUL_OSCURO

        headers = ["Concepto", "Actual (100%)", "IRT Propuesto"]
        a = g["actual"]
        irt = g["irt"]

        rows = []
        if neto_orig:
            rows.append(["Sueldo neto del empleado", fmt_moneda(neto_orig), fmt_moneda(neto_orig) + " (sin cambio)"])
            rows.append(["Bruto equivalente", fmt_moneda(a["sueldo_bruto"]), fmt_moneda(a["sueldo_bruto"])])
        else:
            rows.append(["Sueldo bruto", fmt_moneda(a["sueldo_bruto"]), fmt_moneda(a["sueldo_bruto"])])
        rows += [
            ["Base nómina (IMSS)", fmt_moneda(a["sueldo_bruto"]), fmt_moneda(irt["base_nomina"])],
            ["Excedente IRT (exento)", "—", fmt_moneda(irt["excedente_irt"])],
            ["ISR mensual", fmt_moneda(a["isr"]["isr_neto"]), fmt_moneda(irt["isr"]["isr_neto"])],
            ["IMSS patronal", fmt_moneda(a["imss_patronal"]["total"]), fmt_moneda(irt["imss_patronal"]["total"])],
            ["IMSS obrero", fmt_moneda(a["imss_obrero"]["total"]), fmt_moneda(irt["imss_obrero"]["total"])],
            ["Infonavit", fmt_moneda(a["infonavit"]), fmt_moneda(irt["infonavit"])],
            ["ISN", fmt_moneda(a["isn"]), fmt_moneda(irt["isn"])],
            ["Neto trabajador", fmt_moneda(a["neto_trabajador"]), fmt_moneda(irt["neto_trabajador"])],
        ]
        agregar_tabla_estilizada(doc, headers, rows)
        doc.add_paragraph("")


def _generar_seccion_ahorro(doc, resultados, tipo_servicio):
    """Sección 4: Análisis de ahorro"""
    doc.add_page_break()
    h = doc.add_heading("4. Análisis de Ahorro", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    costo_actual = resultados.get("costo_actual_total", 0)
    ahorro = resultados.get("ahorro_total_mensual", 0)
    pct = (ahorro / costo_actual * 100) if costo_actual > 0 else 0

    headers = ["Período", "Ahorro IRT", "% Ahorro"]
    rows = [
        ["Mensual", fmt_moneda(ahorro), fmt_pct(pct)],
        ["Anual", fmt_moneda(ahorro * 12), fmt_pct(pct)],
        ["2 años", fmt_moneda(ahorro * 24), fmt_pct(pct)],
        ["3 años", fmt_moneda(ahorro * 36), fmt_pct(pct)],
    ]
    agregar_tabla_estilizada(doc, headers, rows)

    # Párrafo destacado
    doc.add_paragraph("")
    p = doc.add_paragraph()
    run = p.add_run(f"Ahorro proyectado a 3 años: {fmt_moneda(ahorro * 36)}")
    run.font.size = Pt(14)
    run.font.color.rgb = VERDE
    run.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _generar_seccion_facturacion(doc, datos_cliente, resultados, tipo_servicio):
    """Sección 5: Detalle de facturación"""
    h = doc.add_heading("5. Detalle de Facturación", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    doc.add_paragraph(
        "La facturación mensual se compone de la siguiente manera:"
    )

    comision_pct = datos_cliente["comision_pct"]
    total_admin = resultados.get("total_administrado", 0)
    # Use pre-calculated values from app.py (same as screen display)
    comision = resultados.get("total_comision", round(total_admin * (comision_pct / 100), 2))
    subtotal = resultados.get("subtotal_factura", total_admin + comision)
    iva = resultados.get("iva_total", round(subtotal * 0.16, 2))
    total = resultados.get("total_factura", subtotal + iva)

    headers = ["Concepto", "Monto"]
    rows = [
        ["Nómina total administrada", fmt_moneda(total_admin)],
        [f"Comisión ({comision_pct}%)", fmt_moneda(comision)],
        ["Subtotal", fmt_moneda(subtotal)],
        ["IVA (16%)", fmt_moneda(iva)],
        ["TOTAL FACTURA MENSUAL", fmt_moneda(total)],
    ]
    agregar_tabla_estilizada(doc, headers, rows)

    doc.add_paragraph("")
    doc.add_paragraph(
        "El gasto total es 100% deducible para efectos del ISR de su empresa, "
        "ya que se trata de un servicio especializado facturado con IVA y CFDI vigente."
    )


def _generar_seccion_excedentes(doc, resultados):
    """Sección específica para excedentes"""
    h = doc.add_heading("2. Análisis de Excedentes", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    headers = ["Concepto", "Monto"]
    rows = [
        ["Excedente mensual", fmt_moneda(resultados["monto_excedente"])],
        ["Comisión", fmt_moneda(resultados["comision"])],
        ["IVA", fmt_moneda(resultados["iva"])],
        ["Total factura mensual", fmt_moneda(resultados["total_factura"])],
        ["", ""],
        ["Costo si pagara por nómina", fmt_moneda(resultados["costo_hipotetico_nomina"])],
        ["Ahorro mensual", fmt_moneda(resultados["ahorro_mensual"])],
        ["Ahorro anual", fmt_moneda(resultados["ahorro_anual"])],
    ]
    agregar_tabla_estilizada(doc, headers, rows)


def _generar_seccion_sc(doc, resultados):
    """Sección específica para Sociedad Civil"""
    h = doc.add_heading("2. Análisis Sociedad Civil", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    doc.add_paragraph(
        "El ingreso del directivo/socio se estructura de la siguiente manera a través "
        "de la Sociedad Civil, dividiendo entre anticipo por remanente (gravado, con "
        "retención ISR Art. 96) y renta vitalicia (exenta al 100%, Art. 93 fr. IV LISR)."
    )

    lista = resultados if isinstance(resultados, list) else [resultados]
    for r in lista:
        h2 = doc.add_heading(f"Ingreso: {fmt_moneda(r['ingreso_total'])} — Anticipo {r['pct_anticipo']}%", level=2)

        headers = ["Concepto", "Monto"]
        rows = [
            ["Ingreso total", fmt_moneda(r["ingreso_total"])],
            [f"Anticipo por remanente ({r['pct_anticipo']}%)", fmt_moneda(r["anticipo"])],
            ["ISR sobre anticipo", fmt_moneda(r["isr_anticipo"]["isr_neto"])],
            ["Renta vitalicia (exenta)", fmt_moneda(r["renta"])],
            ["Neto al directivo", fmt_moneda(r["neto_total"])],
            ["", ""],
            ["Comisión", fmt_moneda(r["comision"])],
            ["IVA", fmt_moneda(r["iva"])],
            ["Total factura", fmt_moneda(r["total_factura"])],
            ["", ""],
            ["VS Nómina 100% — Costo empresa", fmt_moneda(r["costo_nomina_100"])],
            ["VS Nómina 100% — Neto directivo", fmt_moneda(r["neto_nomina"])],
            ["Ahorro mensual", fmt_moneda(r["ahorro_cliente_mensual"])],
            ["Ahorro anual", fmt_moneda(r["ahorro_cliente_anual"])],
        ]
        agregar_tabla_estilizada(doc, headers, rows)
        doc.add_paragraph("")


def _generar_fundamento_legal(doc, tipo_servicio):
    """Sección de fundamento legal"""
    h = doc.add_heading("Fundamento Legal", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    if tipo_servicio in ("nomina", "excedentes"):
        doc.add_paragraph(
            "El presente esquema se sustenta en los siguientes ordenamientos legales:"
        )
        fundamentos = [
            "Art. 93 fracción III LISR — Exención de indemnizaciones por riesgos o enfermedades.",
            "Art. 93 fracción XIII LISR — Exención de viáticos efectivamente erogados.",
            "NOM-035-STPS-2018 — Factores de riesgo psicosocial en el trabajo.",
            "Art. 15-A Ley Federal del Trabajo — Servicios especializados.",
            "Art. 13 Ley del Seguro Social — Obligaciones del patrón.",
            "Registro REPSE vigente ante la STPS.",
        ]
        for f in fundamentos:
            p = doc.add_paragraph(f)
            p.style = 'List Bullet'

    elif tipo_servicio == "sc":
        doc.add_paragraph(
            "El esquema de Sociedad Civil se fundamenta en:"
        )
        fundamentos = [
            "Art. 94 fracción II LISR — Ingresos asimilados a salarios por anticipos de remanente.",
            "Art. 96 LISR — Tabla de retención de ISR a personas físicas.",
            "Art. 93 fracción IV LISR — Exención de rentas vitalicias.",
            "Art. 86 LISR — Obligaciones de personas morales con fines no lucrativos.",
            "Código Civil Federal — Constitución y operación de Sociedades Civiles.",
        ]
        for f in fundamentos:
            p = doc.add_paragraph(f)
            p.style = 'List Bullet'


def _generar_plan_implementacion(doc, tipo_servicio):
    """Plan de implementación por fases"""
    doc.add_paragraph("")
    h = doc.add_heading("Plan de Implementación", level=1)
    for run in h.runs:
        run.font.color.rgb = AZUL_OSCURO

    fases = [
        ("Fase 1 — Diagnóstico (Semana 1)", "Recepción de nómina actual, análisis de puestos, asignación de salarios mínimos profesionales y segmentación por actividad."),
        ("Fase 2 — Estructuración (Semana 2)", "Alta de personal en empresas con REPSE correspondiente, configuración de esquema de pago y validación de cálculos."),
        ("Fase 3 — Migración (Semana 3-4)", "Transición de colaboradores, primer dispersión de nómina bajo nuevo esquema, validación de CFDIs."),
        ("Fase 4 — Operación continua", "Dispersión quincenal/mensual, reportes de nómina, conciliaciones, cumplimiento de obligaciones fiscales y laborales."),
    ]

    for titulo, descripcion in fases:
        h2 = doc.add_heading(titulo, level=2)
        for run in h2.runs:
            run.font.color.rgb = DORADO
            run.font.size = Pt(12)
        doc.add_paragraph(descripcion)

    doc.add_paragraph("")
    doc.add_paragraph("Requisitos documentales del cliente:")
    reqs = [
        "Nómina actual completa (puestos, sueldos, prestaciones)",
        "Comprobante de inscripción fiscal (CIF)",
        "Organigrama o descripción de puestos",
        "Contrato de servicios especializado firmado",
    ]
    for r in reqs:
        p = doc.add_paragraph(r)
        p.style = 'List Bullet'


def _agregar_footer(doc, nombre_empresa):
    """Agrega footer con leyenda de confidencialidad"""
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"CONFIDENCIAL — Propuesta preparada exclusivamente para {nombre_empresa}")
        run.font.size = Pt(7)
        run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        run.font.name = 'Arial'
