# TRAVI Open Toolkit

An early bilingual menu builder for independent shops and cafés. No AI service or API key is required. AI translation is a future direction, not an implemented feature.

## Features

- Vietnamese and English names and descriptions, categories, optional prices and availability.
- HTTPS image links or local JPG/PNG/WebP uploads up to 2 MB each.
- Browser drafts, item ordering, HTML download and browser printing to PDF.
- Public menu URLs, SVG QR codes, updates and deletion using a private edit key.
- Edit-key export and recovery on another device.

## Why we plan to use Claude

Claude API is planned as an optional language and reasoning layer to help independent shop owners serve customers across languages and spend less time preparing content. The core menu builder will continue to work without an AI account.

- **Menu translation:** draft English and other language versions while preserving local dish names, prices and the ingredients supplied by the owner.
- **Product descriptions:** turn owner-provided notes into clear, concise descriptions. Do not infer ingredients, allergens, nutritional values or certifications from photos or names.
- **Store assistance:** explain owner-selected documents and, in a later phase, sales summaries in plain language. Numerical calculations remain deterministic; Claude would explain the computed results.
- **Community resources:** help contributors adapt reusable menu and customer communication templates to local languages and contexts.

The first planned integration is a “Translate with Claude” action with a side-by-side review screen. An owner would select the fields to send, review the generated draft and explicitly approve changes before saving or publishing. API calls would run on the backend; keys would never be embedded in browser code or public menus. Operators would configure their own Anthropic account and pay API usage separately from the Apache-2.0 code.

Before release, we plan to add request limits, error handling and tests for preserving names, prices and supplied ingredient facts, then evaluate translations with bilingual reviewers. AI output can be inaccurate and will require human review.

**Current status:** this repository has no Claude integration, AI translation, document assistant or sales-data connector yet. These are development plans, not available features or a claim of partnership with Anthropic.

## Run with Docker

```bash
docker build -t travi-open-toolkit .
docker run -d --name travi-toolkit -p 127.0.0.1:8080:8080 \
  -e PUBLIC_BASE_URL=http://localhost:8080 \
  -v travi_toolkit_data:/data travi-open-toolkit
```

Open http://localhost:8080. For public hosting, configure an HTTPS reverse proxy and set PUBLIC_BASE_URL to your actual public domain. The QR code uses this value. Avoid exposing the Python server directly to the internet.

## Run locally

```bash
python -m pip install -r requirements.txt
DATA_DIR=./data PUBLIC_BASE_URL=http://localhost:8080 python server.py
```

## Ownership and privacy

Anyone who possesses a menu's edit key can update or delete it. Download the recovery file and keep it private. Losing every copy of the key means losing the ability to edit through the app. Public menus and their images can be viewed by anyone with their URL. Remote images connect to the image host. Browser drafts and edit keys are stored locally; published menu content is stored in SQLite on the server. There are no analytics or AI calls.

## Limits and operations

Maximum 30 items per menu, 7 MB of stored JSON per menu, 500 published menus per instance and five new menus per socket IP per hour. Behind a reverse proxy, visitors may share this rate limit. This is a prototype, not a hardened multi-tenant hosting service. Add proxy rate limits, storage monitoring, abuse reporting and operator moderation before broad public hosting. Rate limits reset on restart. Uploaded images embedded as data URLs can exhaust browser storage; export a copy when a save warning appears.

Back up the data volume using SQLite's backup API or stop the container before copying its database. Keep backup files private. Test restoring on a separate instance before relying on backups.

## License

Code is licensed under Apache-2.0. The TRAVI name does not imply endorsement of forks. This source bundle contains no café photos, company credentials, private menu data or VPS configuration. External image rights remain with their owners.

## Validation

Run `python -m unittest discover -s tests`. JavaScript syntax can be checked with `node --check site/menu-demo.js` and `node --check site/builder.js`. Browser interaction, PDF output and QR scanning still require manual validation on your target devices.
