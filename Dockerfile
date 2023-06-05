FROM python:3.10-alpine
LABEL authors="archdrdr"

RUN apk update --no-cache && \
    apk add --no-cache gcc musl-dev libsndfile-dev python3-dev

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN python init.py

CMD ["python", "main.py"]
