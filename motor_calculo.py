# motor_calculo.py — Motor de cálculo fiscal
# ISR, IMSS desglosado, IRT, Excedentes, Sociedad Civil
# Alineado con cotizadores Excel (Propuesta Esquema, Excedentes, SC)

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
# SBC (Salario Base de Cotización)
# ============================================================
def calcular_sbc_diario(salario_diario):
    """SBC diario = SD × factor de integración, topado a 25 UMA.
    Factor 1.0493 = prestaciones mínimas de ley integradas:
      1 + (25%×6/365) + (15/365) ≈ 1.0493
    Replica fórmula Excel: MIN(SD×1.0493, UMA_DIARIO×25)"""
    tope = UMA_DIARIO * TOPE_SBC_UMA
    return min(round(salario_diario * FACTOR_INTEGRACION, 2), tope)


# ============================================================
# TASA CESANTÍA Y VEJEZ PATRONAL (tabla graduada)
# ============================================================
def obtener_tasa_cesantia_patronal(sbc_diario):
    """Determina la tasa patronal de cesantía y vejez según rango de SBC en UMAs"""
    ratio_uma = sbc_diario / UMA_DIARIO
    for rango in CESANTIA_VEJEZ_PATRONAL:
        if ratio_uma <= rango["hasta_uma"]:
            return rango["tasa"]
    return CESANTIA_VEJEZ_PATRONAL[-1]["tasa"]


# ============================================================
# HELPER: Resolver prima de riesgo de trabajo
# ============================================================
def _resolver_prima_riesgo(clase_riesgo="I", prima_riesgo=None):
    """Si prima_riesgo (numérico %) se proporciona, lo usa. Si no, busca por clase."""
    if prima_riesgo is not None and prima_riesgo > 0:
        return prima_riesgo  # ya es porcentaje (ej: 0.54355)
    return PRIMA_RIESGO.get(str(clase_riesgo), PRIMA_RIESGO["I"])


