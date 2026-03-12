# procesador_nomina.py — Procesador de archivos de nómina (Excel/CSV)
# Detección de columnas, mapeo de puestos, validación

import unicodedata
import difflib
import json
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
# DETECCIÓN DINÁMICA DE FILA DE ENCABEZADO
# ============================================================
_SALARY_KEYS = ["sueldo", "salario", "deposito", "neto", "importe",
                "total", "monto", "percepciones", "asimilado"]
_NAME_KEYS = ["nombre", "empleado", "trabajador", "name"]
_ID_KEYS = ["n°", "no.", "num", "numero", "clave", "rfc", "id"]


def _fila_es_header(df_raw, idx):
    """Evalúa si la fila idx contiene patrones de encabezado de nómina."""
    fila = df_raw.iloc[idx]
    salary_count = 0
    name_count = 0
    id_count = 0
    for v in fila:
        if pd.isna(v):
            continue
        cell = _normalizar(str(v))
        if not cell or cell in ("nan", "none"):
            continue
        if any(kw in cell for kw in _SALARY_KEYS):
            salary_count += 1
        if any(kw in cell for kw in _NAME_KEYS):
            name_count += 1
        if any(kw in cell for kw in _ID_KEYS):
            id_count += 1
    # Condition 1: at least 1 NAME/ID + 1 SALARY
    if (name_count >= 1 or id_count >= 1) and salary_count >= 1:
        return True
    # Condition 2: total >= 3
    if salary_count + name_count + id_count >= 3:
        return True
    return False


def detectar_fila_header(df_raw):
    """
    Escanea filas 0-20 (luego 0-30) buscando la fila de encabezado.
    Retorna (fila_index, encontrado: bool).
    Si no encuentra, retorna (0, False).
    """
    for i in range(min(20, len(df_raw))):
        if _fila_es_header(df_raw, i):
            return i, True
    for i in range(20, min(30, len(df_raw))):
        if _fila_es_header(df_raw, i):
            return i, True
    return 0, False


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


def preparar_dataframe(df):
    """
    Limpia el DataFrame después de leerlo con el header correcto:
    - Strip column names
    - Fuerza conversión numérica en columnas que parecen dinero
    - Elimina filas completamente vacías
    - Reset index
    """
    df.columns = [str(c).strip() for c in df.columns]

    # Force numeric on ALL columns that look like money
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors='coerce')
        if converted.notna().sum() > 0:
            df[col] = converted

    # Drop fully empty rows
    df = df.dropna(how='all')

    # Drop leading spacer rows after header (NaN/0 in sueldo column)
    col_sueldo, _ = detectar_columna_sueldo(df)
    if col_sueldo and col_sueldo in df.columns:
        sueldo_num = pd.to_numeric(df[col_sueldo], errors='coerce')
        first_valid = sueldo_num[sueldo_num >= 10].index.min()
        if pd.notna(first_valid):
            df = df.loc[first_valid:]

    # Reset index
    df = df.reset_index(drop=True)
    return df


def detectar_columna_sueldo(df):
    """
    Score-based salary column detection.
    Returns (column_name or None, is_empty: bool).
    """
    PRIO_HIGH = ["neto real", "total deposito", "deposito total",
                 "total a depositar", "neto real mensual", "deposito"]
    PRIO_MED = ["sueldo", "neto", "bruto", "sueldo neto", "salario neto",
                "sueldo bruto", "bruto mensual"]
    PRIO_LOW = ["salario", "importe", "percepcion", "monto", "pago",
                "remuneracion", "asimilado"]

    mejor_col = None
    mejor_score = -1
    mejor_nonzero = -1
    fallback_col = None
    fallback_nscore = 0

    for col in df.columns:
        if str(col).lower().startswith("unnamed"):
            continue
        col_norm = _normalizar(col)

        name_score = 0
        if any(k in col_norm for k in PRIO_HIGH):
            name_score = 3
        elif any(k in col_norm for k in PRIO_MED):
            name_score = 2
        elif any(k in col_norm for k in PRIO_LOW):
            name_score = 1

        if name_score == 0:
            continue

        try:
            serie = df[col].iloc[:, 0] if isinstance(df[col], pd.DataFrame) else df[col]
            nums = pd.to_numeric(serie, errors="coerce").dropna()
            value_score = int(nums.ge(100).sum())
            nonzero = int(nums.ne(0).sum())
        except Exception:
            value_score = 0
            nonzero = 0

        total_score = name_score * 2 + value_score

        if name_score > fallback_nscore:
            fallback_nscore = name_score
            fallback_col = col

        if value_score > 0 and (total_score > mejor_score or
                                (total_score == mejor_score and nonzero > mejor_nonzero)):
            mejor_score = total_score
            mejor_col = col
            mejor_nonzero = nonzero

    if mejor_col is not None:
        return mejor_col, False
    if fallback_col is not None:
        return fallback_col, True
    return None, False


