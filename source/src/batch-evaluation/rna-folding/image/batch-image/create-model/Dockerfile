FROM python:3.8-slim-buster

WORKDIR /usr/src/app

COPY rna-data rna-data
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY utility utility

COPY image/batch-image/create-model/process.py .

ENTRYPOINT [ "python", "./process.py" ]
