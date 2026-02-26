FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m venv /app/myproject \
    && /app/myproject/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PATH="/app/myproject/bin:$PATH"

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
