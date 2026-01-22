FROM ghcr.io/astral-sh/uv:python3.11-trixie

WORKDIR /app
ADD . .
WORKDIR /app/src
CMD [ "uv", "run", "python", "main.py" ]
