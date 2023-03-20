使用默认参数部署解决方案后，在 AWS 中构建的环境如下图所示。

![architecture](./images/architecture.png)

图 1：量子计算探索之药物发现方案架构图

1. 本方案部署一个笔记本实例，从而允许[Amazon SageMaker Notebook](https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html)用户进行**笔记本实验**。

2. 笔记本附带针对不同药物发现问题的用例，如分子展开、RNA 折叠、蛋白质折叠等。

3. 笔记本实例支持连接外网，方便您下载安装实验用的各种环境。

4. 本方案利用[Amazon Braket][braket] Hybrid Job 进行实验。

5. 在第一次使用时，需要您将实验所需要的依赖包打镜像并上传至[Amazon ECR][ecr]中，方案中提供了镜像打包以及上传 ECR 的脚本。

6. 一次实验运行多个 Hybrid Job，在 Hybrid Job 完成触发[Amazon EventBridge][eventbridge]中的事件。

7. EventBridge 向[Amazon SNS][sns]发送一个通知，所有订阅了该主题的订阅者会收到此通知。此步骤为可选项，您可以在部署方案时指定订阅通知的邮件。

8. 实验结果将存在 Amazon S3 中。

9. 您可以回到 SageMaker Notebook 中运行代码，来对实验结果进行分析及展示。默认的结果分析代码中，提供了经典计算和量子计算的结果对比。

[sagemaker]: https://aws.amazon.com/sagemaker/
[braket]: https://aws.amazon.com/braket/
[ecr]: https://aws.amazon.com/ecr/
[s3]: https://aws.amazon.com/s3/
[eventbridge]: https://aws.amazon.com/eventbridge/
[sns]: https://aws.amazon.com/sns/
