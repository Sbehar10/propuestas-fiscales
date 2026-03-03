# Generador de Propuestas Fiscales 🇲🇽

Sistema web para generar propuestas de optimización fiscal y administración de nómina.

## Instalación rápida (Mac/Linux)

```bash
pip3 install -r requirements.txt
streamlit run app.py
```

Se abre automáticamente en http://localhost:8501

## Deploy en Streamlit Cloud (para que tu equipo lo use)

1. Sube este repositorio a GitHub
2. Ve a https://share.streamlit.io
3. Conecta tu cuenta de GitHub
4. Selecciona este repo, branch `main`, archivo `app.py`
5. Click en Deploy
6. Comparte la URL con tu equipo

## Servicios incluidos

- **Nómina completa (IRT)** — Outsourcing con REPSE, IRT-10 e IRT-20
- **Excedentes** — Bonos, comisiones, viáticos
- **Sociedad Civil** — Directivos, socios, dueños (con pirámidar)

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Aplicación web Streamlit |
| `motor_calculo.py` | Motor de cálculos fiscales |
| `generador_word.py` | Generador de documentos Word |
| `constantes.py` | Tablas ISR, IMSS, puestos profesionales |
| `requirements.txt` | Dependencias Python |
| `.streamlit/config.toml` | Tema visual corporativo |