def detectar_columnas(df):
    """
    Auto-detecta columnas de puesto, sueldo y num_empleados.
    Retorna dict con las columnas encontradas (nombre original).
    """
    # --- SUELDO (dedicated function) ---
    col_sueldo, sueldo_vacio = detectar_columna_sueldo(df)

    PUESTO_HIGH = ["puesto", "cargo", "plaza", "posicion", "rol"]
    PUESTO_LOW  = ["categoria", "departamento", "area"]
    PUESTO_EXCLUIR = ["nombre", "clave", "rfc", "curp", "nss", "empleado", "banco", "cuenta", "clabe"]
    EMPLEADOS_KEYS = ["cantidad", "headcount", "num_empleados", "numero de empleados", "qty"]

    resultado = {"puesto": None, "sueldo": col_sueldo, "sueldo_vacio": sueldo_vacio, "num_empleados": None}
    mejor_puesto_score = 0

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

        # --- NUM EMPLEADOS ---
        score_e = sum(len(k) for k in EMPLEADOS_KEYS if k in col_norm)
        if score_e > 0 and _es_columna_numerica(df, col):
            resultado["num_empleados"] = col

    # Fallback puesto: si no se encontró, buscar columna con nombre/empleado/trabajador
    if resultado["puesto"] is None:
        PUESTO_FALLBACK = ["puesto", "nombre", "empleado", "trabajador", "personal"]
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
_PALABRAS_RESUMEN_EXACT = [
    "total", "suma", "subtotal", "comision", "comisión", "desgloce",
    "nomina", "costo", "factura", "none", "nan", "",
    "iva", "isr", "imss", "infonavit",
]
_PALABRAS_RESUMEN_PARTIAL = [
    r"\btotal\b", r"\bsuma\b", r"\bsubtotal\b", r"\bcomision\b", r"\bcomisión\b",
    r"\biva\b", r"\bisr\b", r"\bimss\b", r"\binfonavit\b",
    r"\bimpuesto\b", r"\bdesgloce\b", r"\bconcepto\b",
    r"\bdescripcion\b", r"\bpromedio\b", r"\bobservacion\b",
]
_RESUMEN_PATTERN = "|".join(_PALABRAS_RESUMEN_PARTIAL)


def limpiar_filas_resumen(df, col_sueldo, col_nombre=None):
    """Elimina filas de totales, resúmenes, sueldo < 10 y valores no numéricos."""
    if col_sueldo not in df.columns:
        return df

    # Force numeric conversion on sueldo column
    df[col_sueldo] = pd.to_numeric(df[col_sueldo], errors="coerce").fillna(0)

    # Eliminar filas con sueldo == 0 (was NaN/text)
    mask = df[col_sueldo] != 0

    # Eliminar filas con sueldo < 10
    mask_min = df[col_sueldo] >= 10

    # Eliminar filas donde primera columna contiene palabras de resumen (exact match)
    primera_col = df.columns[0]
    mask2 = ~df[primera_col].astype(str).str.lower().str.strip().isin(_PALABRAS_RESUMEN_EXACT)

    # Eliminar filas donde col_nombre contiene palabras de resumen o está vacío
    if col_nombre and col_nombre in df.columns:
        nombre_str = df[col_nombre].astype(str).str.lower().str.strip()
        mask3 = ~nombre_str.str.contains(_RESUMEN_PATTERN, na=False, regex=True)
        mask_nombre = (nombre_str != "") & (nombre_str != "nan") & (nombre_str != "none")
    else:
        mask3 = True
        mask_nombre = True

    return df[mask & mask_min & mask2 & mask3 & mask_nombre].reset_index(drop=True)


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
            warnings.append(f"{no_numerico} filas con valores no numericos en '{col_sueldo}' seran omitidas.")

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


# ============================================================
# DETECCIÓN DE ESTRUCTURA CON IA (Claude API)
# ============================================================
def detectar_estructura_con_ia(df_raw, sheet_name):
    """
    Envía las primeras 25 filas del DataFrame raw a Claude API.
    Claude identifica: header row, columna de sueldo, columna de nombre,
    filas de empleados válidos.
    Retorna dict con resultados o None si falla.
    """
    try:
        import anthropic
    except ImportError:
        return None

    preview = df_raw.head(25).to_string()

    prompt = f"""Analiza esta hoja de Excel llamada "{sheet_name}".

Aquí están las primeras 25 filas (raw, sin headers):
{preview}

Identifica:
1. header_row: número de fila (0-indexed) donde están los nombres de columnas reales
2. sueldo_col: número de columna (0-indexed) que contiene el SUELDO o DEPOSITO real de cada empleado (NO totales, NO sumas)
3. nombre_col: número de columna (0-indexed) que contiene el NOMBRE del empleado
4. filas_empleados: lista de números de fila que son empleados reales (excluye SUMA, TOTAL, COSTO, encabezados, pies de página)
5. razon: explicación breve de tu decisión

IMPORTANTE:
- El sueldo de un empleado típico en México está entre $5,000 y $200,000 mensual
- Las filas de SUMA/TOTAL/COSTO no son empleados
- Responde SOLO con JSON válido, sin texto adicional

Ejemplo de respuesta:
{{
  "header_row": 4,
  "sueldo_col": 3,
  "nombre_col": 1,
  "filas_empleados": [5, 6, 7, 8],
  "razon": "Header en fila 4, TOTAL DEPOSITO en col 3, empleados en filas 5-8"
}}"""

    try:
        import streamlit as st
        import os
        api_key = st.secrets.get("ANTHROPIC_API_KEY", None) or os.getenv("ANTHROPIC_API_KEY")
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        result = json.loads(message.content[0].text)
        # Validate expected keys
        for key in ("header_row", "sueldo_col", "nombre_col", "filas_empleados"):
            if key not in result:
                return None
        return result
    except Exception:
        return None
