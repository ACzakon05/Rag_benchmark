FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv

# Outside /app so the compose bind mount of ./backend doesn't hide the venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev


FROM python:3.13-slim

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

EXPOSE 8000
CMD ["scripts/start/app.sh"]
