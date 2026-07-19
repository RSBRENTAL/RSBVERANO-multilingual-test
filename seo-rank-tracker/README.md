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
