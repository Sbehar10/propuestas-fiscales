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
def _score_columna(col_normalizada, keywords):
    """Calcula score de coincidencia por substring"""
    score = 0
    for kw in keywords:
        if kw in col_normalizada:
            score += len(kw)  # Mayor peso a keywords más largas
    return score


def _es_columna_numerica(df, col, umbral=0.5):
    """Retorna True si más del umbral de valores no-nulos son numéricos."""
    try:
        serie = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
        no_nulos = serie.dropna()
        if len(no_nulos) == 0:
            return False
        numericos = pd.to_numeric(no_nulos, errors="coerce").notna().sum()
        return (numericos / len(no_nulos)) >= umbral
    except Exception:
        return False


def _es_columna_texto(df, col, umbral=0.5):
    """Retorna True si más del umbral de valores no-nulos son texto no-numérico."""
    try:
        serie = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
        no_nulos = serie.dropna().astype(str).str.strip()
        no_nulos = no_nulos[no_nulos != ""]
        if len(no_nulos) == 0:
            return False
        no_num = pd.to_numeric(no_nulos, errors="coerce").isna().sum()
        return (no_num / len(no_nulos)) >= umbral
    except Exception:
        return False


def detectar_columnas(df):
    """
    Auto-detecta columnas de puesto, sueldo y num_empleados.
    Retorna dict con las columnas encontradas (nombre original).
    """
    PUESTO_HIGH = ["puesto", "cargo", "plaza", "posicion", "rol"]
    PUESTO_LOW  = ["categoria", "departamento", "area"]
    PUESTO_EXCLUIR = ["nombre", "clave", "rfc", "curp", "nss", "empleado", "banco", "cuenta", "clabe"]

    SUELDO_KEYS = ["total deposito", "deposito total", "total a depositar", "neto real mensual",
                   "neto mensual", "sueldo neto", "salario neto",
                   "bruto mensual", "sueldo bruto", "salario bruto", "deposito",
                   "neto real", "percepcion neta", "importe neto",
                   "neto quincenal", "neto semanal", "sueldo mensual", "ingreso mensual",
                   "salario mensual", "sd real", "sd fiscal", "asimilado", "importe",
                   "salario diario", "remuneracion", "monto",
                   "sueldo", "salario", "pago"]

    EMPLEADOS_KEYS = ["cantidad", "headcount", "num_empleados", "numero de empleados", "qty"]

    resultado = {"puesto": None, "sueldo": None, "sueldo_vacio": False, "num_empleados": None}
    mejor_puesto_score = 0
    mejor_sueldo_score = 0
    mejor_sueldo_solo_nombre = 0  # Fallback: name match without value validation

    for col in df.columns:
        if str(col).lower().startswith("unnamed"):
            continue
        col_norm = _normalizar(col)

        # --- PUESTO ---
        if any(ex in col_norm for ex in PUESTO_EXCLUIR):
            pass  # skip
        else:
            score = 0
            for k in PUESTO_HIGH:
                if k in col_norm:
                    score += len(k) * 2
            for k in PUESTO_LOW:
                if k in col_norm:
                    score += len(k)
            if score > mejor_puesto_score and _es_columna_texto(df, col):
                mejor_puesto_score = score
                resultado["puesto"] = col

        # --- SUELDO ---
        # Step 1: Score by name match (always)
        score_s = 0
        for k in SUELDO_KEYS:
            if k in col_norm:
                score_s += len(k) * 2

        if score_s > 0:
            # Track best name-only match as fallback
            if score_s > mejor_sueldo_solo_nombre:
                mejor_sueldo_solo_nombre = score_s
                _sueldo_fallback = col

            # Step 2: Prefer columns with valid numeric data
            if score_s > mejor_sueldo_score and _es_columna_numerica(df, col):
                try:
                    vals = pd.to_numeric(df[col], errors="coerce").dropna()
                    if len(vals) > 0 and vals.median() >= 500:
                        mejor_sueldo_score = score_s
                        resultado["sueldo"] = col
                except Exception:
                    pass

        # --- NUM EMPLEADOS ---
        score_e = sum(len(k) for k in EMPLEADOS_KEYS if k in col_norm)
        if score_e > 0 and _es_columna_numerica(df, col):
            resultado["num_empleados"] = col

    # Fallback: column name matched but values are empty/zero → accept with warning flag
    if resultado["sueldo"] is None and mejor_sueldo_solo_nombre > 0:
        resultado["sueldo"] = _sueldo_fallback
        resultado["sueldo_vacio"] = True

    # Fallback puesto: si no se encontró, buscar columna con nombre/empleado/trabajador
    if resultado["puesto"] is None:
        PUESTO_FALLBACK = ["nombre", "empleado", "trabajador", "personal"]
        for col in df.columns:
            if str(col).lower().startswith("unnamed"):
                continue
            col_norm = _normalizar(col)
            if any(k in col_norm for k in PUESTO_FALLBACK) and _es_columna_texto(df, col):
                resultado["puesto"] = col
                break

    return resultado


# ============================================================
# LIMPIEZA DE FILAS DE RESUMEN / TOTALES
# ============================================================
def limpiar_filas_resumen(df, col_sueldo):
    """Elimina filas de totales, resúmenes y valores no numéricos en sueldo."""
    if col_sueldo not in df.columns:
        return df
    # Eliminar filas con texto en columna de sueldo
    mask = pd.to_numeric(df[col_sueldo], errors="coerce").notna()
    # Eliminar filas donde primera columna contiene palabras de resumen
    primera_col = df.columns[0]
    palabras_resumen = ["suma", "total", "subtotal", "desgloce", "nomina", "costo",
                        "comision", "factura", "none", "nan", ""]
    mask2 = ~df[primera_col].astype(str).str.lower().str.strip().isin(palabras_resumen)
    return df[mask & mask2].reset_index(drop=True)


# ============================================================
# DETECCIÓN DE PERÍODO DE NÓMINA
# ============================================================
FACTOR_PERIODO = {"quincenal": 2, "semanal": 4.33, "mensual": 1}
KEYWORDS_QUINCENAL = ["quincenal", "quincena", "qna", "15 dias", "15dias"]
KEYWORDS_SEMANAL   = ["semanal", "semana", "sem", "7 dias", "7dias"]
KEYWORDS_MENSUAL   = ["mensual", "mes", "monthly"]

def detectar_periodo(df):
    cols_str = " ".join([_normalizar(str(c)) for c in df.columns])
    for kw in KEYWORDS_QUINCENAL:
        if kw in cols_str:
            return "quincenal"
    for kw in KEYWORDS_SEMANAL:
        if kw in cols_str:
            return "semanal"
    for kw in KEYWORDS_MENSUAL:
        if kw in cols_str:
            return "mensual"
    for col in df.columns:
        if _es_columna_numerica(df, col):
            try:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(vals) > 0 and vals.median() < SALARIO_MINIMO_MENSUAL * 0.7:
                    return "quincenal"
            except Exception:
                pass
    return "mensual"

def convertir_a_bruto_mensual(valor, periodo, tipo_salario):
    from motor_calculo import neto_a_bruto
    factor = FACTOR_PERIODO.get(periodo, 1)
    mensual = valor * factor
    if tipo_salario == "neto":
        return neto_a_bruto(mensual)
    return mensual


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
        serie = df[col_sueldo]
        if isinstance(serie, pd.DataFrame):
            serie = serie.iloc[:, 0]
        valores = pd.to_numeric(serie, errors="coerce").dropna()
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
