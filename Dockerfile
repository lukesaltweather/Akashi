FROM python:3.10

WORKDIR /app
ADD . .
RUN ["pip", "install", "-r", "requirements.txt"]
WORKDIR /app/src
CMD [ "python", "main.py" ]