# ============================================================
# CUOTAS IMSS PATRONALES (desglosado, solo patronal)
# ============================================================
def calcular_imss_patronal(salario_diario, dias=30.4, clase_riesgo="I", prima_riesgo=None):
    """Cuotas IMSS patronales desglosadas. Calcula SBC internamente.
    prima_riesgo: tasa numérica directa (ej: 0.54355 para clase I). Si se da, prevalece sobre clase_riesgo."""
    sbc = calcular_sbc_diario(salario_diario)

    cuota_fija = round(UMA_DIARIO * (IMSS_PATRONAL["cuota_fija"] / 100) * dias, 2)
    exc_base = max(sbc - 3 * UMA_DIARIO, 0)
    excedente = round(exc_base * (IMSS_PATRONAL["excedente_3uma_patronal"] / 100) * dias, 2)
    prest_dinero = round(sbc * (IMSS_PATRONAL["prest_dinero_patronal"] / 100) * dias, 2)
    pensionados = round(sbc * (IMSS_PATRONAL["pensionados_patronal"] / 100) * dias, 2)
    invalidez = round(sbc * (IMSS_PATRONAL["invalidez_patronal"] / 100) * dias, 2)
    prima_rt = _resolver_prima_riesgo(clase_riesgo, prima_riesgo)
    riesgo = round(sbc * (prima_rt / 100) * dias, 2)
    guarderias = round(sbc * (IMSS_PATRONAL["guarderias"] / 100) * dias, 2)
    retiro = round(sbc * (IMSS_PATRONAL["retiro"] / 100) * dias, 2)
    tasa_cesantia = obtener_tasa_cesantia_patronal(sbc)
    cesantia = round(sbc * (tasa_cesantia / 100) * dias, 2)

    total = (cuota_fija + excedente + prest_dinero + pensionados +
             invalidez + riesgo + guarderias + retiro + cesantia)

    return {
        "sbc_diario": sbc,
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


# ============================================================
# CUOTAS IMSS OBRERAS (desglosado)
# ============================================================
def calcular_imss_obrero(salario_diario, dias=30.4):
    """Cuotas IMSS obreras (descuento al trabajador). Calcula SBC internamente."""
    sbc = calcular_sbc_diario(salario_diario)

    exc_base = max(sbc - 3 * UMA_DIARIO, 0)
    excedente = round(exc_base * (IMSS_OBRERO["excedente_3uma_obrero"] / 100) * dias, 2)
    prest_dinero = round(sbc * (IMSS_OBRERO["prest_dinero_obrero"] / 100) * dias, 2)
    pensionados = round(sbc * (IMSS_OBRERO["pensionados_obrero"] / 100) * dias, 2)
    invalidez = round(sbc * (IMSS_OBRERO["invalidez_obrero"] / 100) * dias, 2)
    cesantia = round(sbc * (IMSS_OBRERO["cesantia_obrero"] / 100) * dias, 2)

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
# COSTO SOCIAL COMPLETO (IMSS pat+obr + RCV + INFONAVIT + ISN)
# Replica la hoja IMSS de los cotizadores Excel.
# En IRT el patrón absorbe ambas porciones vía PPS.
# ============================================================
def calcular_costo_social(salario_diario, dias=30.4, clase_riesgo="I", isn_tasa=None, prima_riesgo=None):
    """
    Costo social total para el esquema IRT.
    Usa tasas combinadas (patronal + obrero) como en los cotizadores Excel,
    porque en IRT el patrón absorbe ambas porciones vía PPS.
    prima_riesgo: tasa numérica directa (ej: 0.54355). Si se da, prevalece sobre clase_riesgo.
    """
    if isn_tasa is None:
        isn_tasa = ISN_TASA

    sbc = calcular_sbc_diario(salario_diario)

    # --- IMSS mensual (tasas combinadas pat + obr) ---
    cuota_fija = round(UMA_DIARIO * (IMSS_PATRONAL["cuota_fija"] / 100) * dias, 2)

    exc_base = max(sbc - 3 * UMA_DIARIO, 0)
    tasa_exc = (IMSS_PATRONAL["excedente_3uma_patronal"] + IMSS_OBRERO["excedente_3uma_obrero"]) / 100
    excedente = round(exc_base * tasa_exc * dias, 2)

    tasa_pd = (IMSS_PATRONAL["prest_dinero_patronal"] + IMSS_OBRERO["prest_dinero_obrero"]) / 100
    prest_dinero = round(sbc * tasa_pd * dias, 2)

    tasa_pen = (IMSS_PATRONAL["pensionados_patronal"] + IMSS_OBRERO["pensionados_obrero"]) / 100
    pensionados = round(sbc * tasa_pen * dias, 2)

    prima_rt = _resolver_prima_riesgo(clase_riesgo, prima_riesgo) / 100
    riesgo = round(sbc * prima_rt * dias, 2)

    tasa_inv = (IMSS_PATRONAL["invalidez_patronal"] + IMSS_OBRERO["invalidez_obrero"]) / 100
    invalidez = round(sbc * tasa_inv * dias, 2)

    guarderias = round(sbc * (IMSS_PATRONAL["guarderias"] / 100) * dias, 2)

    total_imss = cuota_fija + excedente + prest_dinero + pensionados + riesgo + invalidez + guarderias

    # --- RCV bimestral ---
    retiro = round(sbc * (IMSS_PATRONAL["retiro"] / 100) * dias, 2)

    tasa_ces_pat = obtener_tasa_cesantia_patronal(sbc) / 100
    tasa_ces_obr = IMSS_OBRERO["cesantia_obrero"] / 100
    cesantia = round(sbc * (tasa_ces_pat + tasa_ces_obr) * dias, 2)

    infonavit = round(sbc * INFONAVIT_TASA * dias, 2)

    total_rcv = retiro + cesantia + infonavit

    # --- ISN (sobre salario base, NO sobre SBC) ---
    isn = round(salario_diario * dias * isn_tasa, 2)

    total = total_imss + total_rcv + isn

    return {
        "sbc_diario": sbc,
        "cuota_fija": cuota_fija,
        "excedente_3uma": excedente,
        "prest_dinero": prest_dinero,
        "pensionados": pensionados,
        "riesgo_trabajo": riesgo,
        "invalidez": invalidez,
        "guarderias": guarderias,
        "total_imss": total_imss,
        "retiro": retiro,
        "cesantia": cesantia,
        "infonavit": infonavit,
        "total_rcv": total_rcv,
        "isn": isn,
        "total": total,
    }


# ============================================================
# PRESTACIONES DE LEY (proporcional mensual)
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
# ESQUEMA ACTUAL (100% NÓMINA) — para comparación
# ============================================================
def calcular_esquema_actual(sueldo_bruto, clase_riesgo, num_empleados=1, prima_riesgo=None):
    """Costo total para el patrón con nómina 100% formal. IMSS sobre SBC."""
    dias = 30.4
    salario_diario = sueldo_bruto / dias
    sbc = calcular_sbc_diario(salario_diario)

    isr = calcular_isr(sueldo_bruto)
    imss_pat = calcular_imss_patronal(salario_diario, 30.4, clase_riesgo, prima_riesgo)
    imss_obr = calcular_imss_obrero(salario_diario, 30.4)
    infonavit = round(sbc * INFONAVIT_TASA * 30.4, 2)
    isn = round(sueldo_bruto * ISN_TASA, 2)
    prestaciones = calcular_prestaciones_ley(salario_diario)

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
# ESQUEMA IRT — Replica cotizador Excel "Propuesta Esquema"
# ============================================================
def calcular_esquema_irt(sueldo_bruto, base_imss_mensual, clase_riesgo,
                          comision_pct, num_empleados=1, dias=30.4, isn_tasa=None, prima_riesgo=None):
    """
    Esquema IRT (Indemnización por Riesgo de Trabajo).

    sueldo_bruto = TOTAL DEPOSITO: lo que el empleado debe recibir.
    base_imss_mensual = base libre para IMSS (mínimo, profesional, o cualquier monto).
    Comisión sobre (nómina + cargas sociales) como en el cotizador Excel.

    Flujo Excel:
      SUELDO = dias * SD
      ISR Art 96 sobre SUELDO
      PPS = DEPOSITO - SUELDO + ISR_NETO
      COSTO SOCIAL = IMSS combinado (pat+obr) + ISN
      NOMINA + CARGAS = (SUELDO + PPS) + COSTO SOCIAL
      COMISION = (NOMINA + CARGAS) * %
      TOTAL FACTURA = (NOMINA + CARGAS + COMISION) * 1.16
    """
    # Base nómina: piso en salario mínimo, techo en sueldo bruto real
    base_nomina = min(max(base_imss_mensual, SALARIO_MINIMO_MENSUAL), sueldo_bruto)

    salario_diario = base_nomina / dias

    # ISR sobre la base nómina
    isr = calcular_isr(base_nomina)
    sueldo_neto = base_nomina - isr["isr_neto"]

    # PPS/IRT = lo que completa el depósito total
    # Excel: PPS = DEPOSITO - SUELDO + ISR_NETO
    excedente_irt = sueldo_bruto - sueldo_neto

    # IMSS desglosado patronal y obrero (para display en Word/app)
    imss_pat = calcular_imss_patronal(salario_diario, 30.4, clase_riesgo, prima_riesgo)
    imss_obr = calcular_imss_obrero(salario_diario, 30.4)

    # Costo social combinado (pat+obr, para display desglosado)
    costo_social = calcular_costo_social(salario_diario, 30.4, clase_riesgo, isn_tasa, prima_riesgo)

    # INFONAVIT y ISN solo patronal (NO combinado)
    sbc = calcular_sbc_diario(salario_diario)
    infonavit = round(sbc * INFONAVIT_TASA * 30.4, 2)
    _isn_tasa = isn_tasa if isn_tasa is not None else ISN_TASA
    isn = round(base_nomina * _isn_tasa, 2)

    # Prestaciones de ley
    prestaciones = calcular_prestaciones_ley(salario_diario)

    # Costo nómina = sueldo + PPS = depósito + ISR_neto
    costo_nomina = base_nomina + excedente_irt

    # Total administrado = sueldos + IMSS patronal + INFONAVIT + ISN
    # NO incluye obrero (no es costo del patrón) NI prestaciones (se ahorran)
    total_administrado = costo_nomina + imss_pat["total"] + infonavit + isn

    # Comisión sobre total administrado
    comision = round(total_administrado * (comision_pct / 100), 2)
    subtotal_factura = total_administrado + comision
    iva = round(subtotal_factura * IVA, 2)
    total_factura = subtotal_factura + iva

    # Neto al trabajador: recibe el depósito completo (PPS cubre ISR)
    neto_trabajador = sueldo_bruto

    return {
        "base_nomina": base_nomina,
        "excedente_irt": excedente_irt,
        "isr": isr,
        "imss_patronal": imss_pat,
        "imss_obrero": imss_obr,
        "imss_patronal_total": imss_pat["total"],
        "infonavit": infonavit,
        "isn": isn,
        "prestaciones": prestaciones,
        "costo_nomina": costo_nomina,
        "costo_social": costo_social["total"],
        "total_administrado": total_administrado,
        "comision": comision,
        "subtotal_factura": subtotal_factura,
        "iva": iva,
        "total_factura": total_factura,
        "costo_total_factura": total_factura * num_empleados,
        "neto_trabajador": neto_trabajador,
        "num_empleados": num_empleados,
    }


# ============================================================
# EXCEDENTES
# ============================================================
def calcular_excedentes(monto_excedente, comision_pct):
    """
    Administración de excedentes (bonos, comisiones, viáticos).
    Replica cotizador Excel "Propuesta Excedentes".
    Comisión sobre el excedente, + IVA.
    """
    comision = round(monto_excedente * (comision_pct / 100), 2)
    subtotal = monto_excedente + comision
    iva = round(subtotal * IVA, 2)
    total_factura = subtotal + iva

    # Costo hipotético si el cliente pagara esto por nómina gravable
    sd_hipotetico = monto_excedente / 30.4
    sbc_hip = calcular_sbc_diario(sd_hipotetico)
    isr_hipotetico = calcular_isr(monto_excedente)
    imss_pat_hipotetico = calcular_imss_patronal(sd_hipotetico, 30.4, "I")
    infonavit_hip = round(sbc_hip * INFONAVIT_TASA * 30.4, 2)
    isn_hip = round(monto_excedente * ISN_TASA, 2)
    # Excedentes son bonos/comisiones — no generan obligación de prestaciones de ley
    costo_hipotetico = (monto_excedente + imss_pat_hipotetico["total"]
                        + infonavit_hip + isn_hip)

    # Ahorro: costo nómina hipotético vs subtotal factura (pre-IVA)
    ahorro = costo_hipotetico - subtotal

    return {
        "monto_excedente": monto_excedente,
        "comision": comision,
        "iva": iva,
        "total_factura": total_factura,
        "costo_hipotetico_nomina": costo_hipotetico,
        "isr_hipotetico": isr_hipotetico["isr_neto"],
        "imss_pat_hipotetico": imss_pat_hipotetico["total"],
        "infonavit_hipotetico": infonavit_hip,
        "isn_hipotetico": isn_hip,
        "ahorro_mensual": ahorro,
        "ahorro_anual": ahorro * 12,
    }


# ============================================================
# SOCIEDAD CIVIL — Replica cotizador Excel "Propuesta SC"
# ============================================================
def calcular_sociedad_civil(ingreso_total, pct_anticipo, comision_pct, piramidar=False, neto_deseado=0):
    """
    Esquema Sociedad Civil.
    pct_anticipo: 10 o 20 (% anticipo por remanente — gravado, retención ISR Art. 96)
    El resto (90% o 80%) va como renta vitalicia (exenta, Art. 93 fr. IV LISR).
    Modo pirámidar: el cliente dice cuánto quiere recibir neto, calculamos el bruto.
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

    # Facturación: comisión sobre ingreso total (como en cotizador Excel SC)
    comision = round(ingreso_total * (comision_pct / 100), 2)
    subtotal = ingreso_total + comision
    iva = round(subtotal * IVA, 2)
    total_factura = subtotal + iva

    # Comparativo vs nómina 100%
    sd = ingreso_total / 30.4
    sbc = calcular_sbc_diario(sd)
    isr_nomina = calcular_isr(ingreso_total)
    imss_pat = calcular_imss_patronal(sd, 30.4, "I")
    infonavit_nom = round(sbc * INFONAVIT_TASA * 30.4, 2)
    isn_nom = round(ingreso_total * ISN_TASA, 2)
    prestaciones_nom = calcular_prestaciones_ley(sd)
    costo_nomina_100 = (ingreso_total + imss_pat["total"] + infonavit_nom
                        + isn_nom + prestaciones_nom["total_mensual"])
    # Neto nómina: sin IMSS obrero porque SC no cotiza IMSS
    neto_nomina = ingreso_total - isr_nomina["isr_neto"]

    # Ahorro: costo nómina 100% vs subtotal factura SC (pre-IVA, el IVA es acreditable)
    ahorro_cliente = costo_nomina_100 - subtotal

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


def neto_a_bruto(neto_deseado, clase_riesgo="I", prima_riesgo=None):
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
        sd = mid / 30.4
        imss_obr = calcular_imss_obrero(sd, 30.4)
        neto = mid - isr["isr_neto"] - imss_obr["total"]
        if abs(neto - neto_deseado) < 0.50:
            return round(mid, 2)
        elif neto < neto_deseado:
            low = mid
        else:
            high = mid
    return round(mid, 2)


def _piramidar_sc(neto_deseado, pct_anticipo, comision_pct):
    """Calcula ingreso bruto necesario para lograr neto deseado en SC (bisección).
    f(bruto) = (bruto×pct% - isr(bruto×pct%)) + bruto×(100-pct)% - neto_deseado
    Tolerancia: $0.01"""
    low, high = neto_deseado, neto_deseado * 3
    for _ in range(200):
        mid = (low + high) / 2
        anticipo = mid * (pct_anticipo / 100)
        renta = mid - anticipo
        isr = calcular_isr(anticipo)
        neto = (anticipo - isr["isr_neto"]) + renta
        if abs(neto - neto_deseado) < 0.01:
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
                           minimo_profesional, comision_pct, prima_riesgo=None):
    """Calcula el resumen completo para un grupo: Actual vs IRT"""
    actual = calcular_esquema_actual(sueldo_bruto, clase_riesgo, num_empleados, prima_riesgo)

    irt = calcular_esquema_irt(sueldo_bruto, minimo_profesional, clase_riesgo,
                                comision_pct, num_empleados, prima_riesgo=prima_riesgo)

    # Ahorro: costo interno actual vs subtotal factura IRT (pre-IVA, el IVA es acreditable)
    ahorro = actual["costo_total"] - (irt["subtotal_factura"] * num_empleados)

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
