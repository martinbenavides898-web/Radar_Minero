# Radar Minero — Versión 0.4.1

Corrección de diversidad internacional y recuperación de fuentes.

## Problema corregido

La versión 0.4 podía completar las tres tarjetas de Mundo con tres publicaciones
de una sola compañía cuando las demás fuentes no respondían.

La versión 0.4.1 aplica estas reglas:

- Si responde una sola fuente internacional, muestra solo su noticia más importante.
- Si responden dos fuentes, permite como máximo dos tarjetas de una misma fuente.
- Si responden tres o más fuentes, las tres tarjetas pertenecen a fuentes diferentes.
- Nunca rellena espacios solo para aparentar que existen más fuentes disponibles.
- El bloque Chile permite como máximo dos noticias de un mismo medio.
- El prefiltro entrega primero una oportunidad a cada fuente antes de incluir repetidas.

## Recuperación de fuentes

Los sitios corporativos construidos con JavaScript pueden no exponer sus enlaces
en el HTML inicial. Cuando esto ocurre, Radar Minero intenta recuperar noticias
desde los sitemaps públicos y oficiales del mismo dominio.

Esto mejora especialmente los conectores de:

- BHP
- Rio Tinto
- Glencore
- Anglo American
- Antofagasta plc

## Gemini

Gemini continúa evaluando importancia, relevancia y valor sustantivo.

Después de seleccionar las noticias internacionales, una segunda llamada pequeña
traduce únicamente las tarjetas elegidas:

- título natural en español;
- resumen de dos o tres oraciones;
- sin agregar hechos que no aparezcan en la publicación recuperada.

Si la traducción falla, la noticia sigue disponible con su texto original.

## Actualización

Las fuentes, el ranking y las traducciones permanecen en caché durante tres horas.
