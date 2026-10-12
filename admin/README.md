# Café administration module

Optional standalone admin server. The root menu builder remains unchanged. This module includes Vietnamese admin login, product CRUD, categories, VND prices, availability, visibility, sorting, image uploads, website content and appearance settings. A minimal storefront demonstrates the saved content; it is not the full travi.vn design. No café photos or production data are included.

## Docker quick start (from repository root)

```bash
cp admin/.env.example admin/.env
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Put the generated password into admin/.env before running.
docker build -f admin/Dockerfile -t travi-toolkit-admin .
docker run -d --name travi-admin -p 127.0.0.1:8080:8080 --env-file admin/.env -v travi_admin_data:/data travi-toolkit-admin
```

Visit http://localhost:8080/admin and log in with your configured credentials. The database starts empty; add your own products. Preview the storefront at /. Image uploads support JPG, PNG and WebP up to 5 MB. Website settings support uploaded images and colors. Admin products use VND integer prices; zero or blank displays Contact. This admin editor is currently Vietnamese and does not have bilingual product fields. An optional administrator-only translation workflow is available separately at /translate.html. It is not integrated into the product editor.

For HTTPS hosting, set COOKIE_SECURE=1 and PUBLIC_BASE_URL to the public HTTPS URL, put a reverse proxy in front and restrict admin access where practical. COOKIE_SECURE=0 is only for local HTTP testing. Never commit .env files. Changing the password requires restarting the process; existing sessions disappear on restart. One administrator account is configured by environment; there are no roles, password reset or multi-store isolation.

## Local run

```bash
python -m pip install -r requirements.txt
# Export ADMIN_USER, ADMIN_PASSWORD, COOKIE_SECURE and PUBLIC_BASE_URL first.
DATA_DIR=./data PYTHONPATH=. python admin/server.py
```

## API

Public: GET /api/menu, GET /api/settings. Admin: POST /api/admin/login, GET /api/admin/session, GET /api/admin/products, POST /api/admin/save, POST /api/admin/delete, POST /api/admin/upload, GET/POST /api/admin/settings, POST /api/admin/logout. Authenticated writes require the session cookie and X-CSRF-Token returned by login. See server.py for request fields.

Back up the SQLite database with the SQLite backup API and copy uploads; restore both together. Sessions and login throttles are in memory. Login throttling uses the socket IP, so visitors may share limits behind a reverse proxy. Image magic-byte validation is basic; add image decoding, malware scanning and operational monitoring before large public use. This is an early single-store prototype, not an audited production CMS.


## Optional Claude translation pilot

The connector is implemented, disabled by default and not tested against a live Claude account. In your private environment, set TRAVI_AI_ENABLED=1, ANTHROPIC_API_KEY and ANTHROPIC_MODEL to an exact model ID available to your account. Never commit credentials. The admin Docker image includes claude_menu.py and /translate.html. Log in at /admin, then open /translate.html, select menu text, consent to sending it to Anthropic, review the English draft and approve it into your browser draft. Publication remains a separate action. It does not automatically update products in the admin database.

Translation uses only the selected item name and description. Prices, images and customer data are not sent. No AI account is needed for the normal menu builder or /sales.html CSV calculations. The pilot limit is 3 attempts per minute, 20 per UTC day and 2 concurrent requests; failed requests count. Timestamp-only usage records are stored in /data/ai-usage.sqlite. Do not treat AI text as verification of allergens, ingredients, nutrition or organic status.

Validation: python3 -m unittest discover -s tests (from repository root). Live provider and browser tests remain outstanding.


Project coordination: TRAVI GROUP VIETNAM JOINT STOCK COMPANY via hotro@travi.vn. Source is managed through the Travivn technical GitHub account. This module remains a prototype; no paying customer or completed live Claude pilot is claimed.
