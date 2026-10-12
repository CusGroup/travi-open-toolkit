FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY published.py ./
COPY admin/server.py ./
COPY claude_menu.py ./
COPY admin/site ./site
COPY site/menu-demo.js site/builder.js site/labs.css ./site/
COPY site/sales* ./site/
RUN useradd -u 10001 -m toolkit && mkdir /data && chown toolkit /data
USER toolkit
EXPOSE 8080
CMD ["python","server.py"]

