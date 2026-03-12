from supabase import create_client
import streamlit as st

def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def guardar_propuesta(cliente, esquema, num_empleados, ahorro_mensual,
                      ahorro_anual, costo_actual, costo_propuesto,
                      usuario="Seba", notas=""):
    sb = get_supabase()
    data = {
        "cliente": cliente,
        "esquema": esquema,
        "num_empleados": num_empleados,
        "ahorro_mensual": ahorro_mensual,
        "ahorro_anual": ahorro_anual,
        "costo_actual": costo_actual,
        "costo_propuesto": costo_propuesto,
        "usuario": usuario,
        "notas": notas,
    }
    return sb.table("propuestas").insert(data).execute()

def obtener_propuestas():
    sb = get_supabase()
    return sb.table("propuestas").select("*").order("created_at",
           desc=True).execute()
