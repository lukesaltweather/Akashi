FROM python:3.11

WORKDIR /app
ADD . .
RUN ["pip", "install", "-r", "requirements.txt"]
WORKDIR /app/src
CMD [ "python", "main.py" ]
