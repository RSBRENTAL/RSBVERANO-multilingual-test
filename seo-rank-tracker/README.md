# SEO Rank Tracker

Herramienta independiente para auditar gratuitamente datos de Google Search Console, Bing Webmaster Tools e importaciones manuales relacionadas con Google generative AI.

No modifica la web y no implementa APIs SERP de pago ni APIs de modelos de IA en esta fase. Los dry-run usan `status=dry_run` y no escriben informes reales.

## Comandos

```bash
python -m src.main google
python -m src.main bing
python -m src.main import-google-ai
python -m src.main report
python -m src.main all
python -m src.main all --dry-run
```

Ejecuta los comandos desde la carpeta `seo-rank-tracker/`.

## Datos no disponibles

Cuando una credencial, API, campo o archivo no existe, la herramienta muestra `No disponible`. `average_position` procede de datos agregados y nunca debe presentarse como `exact_organic_position`.

## Google Search Console

Variables en `.env` local, cargado automáticamente y no versionado:

```env
GSC_PROPERTY=
GOOGLE_CLIENT_SECRET_FILE=
GOOGLE_TOKEN_FILE=
```

Pasos:

1. Verifica la propiedad `https://rentalscooterbarcelona.com/` en Google Search Console.
2. Crea credenciales OAuth 2.0 de aplicación de escritorio en Google Cloud.
3. Guarda el JSON como `client_secret*.json` fuera del repositorio o dentro de `seo-rank-tracker/credentials/`, carpeta ignorada.
4. Define `GOOGLE_CLIENT_SECRET_FILE` con esa ruta.
5. Define `GOOGLE_TOKEN_FILE` con una ruta ignorada, nunca versionada.
6. Define `GSC_PROPERTY` con la propiedad exacta de Search Console.
7. La primera ejecución sin token abrirá el consentimiento OAuth local y guardará el token solo en `GOOGLE_TOKEN_FILE`.
8. Usa solo el alcance `https://www.googleapis.com/auth/webmasters.readonly`.

La consulta usa dimensiones `date`, `query`, `page`, `country` y `device`. `position` se guarda como `average_position`.

## Bing Webmaster Tools

Variables:

```env
BING_WEBMASTER_API_KEY=
BING_SITE_URL=
```

Pasos:

1. Verifica el sitio en Bing Webmaster Tools.
2. Obtén una API key para Bing Webmaster Tools.
3. Define `BING_SITE_URL` con la URL verificada.
4. Define `BING_WEBMASTER_API_KEY` en `.env` local, nunca en Git.

El conector intenta métodos oficiales de solo lectura relacionados con estadísticas: `GetQueryStats`, `GetPageStats`, `GetRankAndTrafficStats` y `GetQueryPageStats`. Si la API no devuelve país o dispositivo, esos campos quedan vacíos.

## Importación manual Google generative AI

Coloca CSV manuales en:

```text
imports/google-ai/
```

Columnas reconocidas: `date`, `page`, `url`, `country`, `device`, `impressions`, `brand_mentioned`, `domain_cited`, `citation_url`.

La importación conserva los archivos originales, informa columnas desconocidas, no inventa consultas, no inventa posiciones y no presenta impresiones de IA como ranking orgánico.

## Informes

Los informes se generan localmente en `reports/` y están ignorados por Git. El HTML incluye filtros de navegador para source, language, query, category, scenario, country, city, device, page/url, period y status.

## Notas técnicas Search Console

Search Console puede tener retraso de varios días. Cuando no se pasa `--end-date`, la herramienta primero consulta los últimos 10 días agrupados por `date` y usa la fecha más reciente con datos disponibles. La extracción del periodo se ejecuta día por día con `type=web`, dimensiones `date`, `query`, `page`, `country` y `device`, y paginación `rowLimit=25000`/`startRow`. Esta API no debe presentarse como exportación completa garantizada: si un día alcanza límites de paginación, se registra una advertencia.

Los datos de Search Console no representan una ubicación física exacta como Plaça de Catalunya. Por eso las filas de Search Console conservan `country` y `device` devueltos por Google, dejan `city` y `scenario` vacíos, y usan `country_format=iso_3166_1_alpha_3` cuando Google devuelve país.

## Bing detallado

Por defecto Bing ejecuta solo métodos generales. Para llamar `GetQueryPageStats` por cada consulta activa única, usa:

```bash
python -m src.main bing --bing-detailed
```

Bing `GetQueryPageStats` conserva `requested_query` y `returned_query_value`. Solo rellena `url` si Bing devuelve explícitamente un campo `Page` o `Url`; si no existe, la URL queda vacía porque el endpoint no documenta una página en todos los contratos/respuestas.

## Límite diario Search Console

La herramienta pagina Search Console hasta recibir menos de 25.000 filas o respuesta vacía. Solo marca `data_limit_reached=true` y `status=warning` cuando se alcanzan 50.000 filas en un día y tipo de búsqueda, con el mensaje: `Search Console daily exposure limit reached; additional rows may not be available`.

Cuando el periodo actual o anterior alcance ese límite, se generan filas de advertencia separadas con `current_period_data_limit_reached`, `previous_period_data_limit_reached` y `data_limit_reached`. Si el límite afecta al periodo anterior, `comparison_reliable=false` y el cambio de posición no se presenta como comparación fiable.
