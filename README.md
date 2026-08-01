# Radar Minero — Versión 0.7

Resúmenes editoriales uniformes con Gemini.

## Nuevo flujo

```text
Fuentes
  ↓
Deduplicación
  ↓
Ranking y diversidad
  ↓
Selección final de 4 Chile + 3 Mundo
  ↓
Una sola edición editorial con Gemini
  ↓
Tarjetas
```

Gemini no resume todas las noticias candidatas. Edita solamente las historias que
ya ganaron un espacio en el feed, reduciendo tiempo y consumo.

## Qué edita

Para cada tarjeta:

- título profesional y directo;
- español natural para noticias chilenas e internacionales;
- resumen objetivo de aproximadamente 55 a 85 palabras;
- dos o tres oraciones;
- hecho central, actores, proyecto y consecuencia inmediata;
- cifras únicamente cuando ya estaban presentes en el material recuperado.

## Controles contra alucinaciones

La aplicación valida cada respuesta antes de mostrarla:

- no acepta cifras nuevas que no aparezcan en el título o resumen original;
- rechaza títulos o resúmenes con extensiones anómalas;
- rechaza frases editoriales como “por qué importa” o “la noticia destaca”;
- exige que cada identificador corresponda a una historia seleccionada;
- si una tarjeta no supera la validación, conserva automáticamente el texto original.

Por eso la aplicación puede indicar, por ejemplo:

```text
Selección con Gemini · 6 resúmenes editados · 7/11 fuentes · 8.6 s
```

## Respaldo

- Si Gemini falla completamente, las siete noticias siguen disponibles.
- Si solo una edición falla, únicamente esa tarjeta conserva el texto original.
- El último feed válido guarda los resúmenes ya editados.
- La caché de noticias continúa siendo de tres horas.

## Sin nuevas pantallas

La interfaz y la navegación no cambian. La mejora está concentrada en la calidad
y consistencia del contenido.
