下图展示的是使用默认参数部署本解决方案在亚马逊云科技中构建的环境。

<center>
![architecture](./images/architecture.png)
      
图1：药物研发量子计算解决方架构图

</center>

此解决方案将 Amazon CloudFormation 模板部署在您的
AWS 云帐户并提供三个 URL。一个用于**可视化**。
其他的为用户提供了两种研究药物发现问题的方法
：**笔记本实验**和**批量评估**：

1. 该解决方案部署了一个实体用于 
[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html). 
用户可以在上面进行**笔记本实验**, 用经典计算和量子计算进行药物发现问题研究

2. 笔记本附带针对不同药物研发问题的示例代码，如分子展开、分子模拟等。
用户可以学习如何利用经典计算或通过访问
[Amazon Braket](https://aws.amazon.com/braket/)
利用量子计算研究这些问题。请参考[动手实验页面](workshop/background.md)
中的指南

3. 笔记本为用户提供公网访问。这可以用来下载实验必备软件。

4. 该解决方案部署了
[AWS Step Function](https://aws.amazon.com/step-functions/) 。这可以让
用户进行
**批量评估**. 

5. AWS Step Function 通过
    [AWS Batch](https://aws.amazon.com/batch/)工作启动了不同计算任务。
    这些任务基于不同的计算资源。

6. AWS Batch启动的实例会尝试在经典计算资源或者量子计算资源上
评估一个特定的药物研发问题. 例如，对于分子展开的问题，模拟退火和量子退火的差异
可以进行比较。

7. **批量评估**的镜像已经内置在[Amazon ECR](https://aws.amazon.com/ecr/). 
如果需要定制批量 **批量评估** 的逻辑, 请参考 
[批量评估您自己的模型页面](workshop/a-molecular-unfolding/evaluate-your-own-model.md).

8. **批量评估** 部署了 [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html) 与以下AWS服务的安全连接:
Amazon ECR, Amazon S3, Amazon Braket.

9. 测试量子算法的批量任务通过Amazon Braket递交工作/任务

10. 经典计算或者量子计算的结果都会被存储到
[Amazon S3](https://aws.amazon.com/s3/),

11. 当量子计算工作/任务结束，
[Amazon EventBridge](https://aws.amazon.com/eventbridge/) 会触发监听者[AWS Lambda](https://aws.amazon.com/lambda/).

12. 监听者lambda会讲一个回调发送给step function.

13. 当所有步骤完成时,
[Amazon SNS](https://aws.amazon.com/sns/) 会发出一个通知

14. [Amazon Athena](https://aws.amazon.com/athena) 
根据存储在
Amazon S3里面的指标数据建立Glue table

15.  
用户可以通过
[Amazon QuickSight](https://aws.amazon.com/quicksight/)
来查看**批量评估**的结果（e.g. 时间，性能）
