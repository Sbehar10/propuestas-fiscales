# motor_calculo.py — Motor de cálculo fiscal
# ISR, IMSS desglosado, IRT, Excedentes, Sociedad Civil

from constantes import *


# ============================================================
# CÁLCULO DE ISR MENSUAL
# ============================================================
def calcular_isr(base_gravable):
    """Calcula ISR mensual según tabla Art. 96 LISR 2026"""
    if base_gravable <= 0:
        return {"isr": 0, "subsidio": 0, "isr_neto": 0, "lim_inf": 0, "excedente": 0,
                "imp_marginal": 0, "cuota_fija": 0, "pct": 0}

    rango = TABLA_ISR_MENSUAL[-1]
    for r in TABLA_ISR_MENSUAL:
        if r["lim_inf"] <= base_gravable <= r["lim_sup"]:
            rango = r
            break

    excedente = base_gravable - rango["lim_inf"]
    imp_marginal = excedente * (rango["pct_excedente"] / 100)
    isr_causado = imp_marginal + rango["cuota_fija"]

    # Subsidio al empleo (reforma 2024+: monto fijo si ingreso <= límite)
    subsidio = SUBSIDIO_MENSUAL if base_gravable <= SUBSIDIO_LIMITE_INGRESOS else 0
    isr_neto = max(isr_causado - subsidio, 0)

    return {
        "isr": isr_causado,
        "subsidio": subsidio,
        "isr_neto": isr_neto,
        "lim_inf": rango["lim_inf"],
        "excedente": excedente,
        "imp_marginal": imp_marginal,
        "cuota_fija": rango["cuota_fija"],
        "pct": rango["pct_excedente"],
    }


# ============================================================
# TASA CESANTÍA Y VEJEZ PATRONAL (tabla graduada 2026)
# ============================================================
def obtener_tasa_cesantia_patronal(sbc_mensual):
    """Determina la tasa patronal de cesantía y vejez según rango de SBC en UMAs"""
    sbc_diario = sbc_mensual / 30.4
    ratio_uma = sbc_diario / UMA_DIARIO
    for rango in CESANTIA_VEJEZ_PATRONAL:
        if ratio_uma <= rango["hasta_uma"]:
            return rango["tasa"]
    return CESANTIA_VEJEZ_PATRONAL[-1]["tasa"]


# ============================================================
# CÁLCULO DE CUOTAS IMSS DESGLOSADO
# ============================================================
def calcular_imss_patronal(sbc_mensual, clase_riesgo="I"):
    """Calcula cuotas IMSS patronales desglosadas con tope de 25 UMA"""
    tope = UMA_MENSUAL * TOPE_SBC_UMA
    sbc = min(sbc_mensual, tope)
    uma_m = UMA_MENSUAL
    tres_uma = uma_m * 3

    # Cuota fija: sobre 1 UMA (siempre, independiente del SBC)
    cuota_fija = uma_m * (IMSS_PATRONAL["cuota_fija"] / 100)

    # Excedente de 3 UMA: solo si SBC > 3 UMA
    excedente_base = max(sbc - tres_uma, 0)
    excedente = excedente_base * (IMSS_PATRONAL["excedente_3uma_patronal"] / 100)

    # Prestaciones en dinero
    prest_dinero = sbc * (IMSS_PATRONAL["prest_dinero_patronal"] / 100)

    # Gastos médicos pensionados
    pensionados = sbc * (IMSS_PATRONAL["pensionados_patronal"] / 100)

    # Invalidez y vida
    invalidez = sbc * (IMSS_PATRONAL["invalidez_patronal"] / 100)

    # Riesgo de trabajo
    prima_rt = PRIMA_RIESGO.get(str(clase_riesgo), PRIMA_RIESGO["I"])
    riesgo = sbc * (prima_rt / 100)

    # Guarderías y prestaciones sociales
    guarderias = sbc * (IMSS_PATRONAL["guarderias"] / 100)

    # Retiro (SAR)
    retiro = sbc * (IMSS_PATRONAL["retiro"] / 100)

    # Cesantía y vejez (tabla graduada 2026)
    tasa_cesantia = obtener_tasa_cesantia_patronal(sbc)
    cesantia = sbc * (tasa_cesantia / 100)

    total = (cuota_fija + excedente + prest_dinero + pensionados +
             invalidez + riesgo + guarderias + retiro + cesantia)

    return {
        "cuota_fija": cuota_fija,
        "excedente_3uma": excedente,
        "prest_dinero": prest_dinero,
        "pensionados": pensionados,
        "invalidez": invalidez,
        "riesgo_trabajo": riesgo,
        "guarderias": guarderias,
        "retiro": retiro,
        "cesantia": cesantia,
        "tasa_cesantia": tasa_cesantia,
        "total": total,
    }


