FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# In dev mode, source code is mounted as a volume
# No need to COPY application code — it's bind-mounted

EXPOSE 8080

# Use --reload for hot reload during development
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --reload --reload-dir /app/wealth_pilot"]
