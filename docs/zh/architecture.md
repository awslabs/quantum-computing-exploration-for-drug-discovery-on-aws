使用默认参数部署药物研发量子计算解决方案后，在亚马逊云科技中构建的环境如下图所示。

<center>

![architecture](./images/architecture.png)

图1：药物研发量子计算解决方案架构图

</center>

本解决方案在您的亚马逊云科技账户中部署Amazon CloudFormation模板，并提供三个URL。其中一个用于**可视化**，另外两个用于提供两种研究药物发现问题的方法：**笔记本实验**和**批量评估**。

01. 部署一个实例用于[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)。用户可以进行**笔记本实验**，利用经典计算和量子计算研究药物发现问题。

02. 笔记本附带针对不同药物发现问题的示例代码，如分子展开、分子模拟等。用户可以学习如何利用经典计算或通过访问[Amazon Braket](https://aws.amazon.com/braket/)利用量子计算研究这些问题。详情请参考[动手实验](workshop/background.md)。

03. 用户可以通过该笔记本访问公网。

04. 部署[AWS Step Functions](https://aws.amazon.com/step-functions/)用于**批量评估**。

05. AWS Step Functions通过[AWS Batch](https://aws.amazon.com/batch/)工作启动基于不同计算资源的各个计算任务。

06. AWS Batch启动的实例会尝试在经典计算资源或者量子计算资源上评估一个特定的药物研发问题。例如，比较模拟退火和量子退火在解决分子展开问题时的差异。

07. **批量评估**的镜像已经内置在[Amazon ECR](https://aws.amazon.com/ecr/)。如果需要定制**批量评估**的逻辑, 请参考[批量评估您自己的模型](workshop/a-molecular-unfolding/evaluate-your-own-model.md)。

08. **批量评估**部署了 [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)能够实现VPC与相应AWS服务（Amazon ECR, Amazon S3, Amazon Braket）的连接。

09. 通过Amazon Braket递交工作/任务来测试量子计算算法。

10. 经典计算或者量子计算的结果都会被存储到[Amazon S3](https://aws.amazon.com/s3/)。

11. 当量子计算工作/任务结束，[Amazon EventBridge](https://aws.amazon.com/eventbridge/)会触发监听者[AWS Lambda](https://aws.amazon.com/lambda/)。

12. 监听者Lambda函数会将一个回调发送给Step Functions。

13. 当所有操作完成时，[Amazon SNS](https://aws.amazon.com/sns/) 会发出一个通知。

14. [Amazon Athena](https://aws.amazon.com/athena)根据存储在Amazon S3里面的指标数据建立Glue table。

15.  用户可以通过[Amazon QuickSight](https://aws.amazon.com/quicksight/)查看**批量评估**的结果。

<!--[workshop-background]: workshop/background.md-->
<!--[evaluate-your-own-model]: workshop/a-molecular-unfolding/evaluate-your-own-model.md-->