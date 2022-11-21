#FROM public.ecr.aws/lambda/python:3.8
FROM amazon/aws-lambda-python:3.8

COPY image/lambda-image/device-available-check/requirements.txt .

RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY image/lambda-image/device-available-check/app.py  ${LAMBDA_TASK_ROOT}

CMD [ "app.handler" ]
