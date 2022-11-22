FROM amazon/aws-lambda-python:3.8

COPY requirements.txt .

RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
COPY utility utility
COPY image/lambda-image/parse-braket-result/app.py  ${LAMBDA_TASK_ROOT}

CMD [ "app.handler" ]
