FROM python:3.8-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD [ "python", "./batch-experiment.py" ]
ENTRYPOINT [ "python", "./batch-experiment.py" ]
