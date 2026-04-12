FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# create non-root user per ADK deployment best practice
RUN adduser --disabled-password --gecos "" adkuser

# copy all agent code — .dockerignore excludes .env, .adk/, .venv, etc.
# ADK expects agents as subdirectories of WORKDIR, so wealth_pilot/ → /app/wealth_pilot/
COPY . .

# chown AFTER COPY so adkuser owns all files and directories created by COPY.
# pre-create .adk/ so the docker named volume initializes with adkuser ownership,
# allowing ADK to write session and artifact data at runtime.
RUN mkdir -p /app/wealth_pilot/.adk && \
    chown -R adkuser:adkuser /app

USER adkuser

ENV PATH="/home/adkuser/.local/bin:$PATH"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
