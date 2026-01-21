# build image
FROM python:3.13-slim AS builder


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

RUN apt-get update && apt-get install -y curl

WORKDIR /app

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

COPY pyproject.toml uv.lock .

RUN uv pip install --system --locked

COPY . .

EXPOSE 8000

CMD ["gunicorn", "src.core.wsgi:application", "--bind", "0.0.0.0:8000"]



