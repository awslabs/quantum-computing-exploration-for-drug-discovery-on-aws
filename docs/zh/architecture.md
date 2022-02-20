下图展示的是使用默认参数部署本解决方案在亚马逊云科技中构建的环境。

![architecture](./images/arch.png)
      
图：方案架构

本解决方案在您的亚马逊云科技账户中部署Amazon CloudFormation模板并提供了三个URLs链接。其中一个用于**可视化**，另外两个链接向您提供了两种用于研究药物研究的方法:**Notebook experiment**和**Batch evaluation**.

1. 本解决方案部署了一个实例在 
[AWS SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html). 
您可以使用 **Notebook Experiment** 进行药物研发基于传统计算资源和量子计算资源.

2. Notebook中包含用于药物研发的不同方法，例如molecular unfolding，molecular simulation等方法。用户可以学习这些方法基于经典计算资源或量子计算资源[Amazon Braket](https://aws.amazon.com/braket/). 逐步教程提供在[Workshop Page](workshop/background.md).

3. Notebook向用户提供了公共网络的访问，用于下载实验必须的软件。

4. 本解决方案同样部署在
[AWS Step Function](https://aws.amazon.com/step-functions/) 以便用户使用
**Batch Evaluation**. 

5. AWS Step功能函数基于不同的资源通过[AWS Batch](https://aws.amazon.com/batch/)启动各种计算任务.

6. 运行在AWS Batch的实例尝试求解一个具体的问题基于不同的计算资源：经典计算资源和量子计算资源. 
例如,对于molecular unfolding问题,用户可以比较量子退火机和模拟退火机之间的性能区别. 

7. **Batch Evaluation**图片存储在[Amazon ECR](https://aws.amazon.com/ecr/). 若想要个性化定制 **Batch Evaluation**的逻辑顺序，请参考
[Batch Evaluate Your Own Model Page](workshop/a-molecular-unfolding/evaluate-your-own-model.md).

8. **Batch Evaluation**部署了[VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)用于确保连接AWS 
服务:Amazon ECR, Amazon S3, Amazon Braket的通信安全.

9. 批处理的量子测试算法可以通过Amazon Braket提交量子计算任务.

10. 当经典计算或量子计算任务完成时，结果会被保存在[Amazon S3](https://aws.amazon.com/s3/),

11. 当量子计算任务完成时, 
[Amazon EventBridge](https://aws.amazon.com/eventbridge/)会触发listener lambda[AWS Lambda](https://aws.amazon.com/lambda/).

12. listener lambda会向Step函数发送回调信号.

13. 当所用步骤执行完后，一个通知会被发送到
[Amazon SNS](https://aws.amazon.com/sns/).

14. Glue table通过Amazon Athena创建基于Amazon S3的矩阵数据.

15. 您可以查看 **Batch Evaluation**的结果(e.g. cost, performance)通过[Amazon QuickSight](https://aws.amazon.com/quicksight/)



