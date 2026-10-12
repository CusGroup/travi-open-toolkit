# TRAVI Open Toolkit

Open-source tools for independent shops and cafés, with a planned F&B operations assistant. Working prototypes include a bilingual menu builder and a local sales CSV workspace. An optional administrator-only Claude translation connector is implemented but has not been tested against a live provider. No API key is required for menu editing or CSV calculations.

## Features

- Vietnamese and English names and descriptions, categories, optional prices and availability.
- HTTPS image links or local JPG/PNG/WebP uploads up to 2 MB each.
- Browser drafts, item ordering, HTML download and browser printing to PDF.
- Public menu URLs, SVG QR codes, updates and deletion using a private edit key.
- Edit-key export and recovery on another device.

## Optional café admin backend

The [admin module](admin/README.md) includes login, product and category management, image uploads, availability and visibility controls, website content and appearance editing, SQLite storage and a minimal storefront. It is a separate single-store server with sample configuration and no production data. The admin interface is currently Vietnamese. The optional Claude translation pilot runs separately at /translate.html, with administrator authentication; it is not a production AI service.

## Why we plan to use Claude

Claude API is planned as an optional language and reasoning layer to help independent shop owners serve customers across languages and spend less time preparing content. The core menu builder will continue to work without an AI account.

- **Menu translation:** draft English and other language versions while preserving local dish names, prices and the ingredients supplied by the owner.
- **Product descriptions:** turn owner-provided notes into clear, concise descriptions. Do not infer ingredients, allergens, nutritional values or certifications from photos or names.
- **Store assistance:** explain owner-selected documents and, in a later phase, sales summaries in plain language. Numerical calculations remain deterministic; Claude would explain the computed results.
- **Community resources:** help contributors adapt reusable menu and customer communication templates to local languages and contexts.

The first implemented connector is a “Translate with Claude” action with a review screen in the optional admin module. Live API testing and pilot evaluation remain outstanding. An owner would select the fields to send, review the generated draft and explicitly approve changes before saving or publishing. API calls would run on the backend; keys would never be embedded in browser code or public menus. Operators would configure their own Anthropic account and pay API usage separately from the Apache-2.0 code.

Request caps, authentication, consent, response-shape validation and local tests are implemented. Next steps are live provider tests and translation evaluation with bilingual reviewers. Semantic preservation of ingredient facts still requires human review. AI output can be inaccurate and will require human review.

**Current status:** working menu and CSV prototypes; optional translation connector code with mocked provider tests. No live API test, document assistant, automated sales connector, forecasting system or completed pilot is claimed. Claude report explanations and inventory assistance remain planned. No Anthropic partnership is claimed.

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

Anyone who possesses a menu's edit key can update or delete it. Download the recovery file and keep it private. Losing every copy of the key means losing the ability to edit through the app. Public menus and their images can be viewed by anyone with their URL. Remote images connect to the image host. Browser drafts and edit keys are stored locally; published menu content is stored in SQLite on the server. There is no background telemetry. The menu builder and CSV workspace make no AI calls. Only the optional admin translation route sends selected name/description text to Anthropic after authentication and consent.

## Limits and operations

Maximum 30 items per menu, 7 MB of stored JSON per menu, 500 published menus per instance and five new menus per socket IP per hour. Behind a reverse proxy, visitors may share this rate limit. This is a prototype, not a hardened multi-tenant hosting service. Add proxy rate limits, storage monitoring, abuse reporting and operator moderation before broad public hosting. Rate limits reset on restart. Uploaded images embedded as data URLs can exhaust browser storage; export a copy when a save warning appears.

Back up the data volume using SQLite's backup API or stop the container before copying its database. Keep backup files private. Test restoring on a separate instance before relying on backups.

## License

Code is licensed under Apache-2.0. The TRAVI name does not imply endorsement of forks. This source bundle contains no café photos, company credentials, private menu data or VPS configuration. External image rights remain with their owners.

## Validation

Run `python -m unittest discover -s tests`. JavaScript syntax can be checked with `node --check site/menu-demo.js` and `node --check site/builder.js`. Browser interaction, PDF output and QR scanning still require manual validation on your target devices.


## Sales CSV workspace

Open /sales.html with the root server or optional admin image. Import a UTF-8 CSV up to 1 MB with headers date,item,quantity,unit_price and up to 5,000 data records. Dates use YYYY-MM-DD, quantities are positive integers and prices use a decimal point without thousands separators. Comma, semicolon and tab delimiters are supported. Invalid rows block the report rather than silently disappearing.

Calculations use integer hundredths of the selected currency: revenue = quantity × unit_price. The workspace reports quantities, item revenue rankings and daily totals. Records are not orders. Refunds, discounts, taxes, costs, profitability and missing dates are not separately modeled. Currency selection labels the supplied figures; it never converts currencies. Sample data is fictional, not evidence of TRAVI revenue or customer usage.

Files stay in page memory, with no upload, local draft persistence or AI call. JSON exports remain on your device. The planned role of Claude is to explain owner-selected computed summaries, identify missing context and suggest reviewable questions; this report explanation feature is not implemented.

Run node tests/test-sales.js to verify CSV parsing, totals, decimal precision, dates and rejection of malformed or oversized inputs.

## Product roadmap and evaluation

1. Evaluate the optional translation connector with a real account and bilingual reviewers.
2. Develop report explanations grounded in deterministic CSV calculations.
3. Pilot with an owner at a café and document actual findings.
4. Explore inventory and preparation estimates only after validating data and needs.

The live project has not started Claude API testing because it currently lacks an API testing budget. No measured waste reduction, global adoption or completed AI deployment is claimed.
