使用默认参数部署解决方案后，在AWS中构建的环境如下图所示。

![architecture](./images/architecture.png)

图1：量子计算探索之药物发现方案架构图


本方案在您的AWS账户中部署AWS CloudFormation模板，并实现三大模块的功能：

- 笔记本实验
- 批量评估
- 可视化

!!! Notice "说明" 

    - 本方案所有计算资源（AWS Batch计算环境和AWS Lambda）都放在[Amazon VPC][vpc]私有子网中，从而保证安全访问。

    - 本方案为Amazon ECR、Amazon S3、Amazon Athena和Amazon Braket创建了[VPC Endpoints][vpc-endpoints]。


1. 本方案部署一个笔记本实例，从而允许[Amazon SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)用户进行**笔记本实验**。

2. 笔记本附带针对不同药物发现问题的用例，如分子展开等。

3. 在公共[子网][subnet]中创建了[NAT网关][nat]，并通过[Internet网关][internet-gateway]连接互联网。笔记本实例部署在私有子网中，它通过NAT网关访问互联网。

4. 本方案使用[AWS Step Functions][step-functions]工作流进行**批量评估**。

5. 根据不同的模型参数、资源、计算方式（经典或者量子计算），AWS Step Functions工作流会并行发起多种[AWS Batch][batch]任务。

6. 每个AWS Batch任务使用预先构建好的容器镜像，根据不同的模型参数，评估药物发现中的问题。

7. 所有预先构建好的镜像都存储在[Amazon ECR][ecr]中。

8. 对于经典计算，AWS Batch任务会在本地评估药物发现中的问题，然后把结果存放到[Amazon S3][s3]。

9. 对于量子计算，AWS Batch会以异步的方式把任务提交到Amazon Braket。

10. 当一个Amazon Braket任务结束后，它会把输出存放在S3桶里的一个文件，并触发一个[Amazon EventBridge][eventbridge]事件。

11. [AWS Lambda][lambda]由Amazon EventBridge事件触发，它会解析Braket任务/作业存储在S3上的输出文件，并把解析后的结果放到S3，并向AWS Step Functions工作流发送一个回调。

12. 当批量评估完成后，AWS Step Functions工作流会向[Amazon SNS][sns]发送一个通知，所有订阅了该主题的订阅者会收到此通知。


13. 在AWS Step Functions工作流执行过程中，会创建一个[Amazon Athena][athena]表用于可视化。

14. 您可以通过[Amazon QuickSight][quicksight]来查看**批量评估**的结果。默认情况下，方案提供不同资源的运行时间做为指标。



[nat]: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
[subnet]: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
[internet-gateway]: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html
[vpc]: https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html
[athena]: https://docs.aws.amazon.com/athena/latest/ug/what-is.html
[lambda]: https://aws.amazon.com/lambda
[sns]: https://aws.amazon.com/sns/
[s3]: https://aws.amazon.com/s3/
[batch]: https://aws.amazon.com/batch/
[eventbridge]: https://aws.amazon.com/eventbridge/
[quicksight]: https://aws.amazon.com/quicksight/
[ecr]: https://aws.amazon.com/ecr/
[braket]: https://aws.amazon.com/braket/
[step-functions]: https://aws.amazon.com/step-functions/
[vpc-endpoints]: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html
[subscribe-topic]: ./deployment.md