FROM ghcr.io/astral-sh/uv:python3.14-trixie

WORKDIR /app
ADD . .
WORKDIR /app/src
CMD [ "uv", "run", "python", "main.py" ]
