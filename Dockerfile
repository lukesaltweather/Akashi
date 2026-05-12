FROM ghcr.io/astral-sh/uv:python3.13-trixie

WORKDIR /app
ADD . .
CMD [ "uv", "venv" ]
WORKDIR /app/src
CMD [ "uv", "run", "python", "main.py" ]
