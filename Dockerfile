FROM python:3.12-alpine

RUN apk update && \
        apk add --no-cache \
        ffmpeg \
        opus-dev \
        libffi-dev \
        python3-dev \
        build-base

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Timer.py .
COPY GoogleCloudTTSProvider.py .
COPY TTSBot.py .

CMD [ "python", "TTSBot.py" ]