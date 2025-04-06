# Python
FROM python:3.10-slim

# environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# work directory inside the container
WORKDIR /app

# system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.4.0
ENV PATH="/root/.local/bin:$PATH"

# pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* /app/

# Poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy the rest of the code
COPY . /app/

# port FastAPI
EXPOSE 8000

# Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
