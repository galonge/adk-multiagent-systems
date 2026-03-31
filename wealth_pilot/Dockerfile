FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code into the image
COPY . .

EXPOSE 8080


CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} "]
