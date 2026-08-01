# Radar Minero — Versión 0.4

Selección editorial inteligente de noticias mineras para lectura móvil.

## Qué cambia

- Cochilco fue eliminado como fuente de noticias por la fricción de acceso/registro.
- Se agregó SONAMI como fuente chilena pública.
- Se agregaron Rio Tinto y Glencore al bloque internacional.
- El sistema ya no toma simplemente la primera noticia de cada página.
- Se recopilan y deduplican candidatos de todas las fuentes.
- Un ranking local reduce el conjunto a un máximo de 32 candidatos.
- Gemini 3.5 Flash evalúa en una sola llamada:
  - importancia global;
  - relevancia para un estudiante de Ingeniería Civil de Minas;
  - valor sustantivo versus contenido corporativo;
  - historias que corresponden al mismo evento.
- El orden que recibe Gemini se baraja para evitar sesgo hacia la primera posición.
- La salida final mantiene diversidad de fuentes y una cuota flexible Chile/Mundo.
- Si Gemini o la API fallan, la app continúa con el ranking local.

## Activar Gemini en Streamlit

1. Crea una API key en Google AI Studio.
2. Abre tu app en Streamlit Community Cloud.
3. Ve a `Manage app` → `Settings` → `Secrets`.
4. Agrega:

```toml
GEMINI_API_KEY = "TU_API_KEY"
GEMINI_MODEL = "gemini-3.5-flash"
```

5. Guarda los cambios y reinicia la app.

Nunca subas la API key a GitHub.

## Flujo editorial

```text
Fuentes públicas
    ↓
Normalización
    ↓
Deduplicación local
    ↓
Prefiltro técnico (máx. 16 Chile + 16 Mundo)
    ↓
Evaluación agrupada con Gemini
    ↓
Combinación IA + recencia + autoridad
    ↓
Diversidad de fuentes
    ↓
4 Chile + 3 Mundo, con cuota flexible
```

## Actualización

Las noticias y el ranking se mantienen en caché durante tres horas. Solo se hace una llamada agrupada a Gemini por actualización, no una llamada por noticia.