def calcular_imss_obrero(sbc_mensual):
    """Calcula cuotas IMSS obreras (descuento al trabajador) con tope de 25 UMA"""
    tope = UMA_MENSUAL * TOPE_SBC_UMA
    sbc = min(sbc_mensual, tope)
    tres_uma = UMA_MENSUAL * 3

    excedente_base = max(sbc - tres_uma, 0)
    excedente = excedente_base * (IMSS_OBRERO["excedente_3uma_obrero"] / 100)
    prest_dinero = sbc * (IMSS_OBRERO["prest_dinero_obrero"] / 100)
    pensionados = sbc * (IMSS_OBRERO["pensionados_obrero"] / 100)
    invalidez = sbc * (IMSS_OBRERO["invalidez_obrero"] / 100)
    cesantia = sbc * (IMSS_OBRERO["cesantia_obrero"] / 100)

    total = excedente + prest_dinero + pensionados + invalidez + cesantia

    return {
        "excedente_3uma": excedente,
        "prest_dinero": prest_dinero,
        "pensionados": pensionados,
        "invalidez": invalidez,
        "cesantia": cesantia,
        "total": total,
    }


# ============================================================
# CÁLCULO DE PRESTACIONES DE LEY PROPORCIONAL MENSUAL
# ============================================================
def calcular_prestaciones_ley(sueldo_diario):
    """Aguinaldo, vacaciones, prima vacacional (proporcional mensual)"""
    aguinaldo_anual = sueldo_diario * 15
    dias_vacaciones = 12  # Primer año mínimo legal (reforma 2023+)
    vacaciones_anual = sueldo_diario * dias_vacaciones
    prima_vac_anual = vacaciones_anual * 0.25

    return {
        "aguinaldo_mensual": aguinaldo_anual / 12,
        "vacaciones_mensual": vacaciones_anual / 12,
        "prima_vac_mensual": prima_vac_anual / 12,
        "total_mensual": (aguinaldo_anual + vacaciones_anual + prima_vac_anual) / 12,
    }


# ============================================================
# CÁLCULO COMPLETO - ESQUEMA ACTUAL (100% NÓMINA)
# ============================================================
def calcular_esquema_actual(sueldo_bruto, clase_riesgo, num_empleados=1):
    """Costo total para el patrón con nómina 100%"""
    isr = calcular_isr(sueldo_bruto)
    imss_pat = calcular_imss_patronal(sueldo_bruto, clase_riesgo)
    imss_obr = calcular_imss_obrero(sueldo_bruto)
    infonavit = sueldo_bruto * INFONAVIT_TASA
    isn = sueldo_bruto * ISN_TASA
    sueldo_diario = sueldo_bruto / 30.4
    prestaciones = calcular_prestaciones_ley(sueldo_diario)

    costo_por_empleado = sueldo_bruto + imss_pat["total"] + infonavit + isn + prestaciones["total_mensual"]
    neto_trabajador = sueldo_bruto - isr["isr_neto"] - imss_obr["total"]

    return {
        "sueldo_bruto": sueldo_bruto,
        "isr": isr,
        "imss_patronal": imss_pat,
        "imss_obrero": imss_obr,
        "infonavit": infonavit,
        "isn": isn,
        "prestaciones": prestaciones,
        "costo_por_empleado": costo_por_empleado,
        "costo_total": costo_por_empleado * num_empleados,
        "neto_trabajador": neto_trabajador,
        "num_empleados": num_empleados,
    }


