FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY . .

ENV PORT=8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "API_endpoints:app"]