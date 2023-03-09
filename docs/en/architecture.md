Deploying the Quantum Computing Exploration for Drug Discovery on AWS solution with the default parameters builds the following environment in the AWS Cloud.

![architecture](./images/architecture.png)

Figure 1: Quantum Computing Exploration for Drug Discovery on AWS architecture

1. This solution deploy an [Amazon SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html) instance, which allows **notebook experimentation** for drug discovery.

2. The notebook comes with prepared use cases for different problems in drug discovery, such as molecular unfolding.

3. This program uses [Amazon Braket][braket] Hybrid Job for experiments.

4. When you use it for the first time, you need to package the dependency packages required for the experiment to image and upload the image to [Amazon ECR][ecr]. The solution provides scripts for mirror packaging and uploading ECR.

5. Run multiple Hybrid Jobs in one experiment, and trigger the events in [Amazon EventBridge][eventbridge] when the Hybrid Job is completed.

6. EventBridge sends a notification to [Amazon SNS][sns], and all subscribers who have subscribed to this topic will receive this notification. This step is optional, and you can specify emails for subscription notifications when deploying the solution.

7. Experiment results will be stored in Amazon S3.

8. You can return to SageMaker Notebook to run the code to analyze and display the experimental results. In the default result analysis code, a comparison of the results of classical calculation and quantum calculation is provided.

[sagemaker]: https://aws.amazon.com/sagemaker/
[braket]: https://aws.amazon.com/braket/
[ecr]: https://aws.amazon.com/ecr/
[s3]: https://aws.amazon.com/s3/
[eventbridge]: https://aws.amazon.com/eventbridge/
[sns]: https://aws.amazon.com/sns/
