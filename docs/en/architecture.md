Deploying this solution with the default parameters builds the following environment in the AWS Cloud.

![architecture](./images/architecture.png)
*Figure 1: The quantum ready solution for drug discovery architecture on AWS*

This solution deploys the Amazon CloudFormation template in your AWS Cloud account and completes the following settings.

The AWS CloudFormation template deploys the following workflows and service:

- 1.Notebook Experiment 
    - 1.1 The user deploys the solution solution into their AWS account and 
    open the deployed [AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html). The user can run and study sample 
    codes for drug discovery, following the step-by-step guide in **ZAY workshop md**
    - 1.2 When the user want to modify the default algorithms and update the 
    images of [Amazon ECR](https://aws.amazon.com/ecr/) for the 
    following batch test, they can find the step-by-step guide in **ZAY deployment md**
- 2.Batch Test
    - 2.1 The user can open the deployed [AWS Step Function](https://aws.amazon.com/step-functions/) for batch test the same problem 
    in drug discovery using classical computers and quantum computers. 
    - 2.2 The AWS Step Function launches various classical computing tasks through [AWS Batch](https://aws.amazon.com/batch/) jobs based on different resources 
    ().
    - 2.3 AWS Batch save results to [Amazon S3](https://aws.amazon.com/s3/).
    - 2.4 At the same time as 2.2, AWS Step Function parallely launches various quantum computing tasks based on different quantum computing devices.
    - 2.5 Each batch job asynchronously submits the quantum computing jobs/tasks 
    through [Amazon Braket](https://aws.amazon.com/braket/)
    - 2.6 When quantum computing jobs/tasks complete, the results are saved to 
    Amazon S3. 
    - 2.7 [Amazon EventBridge](https://aws.amazon.com/eventbridge/) triggers 
    the lisener [AWS Lambda](https://aws.amazon.com/lambda/)
    - 2.8 The lisener lambda sends a callback token to the step function
    - 2.9 When all the steps complete, a SNS notification is send out by 
    [Amazon SNS](https://aws.amazon.com/sns/).
    - 2.10 The Athena table is created by [Amazon Athena](https://aws.amazon.com/athena/)
     based on metrics data in Amazon S3.
    - 2.11 The user can view the batch test results(e.g. cost, performance and time) 
    through [Amazon QuickSight](https://aws.amazon.com/quicksight/)