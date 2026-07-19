# SEO Rank Tracker

Herramienta independiente para auditar gratuitamente datos de Google Search Console, Bing Webmaster Tools e importaciones manuales relacionadas con Google generative AI.

No modifica la web y no implementa APIs SERP de pago ni APIs de modelos de IA en esta fase.

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

Variables:

```env
GSC_PROPERTY=
GOOGLE_CLIENT_SECRET_FILE=
GOOGLE_TOKEN_FILE=
```

Pasos:

1. Verifica la propiedad `https://rentalscooterbarcelona.com/` en Google Search Console.
2. Crea credenciales OAuth 2.0 de aplicación de escritorio en Google Cloud.
3. Descarga el JSON como `client_secret*.json` dentro de una carpeta local ignorada, por ejemplo `credentials/`.
4. Define `GOOGLE_CLIENT_SECRET_FILE` con esa ruta.
5. Define `GOOGLE_TOKEN_FILE` con una ruta local para el token.
6. Define `GSC_PROPERTY` con la propiedad exacta de Search Console.
7. Usa solo el alcance `https://www.googleapis.com/auth/webmasters.readonly`.

## Bing Webmaster Tools

Variables:

```env
BING_WEBMASTER_API_KEY=
BING_SITE_URL=
```

Pasos:

1. Verifica el sitio en Bing Webmaster Tools.
2. Obtén una API key de solo lectura si está disponible para la cuenta.
3. Define `BING_SITE_URL` con la URL verificada.
4. Define `BING_WEBMASTER_API_KEY` en `.env` local, nunca en Git.

## Importación manual Google generative AI

Coloca CSV manuales en:

```text
imports/google-ai/
```

Columnas reconocidas: `date`, `page`, `url`, `country`, `device`, `impressions`, `brand_mentioned`, `domain_cited`, `citation_url`.

La importación conserva los archivos originales, informa columnas desconocidas, no inventa consultas, no inventa posiciones y no presenta impresiones de IA como ranking orgánico.