# ============================================================
# CÁLCULO COMPLETO - ESQUEMA IRT (UN SOLO ESQUEMA)
# ============================================================
def calcular_esquema_irt(sueldo_bruto, minimo_profesional, clase_riesgo,
                          comision_pct, num_empleados=1):
    """
    Cálculo del esquema IRT.
    Base IMSS = mínimo profesional del puesto (piso: salario mínimo).
    Diferencial (bruto - mínimo profesional) = IRT exento (Art. 93 fr. III LISR).
    """
    # Base nómina = mínimo profesional, con piso en salario mínimo
    base_nomina = max(minimo_profesional, SALARIO_MINIMO_MENSUAL)
    excedente_irt = sueldo_bruto - base_nomina

    if excedente_irt < 0:
        excedente_irt = 0
        base_nomina = sueldo_bruto

    # Cálculos sobre la base reducida
    isr = calcular_isr(base_nomina)
    imss_pat = calcular_imss_patronal(base_nomina, clase_riesgo)
    imss_obr = calcular_imss_obrero(base_nomina)
    infonavit = base_nomina * INFONAVIT_TASA
    isn = base_nomina * ISN_TASA
    sueldo_diario = base_nomina / 30.4
    prestaciones = calcular_prestaciones_ley(sueldo_diario)

    # Costo de nómina (parte formal)
    costo_nomina = base_nomina + imss_pat["total"] + infonavit + isn + prestaciones["total_mensual"]

    # Total a administrar por empleado (nómina + IRT)
    total_administrado = sueldo_bruto

    # Comisión y facturación (por empleado)
    comision = total_administrado * (comision_pct / 100)
    subtotal_factura = total_administrado + comision
    iva = subtotal_factura * IVA
    total_factura = subtotal_factura + iva

    # Neto del trabajador (recibe lo mismo o más)
    neto_trabajador = base_nomina - isr["isr_neto"] - imss_obr["total"] + excedente_irt

    return {
        "base_nomina": base_nomina,
        "excedente_irt": excedente_irt,
        "isr": isr,
        "imss_patronal": imss_pat,
        "imss_obrero": imss_obr,
        "infonavit": infonavit,
        "isn": isn,
        "prestaciones": prestaciones,
        "costo_nomina": costo_nomina,
        "total_administrado": total_administrado,
        "comision": comision,
        "iva": iva,
        "total_factura": total_factura,
        "costo_total_factura": total_factura * num_empleados,
        "neto_trabajador": neto_trabajador,
        "num_empleados": num_empleados,
    }


# ============================================================
# CÁLCULO COMPLETO - EXCEDENTES
# ============================================================
def calcular_excedentes(monto_excedente, comision_pct):
    """Cálculo cuando solo se administran excedentes (bonos, comisiones, etc.)"""
    comision = monto_excedente * (comision_pct / 100)
    subtotal = monto_excedente + comision
    iva = subtotal * IVA
    total_factura = subtotal + iva

    # Costo hipotético si el cliente pagara esto por nómina
    imss_pat_hipotetico = calcular_imss_patronal(monto_excedente, "I")
    costo_hipotetico = (monto_excedente + imss_pat_hipotetico["total"] +
                        monto_excedente * INFONAVIT_TASA + monto_excedente * ISN_TASA)

    ahorro = costo_hipotetico - total_factura

    return {
        "monto_excedente": monto_excedente,
        "comision": comision,
        "iva": iva,
        "total_factura": total_factura,
        "costo_hipotetico_nomina": costo_hipotetico,
        "ahorro_mensual": ahorro,
        "ahorro_anual": ahorro * 12,
    }


