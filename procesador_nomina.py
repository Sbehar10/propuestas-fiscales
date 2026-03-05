# procesador_nomina.py — Procesador de archivos de nómina (Excel/CSV)
# Detección de columnas, mapeo de puestos, validación

import unicodedata
import difflib
import pandas as pd
from constantes import PUESTOS_PROFESIONALES, SALARIO_MINIMO_MENSUAL


# ============================================================
# NORMALIZACIÓN DE TEXTO
# ============================================================
def _normalizar(texto):
    """Quita acentos, convierte a minúsculas y strip"""
    if not isinstance(texto, str):
        return str(texto).strip().lower()
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sin_acentos.strip().lower()


# ============================================================
# DETECCIÓN AUTOMÁTICA DE COLUMNAS
# ============================================================
KEYWORDS_PUESTO = ["puesto", "cargo", "posicion", "posición", "rol", "funcion", "plaza",
                    "categoria", "nombre", "clave", "departamento", "area"]
KEYWORDS_SUELDO = ["sueldo", "salario", "ingreso", "pago", "remuneracion", "percepcion",
                    "bruto", "neto", "liquido", "mensual", "deposito", "actual", "nuevo",
                    "total deposito", "importe", "monto"]
KEYWORDS_EMPLEADOS = ["empleados", "cantidad", "num", "numero", "headcount",
                       "personas", "colaboradores", "trabajadores", "plazas"]


def _score_columna(col_normalizada, keywords):
    """Calcula score de coincidencia por substring"""
    score = 0
    for kw in keywords:
        if kw in col_normalizada:
            score += len(kw)  # Mayor peso a keywords más largas
    return score


def detectar_columnas(df):
    """
    Auto-detecta columnas de puesto, sueldo y num_empleados.
    Retorna dict con las columnas encontradas (nombre original).
    """
    resultado = {"puesto": None, "sueldo": None, "num_empleados": None}
    scores = {"puesto": 0, "sueldo": 0, "num_empleados": 0}

    for col in df.columns:
        col_norm = _normalizar(col)

        # Score para puesto
        s_puesto = _score_columna(col_norm, KEYWORDS_PUESTO)
        if s_puesto > scores["puesto"]:
            scores["puesto"] = s_puesto
            resultado["puesto"] = col

        # Score para sueldo
        s_sueldo = _score_columna(col_norm, KEYWORDS_SUELDO)
        if s_sueldo > scores["sueldo"]:
            scores["sueldo"] = s_sueldo
            resultado["sueldo"] = col

        # Score para num_empleados (solo si no es la misma col que sueldo)
        s_emp = _score_columna(col_norm, KEYWORDS_EMPLEADOS)
        if s_emp > scores["num_empleados"]:
            scores["num_empleados"] = s_emp
            resultado["num_empleados"] = col

    # Evitar que la misma columna se asigne a dos campos
    asignadas = set()
    for campo in ["puesto", "sueldo", "num_empleados"]:
        if resultado[campo] in asignadas:
            resultado[campo] = None
        elif resultado[campo] is not None:
            asignadas.add(resultado[campo])

    return resultado


# ============================================================
# DETECCIÓN BRUTO / NETO
# ============================================================
KEYWORDS_NETO = ["neto", "liquido", "líquido", "percepcion neta", "sueldo neto"]
KEYWORDS_BRUTO = ["bruto", "total", "nominal", "tabular", "sueldo bruto"]


def detectar_bruto_neto(df, col_sueldo):
    """
    Detecta si la columna de sueldo es bruto o neto.
    Retorna 'bruto', 'neto' o 'desconocido'.
    """
    if col_sueldo is None:
        return "desconocido"

    col_norm = _normalizar(col_sueldo)

    # Buscar en nombre de columna
    for kw in KEYWORDS_NETO:
        if kw in col_norm:
            return "neto"

    for kw in KEYWORDS_BRUTO:
        if kw in col_norm:
            return "bruto"

    # Heurística: si la mediana es menor que 1.5x el SM, probablemente es neto
    try:
        valores = pd.to_numeric(df[col_sueldo], errors="coerce").dropna()
        if len(valores) > 0:
            mediana = valores.median()
            if mediana < SALARIO_MINIMO_MENSUAL * 0.85:
                return "neto"  # Muy bajo, probablemente neto
    except Exception:
        pass

    return "desconocido"


