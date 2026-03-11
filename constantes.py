# constantes.py — Constantes fiscales México 2026
# UMA, Salario Mínimo, Tablas ISR, Cuotas IMSS, Puestos profesionales
# Fuentes: INEGI, CONASAMI, SAT Anexo 8 RMF 2026, DOF, LSS

# === VALORES 2026 ===
UMA_DIARIO = 117.31            # UMA diario 2026 (vigente 01-feb-2026, INEGI)
UMA_MENSUAL = 3_566.22         # UMA mensual 2026 (UMA_DIARIO * 30.4)
UMA_ANUAL = 42_794.64          # UMA anual 2026 (UMA_MENSUAL * 12)

SALARIO_MINIMO_DIARIO = 315.04         # Salario mínimo general diario 2026 (CONASAMI)
SALARIO_MINIMO_FRONTERA = 440.87       # Salario mínimo zona libre frontera norte 2026
SALARIO_MINIMO_MENSUAL = SALARIO_MINIMO_DIARIO * 30.4

IVA = 0.16
ISN_TASA = 0.03               # Impuesto Sobre Nómina (CDMX default 3%, configurable por estado/cliente)
INFONAVIT_TASA = 0.05

# === TASAS ISN POR ESTADO (Impuesto Sobre Nómina 2026) ===
ISN_TASAS_ESTADO = {
    "Aguascalientes": 0.025,
    "Baja California": 0.018,
    "Baja California Sur": 0.025,
    "Campeche": 0.03,
    "Chiapas": 0.02,
    "Chihuahua": 0.03,
    "Ciudad de México": 0.03,
    "Coahuila": 0.02,
    "Colima": 0.02,
    "Durango": 0.02,
    "Estado de México": 0.03,
    "Guanajuato": 0.0295,
    "Guerrero": 0.02,
    "Hidalgo": 0.025,
    "Jalisco": 0.02,
    "Michoacán": 0.025,
    "Morelos": 0.02,
    "Nayarit": 0.02,
    "Nuevo León": 0.03,
    "Oaxaca": 0.03,
    "Puebla": 0.03,
    "Querétaro": 0.02,
    "Quintana Roo": 0.03,
    "San Luis Potosí": 0.025,
    "Sinaloa": 0.024,
    "Sonora": 0.02,
    "Tabasco": 0.025,
    "Tamaulipas": 0.03,
    "Tlaxcala": 0.03,
    "Veracruz": 0.03,
    "Yucatán": 0.025,
    "Zacatecas": 0.025,
}
TOPE_SBC_UMA = 25              # Tope de cotización IMSS: 25 UMA
FACTOR_INTEGRACION = 1.0493    # Factor de integración SBC: 1 + (25%×6/365) + (15/365) — prestaciones mínimas de ley

# === TABLA ISR MENSUAL ART. 96 LISR 2026 (Anexo 8 RMF 2026, DOF 28-dic-2025) ===
TABLA_ISR_MENSUAL = [
    {"lim_inf": 0.01,       "lim_sup": 844.59,      "cuota_fija": 0.00,      "pct_excedente": 1.92},
    {"lim_inf": 844.60,     "lim_sup": 7_168.51,     "cuota_fija": 16.22,     "pct_excedente": 6.40},
    {"lim_inf": 7_168.52,   "lim_sup": 12_598.02,    "cuota_fija": 420.95,    "pct_excedente": 10.88},
    {"lim_inf": 12_598.03,  "lim_sup": 14_644.64,    "cuota_fija": 1_011.68,  "pct_excedente": 16.00},
    {"lim_inf": 14_644.65,  "lim_sup": 17_533.64,    "cuota_fija": 1_339.14,  "pct_excedente": 17.92},
    {"lim_inf": 17_533.65,  "lim_sup": 35_362.83,    "cuota_fija": 1_856.84,  "pct_excedente": 21.36},
    {"lim_inf": 35_362.84,  "lim_sup": 55_736.68,    "cuota_fija": 5_665.16,  "pct_excedente": 23.52},
    {"lim_inf": 55_736.69,  "lim_sup": 106_410.50,   "cuota_fija": 10_457.09, "pct_excedente": 30.00},
    {"lim_inf": 106_410.51, "lim_sup": 141_880.66,   "cuota_fija": 25_659.23, "pct_excedente": 32.00},
    {"lim_inf": 141_880.67, "lim_sup": 425_641.99,   "cuota_fija": 37_009.69, "pct_excedente": 34.00},
    {"lim_inf": 425_642.00, "lim_sup": float("inf"), "cuota_fija": 133_488.54,"pct_excedente": 35.00},
]

# === SUBSIDIO AL EMPLEO MENSUAL 2026 (Reforma DOF 01-may-2024, actualizado DOF 31-dic-2025) ===
# Ya no es tabla de rangos — es monto fijo si el ingreso no excede el límite
SUBSIDIO_MENSUAL = 535.65              # Monto fijo mensual (feb-dic 2026, 15.02% de UMA mensual)
SUBSIDIO_LIMITE_INGRESOS = 11_492.66   # Límite de ingresos mensuales para aplicar subsidio

