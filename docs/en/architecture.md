Deploying the Quantum Computing Exploration for Drug Discovery on AWS solution with the default parameters builds the following environment in the AWS Cloud.

![architecture](./images/architecture.png)

Figure 1: Quantum Computing Exploration for Drug Discovery on AWS architecture

1. This solution deploys a notebook instance to allow [Amazon SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html) users to conduct **notebook experiments**. Notebooks come with use cases for different drug discovery problems such as molecule unfolding, RNA folding, protein folding, etc.

2. When used for the first time, the system will mirror and upload the dependent packages required for the experiment to [Amazon ECR][ecr].

3. This program uses [Amazon Braket][braket] Hybrid Job for experiments.

4. The experiment results are stored in Amazon S3.

5. Run multiple Hybrid Jobs in one experiment, and initiate the events in [Amazon EventBridge][eventbridge] when the Hybrid Job is completed.

6. Events initiated by Amazon EventBridge will be sent to Lambda for analysis and summary.

7. Lambda sends a analysis report to [Amazon SNS][sns], and all subscribers who have subscribed to this topic will receive this report by email. This step is optional, and you can specify emails for subscription notifications when deploying the solution.

8. Return to SageMaker Notebook to run the code to analyze and display the experiment results.

[sagemaker]: https://aws.amazon.com/sagemaker/
[braket]: https://aws.amazon.com/braket/
[ecr]: https://aws.amazon.com/ecr/
[s3]: https://aws.amazon.com/s3/
[eventbridge]: https://aws.amazon.com/eventbridge/
[sns]: https://aws.amazon.com/sns/
