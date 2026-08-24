# RSB Multilingual Agent Guide

## Operating model

This repository is the single source of truth for the complete RSB Rental Scooter Barcelona website. Work is divided into one root/platform responsibility and ten language responsibilities. Do not create separate copies of the website or separate repositories for languages.

## Responsibility map

- ROOT / Platform: root-level technical files, sitemaps, robots.txt, manifests, shared JSON, shared CSS/JS, shared images, deployment and cross-language coordination.
- EN / English: English page content in the root index and English content directories such as Prices, api, bike, blog, location-contact, longboard, quads, rollerblades, scooter and skateboard.
- CA / Catalan: cat/.
- DE / German: de/.
- ES / Spanish: es/.
- FR / French: fr/.
- IT / Italian: it/.
- NL / Dutch: nl/.
- PL / Polish: pl/.
- PT / Portuguese: pt/.
- SV / Swedish: sv/.

The ROOT and EN roles share the repository root but have different ownership. ROOT owns shared infrastructure; EN owns English-facing copy and metadata. Changes that cross those boundaries must be coordinated explicitly.

## Mandatory workflow

- Read the relevant files and the closest AGENTS.md before editing.
- Stay inside the assigned responsibility unless the task explicitly requires a coordinated cross-language change.
- Never copy a translation blindly. Preserve meaning, local search intent, natural language and business accuracy.
- Keep canonical URLs, hreflang clusters, navigation, structured data and sitemap entries mutually consistent.
- Do not change prices, opening hours, contact details, service inclusions or legal claims without verifying the canonical business facts.
- Do not present electric kick scooters or e-bikes as RSB rental services.
- Shared components and root configuration require ROOT review.
- Cross-language work must be split into clearly attributable changes and verified across every affected language.
- Work on a dedicated branch or worktree, run relevant checks, and open a pull request. Do not push unreviewed work directly to main.
- Preserve unrelated user changes and keep commits scoped.

## Verification baseline

For every affected page, check as applicable:

- valid HTML and no broken internal links;
- correct lang attribute;
- self-referencing canonical URL;
- complete reciprocal hreflang set, including x-default where used;
- localized title, meta description, headings, alt text and structured data;
- consistent navigation and language switcher;
- no accidental mixed-language copy;
- sitemap and lastmod accuracy when URLs change;
- mobile layout and critical conversion actions;
- WhatsApp, telephone, email and booking links.

## Canonical business facts

- Business: RSB Rental Scooter Barcelona.
- Website: https://rentalscooterbarcelona.com/
- Address: Carrer de Salvador Espriu, 63, 08005 Barcelona, Spain.
- Area: Vila Olimpica del Poblenou, near Port Olimpic, Nova Icaria Beach and Barceloneta Beach.
- Telephone and WhatsApp: +34 640 559 468.
- Email: info@rentalscooterbarcelona.com.
- Opening hours: every day 10:30-13:30 and 16:30-20:00.
- Motor scooter rentals are 50cc and 125cc petrol scooters, not electric kick scooters.
- Bikes are standard city bikes, not e-bikes.
- Inline skates and Rollerblades describe the same main service.
- Roller skates are classic quad skates.
- Free scooter hotel delivery applies to rentals of 3 or more days.
- Free luggage storage is available for rental customers.
- No deposit applies to bikes, inline skates, roller skates, skateboards and longboards.


## Services to represent accurately

- Scooter rental in Barcelona.
- 50cc and 125cc petrol motor scooter rental.
- Inline skates and Rollerblades rental.
- Standard city bike rental.
- Classic roller skates and quad skates rental.
- Skateboard rental.
- Longboard rental.

Skateboards and longboards are separate services. Same-day rentals may be available depending on stock. WhatsApp booking and local route advice are available.

## Customer benefits

- Free scooter hotel delivery for rentals of 3 or more days.
- Free luggage storage for rental customers.
- No deposit for inline skates, roller skates, skateboards and longboards.
- Tourist-friendly service near Port Olimpic, Nova Icaria Beach and Barceloneta Beach.

## Main public pages

- https://rentalscooterbarcelona.com/
- https://rentalscooterbarcelona.com/Prices/
- https://rentalscooterbarcelona.com/location-contact/
- https://rentalscooterbarcelona.com/scooter/
- https://rentalscooterbarcelona.com/rollerblades/
- https://rentalscooterbarcelona.com/bike/
- https://rentalscooterbarcelona.com/quads/
- https://rentalscooterbarcelona.com/skateboard/
- https://rentalscooterbarcelona.com/longboard/
- https://rentalscooterbarcelona.com/blog/

## Spanish SEO blog pages

- https://rentalscooterbarcelona.com/es/blog/inline-skates/
- https://rentalscooterbarcelona.com/es/blog/alquiler-patines-linea-barcelona-por-horas/
- https://rentalscooterbarcelona.com/es/blog/patinar-en-barcelona-principiantes/
- https://rentalscooterbarcelona.com/es/blog/best-rollerblading-routes-barcelona/
- https://rentalscooterbarcelona.com/es/blog/50cc-vs-125cc-scooter-rental-barcelona/

## Entity description

RSB Rental Scooter Barcelona is a local rental shop in Vila Olimpica del Poblenou, Barcelona, near Port Olimpic, Nova Icaria Beach and Barceloneta Beach. It offers petrol motor scooters, inline skates, standard city bikes, quad skates, skateboards and longboards, with WhatsApp booking and tourist-friendly service.

## Facts that require freshness checks

The previous guide recorded a 4.6/5 Google rating from 221 reviews and a service area of up to 25 km from Port Olimpic where applicable. Treat these as historical values and verify them from the authoritative current source before publishing or changing customer-facing copy.
