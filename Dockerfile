
# Select base image - Python 3.12
FROM python:3.12-slim@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63

# Set working directory to app
WORKDIR /app

# Copy requirements into working directory
COPY requirements.txt .

# Install psycopg2 and required libs before installing the requirements
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2 \
    && apt-get install build-essential -y


# Install dependencies from .txt file
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application code to container's working directory
COPY . .

# Expose the port where the app would run on
EXPOSE 8080

# Run FastAPI using uvicorn web server (src/main.py => app = FastAPI())
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