# ============================================================
# MAPEO DE PUESTOS AL CATÁLOGO
# ============================================================
def mapear_puestos(puestos_serie):
    """
    Mapea puestos del archivo al catálogo de puestos profesionales.
    Retorna DataFrame con: puesto_original, puesto_catalogo, minimo_profesional, confianza
    """
    catalogo = {k: v for k, v in PUESTOS_PROFESIONALES.items() if k != "Otro (personalizado)"}
    catalogo_normalizado = {_normalizar(k): k for k in catalogo}
    nombres_catalogo = list(catalogo_normalizado.keys())

    resultados = []
    for puesto_orig in puestos_serie.unique():
        puesto_norm = _normalizar(str(puesto_orig))

        # Match exacto
        if puesto_norm in catalogo_normalizado:
            nombre_cat = catalogo_normalizado[puesto_norm]
            resultados.append({
                "puesto_original": puesto_orig,
                "puesto_catalogo": nombre_cat,
                "minimo_profesional": catalogo[nombre_cat],
                "confianza": 1.0,
            })
            continue

        # Match difuso
        matches = difflib.get_close_matches(puesto_norm, nombres_catalogo, n=1, cutoff=0.5)
        if matches:
            nombre_cat = catalogo_normalizado[matches[0]]
            # Calcular confianza como ratio de similitud
            ratio = difflib.SequenceMatcher(None, puesto_norm, matches[0]).ratio()
            resultados.append({
                "puesto_original": puesto_orig,
                "puesto_catalogo": nombre_cat,
                "minimo_profesional": catalogo[nombre_cat],
                "confianza": round(ratio, 2),
            })
        else:
            # Sin match
            resultados.append({
                "puesto_original": puesto_orig,
                "puesto_catalogo": "Otro (personalizado)",
                "minimo_profesional": SALARIO_MINIMO_MENSUAL,
                "confianza": 0.0,
            })

    return pd.DataFrame(resultados)


# ============================================================
# VALIDACIÓN DE DATOS
# ============================================================
def validar_datos(df, cols):
    """
    Valida los datos del DataFrame según las columnas detectadas.
    Retorna lista de warnings.
    """
    warnings = []

    col_sueldo = cols.get("sueldo")
    col_puesto = cols.get("puesto")
    col_emp = cols.get("num_empleados")

    # Validar sueldo
    if col_sueldo and col_sueldo in df.columns:
        no_numerico = pd.to_numeric(df[col_sueldo], errors="coerce").isna().sum()
        if no_numerico > 0:
            warnings.append(f"Se encontraron {no_numerico} valores no numéricos en '{col_sueldo}'.")

        sueldos = pd.to_numeric(df[col_sueldo], errors="coerce").dropna()
        bajo_sm = (sueldos < SALARIO_MINIMO_MENSUAL).sum()
        if bajo_sm > 0:
            warnings.append(f"{bajo_sm} sueldos están por debajo del salario mínimo (${SALARIO_MINIMO_MENSUAL:,.2f}).")

    # Validar empleados
    if col_emp and col_emp in df.columns:
        no_numerico = pd.to_numeric(df[col_emp], errors="coerce").isna().sum()
        if no_numerico > 0:
            warnings.append(f"Se encontraron {no_numerico} valores no numéricos en '{col_emp}'.")

        empleados = pd.to_numeric(df[col_emp], errors="coerce").dropna()
        invalidos = (empleados <= 0).sum()
        if invalidos > 0:
            warnings.append(f"{invalidos} filas con número de empleados <= 0.")

    # Validar puestos
    if col_puesto and col_puesto in df.columns:
        vacios = df[col_puesto].isna().sum() + (df[col_puesto].astype(str).str.strip() == "").sum()
        if vacios > 0:
            warnings.append(f"{vacios} filas con puesto vacío.")

    return warnings
