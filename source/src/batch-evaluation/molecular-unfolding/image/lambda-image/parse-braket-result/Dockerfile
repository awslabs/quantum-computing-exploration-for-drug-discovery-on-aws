FROM amazon/aws-lambda-python:3.8

COPY requirements.txt .

RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
COPY utility utility
COPY lambda/ParseBraketResultLambda/app.py  ${LAMBDA_TASK_ROOT}

CMD [ "app.handler" ]