# === CUOTAS IMSS (tasas como porcentaje) ===
# Riesgo de trabajo por clase (Art. 73 LSS — prima media)
PRIMA_RIESGO = {
    "I":   0.54355,
    "II":  1.13065,
    "III": 2.59840,
    "IV":  4.65325,
    "V":   7.58875,
}

# Cuotas patronales (porcentaje) — SIN cesantía y vejez (es graduada, ver tabla abajo)
IMSS_PATRONAL = {
    "cuota_fija": 20.40,               # Enf. y maternidad — sobre 1 UMA (solo patronal)
    "excedente_3uma_patronal": 1.10,    # Enf. y maternidad — sobre excedente de 3 UMA
    "prest_dinero_patronal": 0.70,      # Enf. y maternidad — sobre SBC
    "pensionados_patronal": 1.05,       # Gastos médicos pensionados — sobre SBC
    "invalidez_patronal": 1.75,         # Invalidez y vida — sobre SBC
    "guarderias": 1.00,                 # Guarderías y prest. sociales — sobre SBC
    "retiro": 2.00,                     # Retiro (SAR) — sobre SBC
}

# Cesantía y vejez patronal — TABLA GRADUADA por reforma de pensiones 2020
# Tasa varía según rango de SBC en múltiplos de UMA (2026 = 4to año de incremento)
# Fuente: Art. transitorio Decreto DOF 16-dic-2020, ElConta.mx, IDC Online
CESANTIA_VEJEZ_PATRONAL = [
    {"desde_uma": 0,    "hasta_uma": 1.00, "tasa": 3.150},
    {"desde_uma": 1.00, "hasta_uma": 1.50, "tasa": 3.676},
    {"desde_uma": 1.50, "hasta_uma": 2.00, "tasa": 4.851},
    {"desde_uma": 2.00, "hasta_uma": 2.50, "tasa": 5.556},
    {"desde_uma": 2.50, "hasta_uma": 3.00, "tasa": 6.026},
    {"desde_uma": 3.00, "hasta_uma": 3.50, "tasa": 6.361},
    {"desde_uma": 3.50, "hasta_uma": 4.00, "tasa": 6.613},
    {"desde_uma": 4.00, "hasta_uma": 25.0, "tasa": 7.513},
]

# Cuotas obreras (porcentaje)
IMSS_OBRERO = {
    "excedente_3uma_obrero": 0.40,      # Enf. y maternidad — sobre excedente de 3 UMA
    "prest_dinero_obrero": 0.25,        # Enf. y maternidad — sobre SBC
    "pensionados_obrero": 0.375,        # Gastos médicos pensionados — sobre SBC
    "invalidez_obrero": 0.625,          # Invalidez y vida — sobre SBC
    "cesantia_obrero": 1.125,           # Cesantía y vejez — sobre SBC (tasa fija)
}

# === SALARIOS MÍNIMOS PROFESIONALES IMSS (mensuales estimados 2026) ===
# Nota: ningún puesto puede estar por debajo del salario mínimo mensual ($9,577.22)
PUESTOS_PROFESIONALES = {
    "Auxiliar contable": 11_000,
    "Contador": 16_500,
    "Auxiliar administrativo": 9_800,
    "Recepcionista": 9_600,
    "Secretaria": 9_600,
    "Almacenista": 9_600,
    "Chofer": 10_800,
    "Operador de maquinaria": 12_000,
    "Soldador": 11_500,
    "Electricista": 11_800,
    "Plomero": 10_500,
    "Mecánico": 11_200,
    "Vigilante / Guardia de seguridad": 9_600,
    "Personal de limpieza": 9_600,
    "Cocinero": 9_600,
    "Mesero": 9_600,
    "Vendedor": 9_800,
    "Promotor": 9_600,
    "Diseñador gráfico": 12_500,
    "Programador / Desarrollador": 16_000,
    "Técnico en mantenimiento": 10_800,
    "Enfermera": 12_000,
    "Paramédico": 11_500,
    "Farmacéutico": 14_000,
    "Maestro / Profesor": 13_500,
    "Abogado": 16_000,
    "Arquitecto": 15_500,
    "Ingeniero civil": 15_800,
    "Ingeniero industrial": 15_500,
    "Ingeniero mecánico": 15_200,
    "Médico general": 18_000,
    "Dentista": 16_500,
    "Psicólogo": 14_000,
    "Nutriólogo": 13_000,
    "Gerente administrativo": 22_000,
    "Gerente de ventas": 24_000,
    "Gerente de operaciones": 25_000,
    "Director general": 35_000,
    "Supervisor de producción": 14_500,
    "Jefe de almacén": 13_000,
    "Jefe de mantenimiento": 14_000,
    "Analista de datos": 14_500,
    "Ejecutivo de ventas": 11_000,
    "Asesor financiero": 15_000,
    "Cajero": 9_600,
    "Capturista": 9_600,
    "Mensajero / Repartidor": 9_600,
    "Fotógrafo": 10_500,
    "Community manager": 11_000,
    "Recursos humanos / Reclutador": 13_000,
    "Otro (personalizado)": 0,
}

# Lista ordenada de puestos para dropdown
LISTA_PUESTOS = sorted([p for p in PUESTOS_PROFESIONALES.keys() if p != "Otro (personalizado)"]) + ["Otro (personalizado)"]
