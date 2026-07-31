# Radar Minero — Versión 0.1

Primera versión visual del feed móvil de noticias mineras.

## Qué incluye

- Diseño oscuro y mobile-first.
- Cinta superior animada de indicadores.
- Cuatro noticias de Chile y tres internacionales.
- Tarjetas completas clickeables.
- Apertura directa de la fuente original.
- Contenido y valores simulados claramente identificados.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

```text
radar_minero_v0_1/
├── app.py
├── requirements.txt
├── data/
│   ├── __init__.py
│   └── mock_data.py
└── ui/
    ├── __init__.py
    ├── components.py
    └── styles.py
```

## Siguiente versión

1. Probar la interfaz en iPhone.
2. Ajustar identidad visual.
3. Reemplazar una noticia simulada por una fuente RSS real.
4. Conectar el dólar observado y el precio diario del cobre.
