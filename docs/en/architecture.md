Deploying this solution with the default parameters builds the following environment in the AWS Cloud.

![architecture](./images/architecture.png)
*Figure 1: The quantum ready solution for drug discovery architecture on AWS*

This solution deploys the Amazon CloudFormation template in your 
AWS Cloud account and provides three URLs. One for **Visualization**.
The others provide user with two approaches to study drug discovery 
problems: **Notebook Experiment** and **Batch Test**:

1. The solution deploys an instance for 
[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html). 
The user can do **Notebook Experiment** for drug discovery on classical computing and 
quantum computing in this notebook.

2. The notebook comes with prepared sample code for different problems 
in drug discovery, like molecule unfolding, molecule simulation and so on. 
The user can study sample code, following the step-by-step guide in workshop 
page.

3. The notebook provides the user with the public network access to download 
possible software as well as access to other 
AWS services:  [Amazon ECR](https://aws.amazon.com/ecr/), 
[Amazon S3](https://aws.amazon.com/s3/),
and [Amazon Braket](https://aws.amazon.com/braket/).

4. The solution also deploys 
[AWS Step Function](https://aws.amazon.com/step-functions/) for user to do 
**Batch Test**. 

5. The AWS Step Function launches various computing tasks through 
    [AWS Batch](https://aws.amazon.com/batch/) jobs based on different resources.

6. Instances launched by AWS Batch try to test a particular problem based 
on different computing resources , classical computing or quantum computing. 
For example, for the problem of molecule unfolding, the performance difference 
between quantum annealer and simulated annealer can be figured out. 

7. The images for **Batch Test** have been built in Amazon ECR. For customizing 
the logic for **Batch Test**, please refer to the instructions in workshop page.

8. The **Batch Test** deploys [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html) to ensure secure connection to AWS 
services: AWS Step Function, [Amazon SNS](https://aws.amazon.com/sns/), 
Amazon ECR, Amazon S3, Amazon Braket and 
[Amazon EventBridge](https://aws.amazon.com/eventbridge/).

9. The batch job for testing quantum algorithm submits the quantum computing 
jobs/tasks through Amazon Braket.

10. Either classical computing task or quantum computing jobs/tasks complete, 
the results will be saved to Amazon S3.

11. When quantum computing jobs/tasks complete, Amazon EventBridge triggers 
the lisener [AWS Lambda](https://aws.amazon.com/lambda/).

12. The lisener lambda sends a callback to the step function.

13. When all the steps complete, a SNS notification is send out by Amazon SNS.

14. The Athena table is created by Amazon Athena based on metrics data in 
Amazon S3.

15. The user can view the **Batch Test** results(e.g. cost, performance) 
through [Amazon QuickSight](https://aws.amazon.com/quicksight/)