To automate deployment, this solution uses the following AWS CloudFormation templates, which you can download before deployment:

 [xxx.template](to be added): Use this template to launch the solution and all associated components. 
 The default configuration deploys 
[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html),
[Amazon Braket](https://aws.amazon.com/braket/),
[AWS Step Function](https://aws.amazon.com/step-functions/),
[AWS Batch](https://aws.amazon.com/batch/),
[Amazon EventBridge](https://aws.amazon.com/eventbridge/),
[Amazon API Gateway][api-gateway], 
[AWS Lambda](https://aws.amazon.com/lambda/),
[Amazon Athena](https://aws.amazon.com/athena/) and 
[Amazon QuickSight](https://aws.amazon.com/quicksight/),
but you can customize the template to meet your specific needs.