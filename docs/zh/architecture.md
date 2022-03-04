使用默认参数部署药物研发量子计算解决方案后，在亚马逊云科技中构建的环境如下图所示。

图1 是AWS药物研发量子计算决方案架构图，本架构用于赋能用户，在药物研发领域，使用AWS云进行量子计算。
<center>

![architecture](./images/architecture.png)

图1：药物研发量子计算解决方案架构图

</center>

<<<<<<< HEAD
此解决方案将使用 Amazon CloudFormation 模板部署在您的AWS云帐户部署资源，将提供三部分：
 
  - **笔记本实验**
  - **批量评估**
  - **可视化**

**笔记本实验**

1. 该解决方案部署了一个实例用于 
[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)
用户可以在上面进行**笔记本实验**, 用经典计算和量子计算进行药物发现问题研究(1)。
=======
本解决方案在您的亚马逊云科技账户中部署Amazon CloudFormation模板，并提供三个URL。其中一个用于**可视化**，另外两个用于提供两种研究药物发现问题的方法：**笔记本实验**和**批量评估**。

01. 部署一个实例用于[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)。用户可以进行**笔记本实验**，利用经典计算和量子计算研究药物发现问题。

02. 笔记本附带针对不同药物发现问题的示例代码，如分子展开、分子模拟等。用户可以学习如何利用经典计算或通过访问[Amazon Braket](https://aws.amazon.com/braket/)利用量子计算研究这些问题。详情请参考[动手实验](workshop/background.md)。
>>>>>>> f8708da (docs on-going)

2. 笔记本附带针对不同药物研发问题的示例代码，如分子展开、分子模拟等。用户可以学习如何利用经典计算或通过访问
[Amazon Braket][braket]利用量子计算研究这些问题。
请参考[动手实验](workshop/background.md)中的指南。

<<<<<<< HEAD
3. 本方案在公共[子网][subnet]中创建了[NAT网关][nat]，并通过[因特网网关][internet-gateway]连接互联网。
笔记本实例部署在私有子网中，它能通过NAT网关访问互联网(3)。

**批量评估**

1. 本方案使用[AWS Step Functions][step-functions]工作流进行**批量评估**(4)。

2. 根据不同的模型参数、资源、计算方式（经典或者量子计算），AWS Step Functions工作流会并行发起多种[AWS Batch][batch]任务(5)。

3. 每个AWS Batch任务使用预先构建好的存储在[Amazon ECR][ecr](7)中容器镜像，根据不同的模型参数，用来评估药物发现中的问题(6)。
=======
04. 部署[AWS Step Functions](https://aws.amazon.com/step-functions/)用于**批量评估**。

05. AWS Step Functions通过[AWS Batch](https://aws.amazon.com/batch/)工作启动基于不同计算资源的各个计算任务。

06. AWS Batch启动的实例会尝试在经典计算资源或者量子计算资源上评估一个特定的药物研发问题。例如，比较模拟退火和量子退火在解决分子展开问题时的差异。

07. **批量评估**的镜像已经内置在[Amazon ECR](https://aws.amazon.com/ecr/)。如果需要定制**批量评估**的逻辑, 请参考[批量评估您自己的模型](workshop/a-molecular-unfolding/evaluate-your-own-model.md)。

08. **批量评估**部署了 [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)能够实现VPC与相应AWS服务（Amazon ECR, Amazon S3, Amazon Braket）的连接。
>>>>>>> f8708da (docs on-going)

4. 对于经典计算，AWS Batch任务会在本地评价药物发现中的问题，然后把结果存放到[Amazon S3][s3](10)。

<<<<<<< HEAD
5. 对于量子计算，AWS Batch会以异步的方式把任务提交到Amazon Braket，把它变成Amazon Braket任务(9)。

6. AWS Step Functions工作流停在当前步骤，等待所有任务结束。
=======
10. 经典计算或者量子计算的结果都会被存储到[Amazon S3](https://aws.amazon.com/s3/)。

11. 当量子计算工作/任务结束，[Amazon EventBridge](https://aws.amazon.com/eventbridge/)会触发监听者[AWS Lambda](https://aws.amazon.com/lambda/)。
>>>>>>> f8708da (docs on-going)

7. 当一个Amazon Braket任务结束后，它会把输出存放在S3桶里，并触发一个[Amazon EventBridge][eventbridge]事件(11)。

<<<<<<< HEAD
8. [AWS Lambda][lambda]被Amazon EventBridge事件触发，它会解析Braket任务存储在S3上的输出文件，并把解析后的结果放到S3，并向AWS Step Functions工作流发送一个回调。

9. 当所有子任务结束，AWS Step Functions工作流结束等待，前进到下一步(12)。

10. 当批量评估完成后，AWS Step Functions工作流会向[Amazon SNS][sns]发送一个通知，所有订阅了该主题的[订阅者][subscribe-topic]会收到此通知(13)。
=======
13. 当所有操作完成时，[Amazon SNS](https://aws.amazon.com/sns/) 会发出一个通知。

14. [Amazon Athena](https://aws.amazon.com/athena)根据存储在Amazon S3里面的指标数据建立Glue table。

15.  用户可以通过[Amazon QuickSight](https://aws.amazon.com/quicksight/)查看**批量评估**的结果。
>>>>>>> f8708da (docs on-going)

**可视化**

1. 在AWS Step Functions工作流执行过程中，会创建一个[Amazon Athena][athena]表用于可视化。

2. 用户可以通过[Amazon QuickSight][quicksight]来查看**批量评估**的性能结果。

备注: 

- 本方案所有计算资源（AWS Batch计算环境，AWS Lambda）都放在[Amazon VPC][vpc]私有子网中。

- 本方案为Amazon ECR, Amazon S3, Amazon Athena and Amazon Braket创建了[VPC Endpoints][vpc-endpoints]。

[nat]: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
[subnet]: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Subnets.html
[internet-gateway]: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html
[vpc]: https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html
[athena]: https://docs.aws.amazon.com/athena/latest/ug/what-is.html
[gule]: https://aws.amazon.com/glue/getting-started/
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
