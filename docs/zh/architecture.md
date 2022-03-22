使用默认参数部署解决方案后，在亚马逊云科技中构建的环境如下图所示。

![architecture](./images/architecture.png)

图1：药物发现量子计算解决方案架构图


本解决方案在您的亚马逊云科技账户中部署AWS CloudFormation模板，并提供三个功能模块：
 
  - **笔记本实验**
  - **批量评估**
  - **可视化**

**笔记本实验**

1. 本方案部署一个笔记本实例，从而允许[Amazon SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)用户进行**笔记本实验**（1）。

2. 笔记本附带针对不同药物发现问题的示例代码，如分子展开等。用户可以学习如何利用经典计算或通过访问[Amazon Braket][braket]利用量子计算研究这些问题（2）。详情请参考[动手实验](workshop/background.md)。

3. 在公共[子网][subnet]中创建了[NAT网关][nat]，并通过[Internet网关][internet-gateway]连接互联网。笔记本实例部署在私有子网中，它通过NAT网关访问互联网（3）。

**批量评估**

1. 本方案使用[AWS Step Functions][step-functions]工作流进行**批量评估**（4）。

2. 根据不同的模型参数、资源、计算方式（经典或者量子计算），AWS Step Functions工作流会并行发起多种[AWS Batch][batch]任务（5）。

3. 每个AWS Batch任务使用预先构建好的存储在[Amazon ECR][ecr]（7）中容器镜像，根据不同的模型参数，评估药物发现中的问题（6）。

4. 对于经典计算，AWS Batch任务会在本地评估药物发现中的问题，然后把结果存放到[Amazon S3][s3]（10）。

5. 对于量子计算，AWS Batch会以异步的方式把任务提交到Amazon Braket，把它变成Amazon Braket任务（9）。

6. AWS Step Functions工作流停在当前步骤，等待所有任务结束。

7. 当一个Amazon Braket任务结束后，它会把输出存放在S3桶里，并触发一个[Amazon EventBridge][eventbridge]事件（11）。

8. [AWS Lambda][lambda]由Amazon EventBridge事件触发，它会解析Braket任务存储在S3上的输出文件，并把解析后的结果放到S3，并向AWS Step Functions工作流发送一个回调。

9. 当所有子任务结束，AWS Step Functions工作流结束等待，前进到下一步（12）。

10. 当批量评估完成后，AWS Step Functions工作流会向[Amazon SNS][sns]发送一个通知，所有订阅了该主题的[订阅者][subscribe-topic]会收到此通知（13）。

**可视化**

1. 在AWS Step Functions工作流执行过程中，会创建一个[Amazon Athena][athena]表用于可视化（14）。

2. 您可以通过[Amazon QuickSight][quicksight]来查看**批量评估**的结果（15）。

备注： 

- 本方案所有计算资源（AWS Batch计算环境和AWS Lambda）都放在[Amazon VPC][vpc]私有子网中。

- 本方案为Amazon ECR、Amazon S3、Amazon Athena和Amazon Braket创建了[VPC Endpoints][vpc-endpoints](8)。

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