# ============================================================
# CÁLCULO COMPLETO - SOCIEDAD CIVIL
# ============================================================
def calcular_sociedad_civil(ingreso_total, pct_anticipo, comision_pct, piramidar=False, neto_deseado=0):
    """
    Cálculo del esquema Sociedad Civil.
    pct_anticipo: 10 o 20 (% anticipo por remanente — gravado, retención ISR Art. 96)
    El resto (90% o 80%) va como renta vitalicia (exenta, Art. 93 fr. IV LISR)
    """
    if piramidar and neto_deseado > 0:
        ingreso_total = _piramidar_sc(neto_deseado, pct_anticipo, comision_pct)

    anticipo = ingreso_total * (pct_anticipo / 100)
    renta = ingreso_total - anticipo

    # ISR sobre el anticipo únicamente (tabla Art. 96)
    isr_anticipo = calcular_isr(anticipo)

    # Neto al directivo
    neto_anticipo = anticipo - isr_anticipo["isr_neto"]
    neto_total = neto_anticipo + renta  # renta es exenta al 100%

    # Facturación
    comision = ingreso_total * (comision_pct / 100)
    subtotal = ingreso_total + comision
    iva = subtotal * IVA
    total_factura = subtotal + iva

    # Comparativo vs nómina 100%
    isr_nomina = calcular_isr(ingreso_total)
    imss_pat = calcular_imss_patronal(ingreso_total, "I")
    imss_obr = calcular_imss_obrero(ingreso_total)
    costo_nomina_100 = (ingreso_total + imss_pat["total"] +
                         ingreso_total * INFONAVIT_TASA + ingreso_total * ISN_TASA)
    neto_nomina = ingreso_total - isr_nomina["isr_neto"] - imss_obr["total"]

    ahorro_cliente = costo_nomina_100 - total_factura

    return {
        "ingreso_total": ingreso_total,
        "pct_anticipo": pct_anticipo,
        "anticipo": anticipo,
        "renta": renta,
        "isr_anticipo": isr_anticipo,
        "neto_anticipo": neto_anticipo,
        "neto_total": neto_total,
        "comision": comision,
        "iva": iva,
        "total_factura": total_factura,
        "piramidar": piramidar,
        "neto_deseado": neto_deseado if piramidar else neto_total,
        # Comparativo
        "costo_nomina_100": costo_nomina_100,
        "neto_nomina": neto_nomina,
        "isr_nomina": isr_nomina,
        "ahorro_cliente_mensual": ahorro_cliente,
        "ahorro_cliente_anual": ahorro_cliente * 12,
    }


def neto_a_bruto(neto_deseado, clase_riesgo="I"):
    """
    Calcula el sueldo bruto necesario para lograr un neto deseado.
    neto = bruto - ISR(bruto) - IMSS_obrero(bruto)
    Usa bisección, tolerancia $0.50
    """
    low = neto_deseado
    high = neto_deseado * 2.5
    for _ in range(100):
        mid = (low + high) / 2
        isr = calcular_isr(mid)
        imss_obr = calcular_imss_obrero(mid)
        neto = mid - isr["isr_neto"] - imss_obr["total"]
        if abs(neto - neto_deseado) < 0.50:
            return round(mid, 2)
        elif neto < neto_deseado:
            low = mid
        else:
            high = mid
    return round(mid, 2)


def _piramidar_sc(neto_deseado, pct_anticipo, comision_pct):
    """Calcula ingreso bruto necesario para lograr neto deseado en SC (bisección)"""
    low, high = neto_deseado, neto_deseado * 3
    for _ in range(100):
        mid = (low + high) / 2
        anticipo = mid * (pct_anticipo / 100)
        renta = mid - anticipo
        isr = calcular_isr(anticipo)
        neto = (anticipo - isr["isr_neto"]) + renta
        if abs(neto - neto_deseado) < 0.50:
            return round(mid, 2)
        elif neto < neto_deseado:
            low = mid
        else:
            high = mid
    return round(mid, 2)


# ============================================================
# CÁLCULO RESUMEN POR GRUPO DE EMPLEADOS
# ============================================================
def calcular_grupo_nomina(puesto, num_empleados, sueldo_bruto, clase_riesgo,
                           minimo_profesional, comision_pct):
    """Calcula el resumen completo para un grupo: Actual vs IRT (un solo esquema)"""
    actual = calcular_esquema_actual(sueldo_bruto, clase_riesgo, num_empleados)

    irt = calcular_esquema_irt(sueldo_bruto, minimo_profesional, clase_riesgo,
                                comision_pct, num_empleados)

    ahorro = actual["costo_total"] - (irt["total_factura"] * num_empleados)

    return {
        "puesto": puesto,
        "num_empleados": num_empleados,
        "sueldo_bruto": sueldo_bruto,
        "clase_riesgo": clase_riesgo,
        "minimo_profesional": minimo_profesional,
        "actual": actual,
        "irt": irt,
        "ahorro_mensual": ahorro,
        "ahorro_anual": ahorro * 12,
    }
