FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py published.py ./
COPY site ./site
RUN useradd -u 10001 -m toolkit && mkdir /data && chown toolkit /data
USER toolkit
EXPOSE 8080
CMD ["python","server.py"]
