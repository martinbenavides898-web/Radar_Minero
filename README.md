# Radar Minero — Versión 0.3

Corrección de diversidad, duplicados y sección internacional.

## Cambios

- Deduplicación por URL y similitud entre titulares.
- Máximo inicial de una noticia por fuente antes de repetir un medio.
- Cuatro noticias de Chile provenientes de distintas fuentes cuando estén disponibles.
- Tres noticias internacionales con respaldo para evitar una sección vacía.
- Fuentes chilenas:
  - Codelco
  - Cochilco
  - Ministerio de Minería
  - Reporte Minero
  - Minería Chilena
- Fuentes internacionales:
  - MINING.com
  - BHP
  - Anglo American
  - Antofagasta plc
- Descarga paralela de fuentes para reducir el tiempo de espera.
- Mensaje discreto con cantidad de fuentes activas.
- Fallbacks reales con enlaces exactos, no portadas generales.

## Actualización

El resultado se mantiene en caché durante tres horas.
