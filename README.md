# Radar Minero — Versión 0.6

Versión centrada en estabilidad, continuidad y rendimiento.

## Mejoras

### Último feed válido

Cuando la actualización actual no consigue suficientes noticias:

1. Radar Minero carga las fuentes que sí respondieron.
2. Completa únicamente los espacios faltantes con el último feed exitoso.
3. Marca discretamente esas tarjetas como `RESPALDO`.
4. Nunca presenta una noticia antigua como si acabara de ser descargada.

El snapshot se guarda durante la ejecución del servidor en:

```text
.cache/news_snapshot.json
/tmp/radar_minero_news_snapshot.json
```

Streamlit Community Cloud puede borrar estos archivos al reconstruir completamente
el contenedor. Por eso existe también un respaldo inicial empaquetado, usado solo
cuando nunca se ha podido crear un snapshot real.

### Reintentos y límites

- Reintentos automáticos para errores transitorios, límites de tasa y timeouts.
- Backoff corto para no bloquear la interfaz.
- Presupuesto máximo aproximado por fuente.
- Descarga paralela con aislamiento de fallas.
- Una fuente rota no detiene las demás.

### Diagnóstico discreto

La parte inferior muestra solamente información útil:

```text
Selección con Gemini · 7/11 fuentes · 8.4 s
```

Cuando corresponde también informa:

- cantidad de tarjetas de respaldo;
- último feed válido;
- caída parcial de fuentes;
- uso automático del ranking local.

Los nombres técnicos de excepciones no aparecen en la interfaz.

### Carga

La aplicación muestra tarjetas skeleton mientras consulta mercados, recopila las
fuentes y realiza el ranking editorial.

## Sin feature creep

La versión 0.6 no agrega favoritos, buscador, cuentas ni navegación adicional.
