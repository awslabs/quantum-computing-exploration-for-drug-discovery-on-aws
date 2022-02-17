FROM python:3.8-slim-buster

WORKDIR /usr/src/app

COPY molecule-data molecule-data
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY utility utility

COPY batch-images/create-model/process.py .

ENTRYPOINT [ "python", "./process.py" ]
