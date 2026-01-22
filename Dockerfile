FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /app
ADD . .
WORKDIR /app/src
CMD [ "uv", "run", "python", "main.py" ]
