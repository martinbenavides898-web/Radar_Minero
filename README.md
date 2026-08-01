# Radar Minero — Versión 0.5

Integración de mercados oficiales del Banco Central de Chile.

## Indicadores

La cinta superior muestra:

- Dólar observado, pesos por dólar.
- Precio del cobre, dólares por libra.
- Precio del oro, dólares por onza troy.

Los valores se obtienen desde las series públicas de Indicadores Diarios del
Banco Central de Chile. No se requiere registro ni una API key adicional.

## Variación

Cada indicador compara la observación más reciente con la observación oficial
inmediatamente anterior:

```text
variación = (valor actual / valor anterior - 1) × 100
```

La flecha verde indica aumento y la roja disminución.

## Caché y respaldo

- Noticias: caché de 3 horas.
- Mercados: caché independiente de 6 horas.
- Si el Banco Central falla temporalmente, la aplicación intenta usar el último
  resultado oficial guardado durante la vida del servidor.
- Si nunca ha existido una descarga correcta, la cinta informa que los datos no
  están disponibles. Nunca vuelve a mostrar cifras simuladas.

## Archivos nuevos

```text
src/market_service.py
```

El antiguo archivo `data/market_data.py` fue eliminado porque contenía valores
de demostración.
