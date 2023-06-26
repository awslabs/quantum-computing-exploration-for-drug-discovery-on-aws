您需要承担运行量子计算探索之药物发现方案时使用亚马逊云科技各个服务的成本费用。实际成本取决于具体执行的任务和复杂性。截至本次发布日期，影响解决方案的成本因素主要包括以下类型：

- 笔记本
- 存储
- ECR
- 任务调度

如果客户仅使用笔记本探算法，成本因素主要涉及笔记本和 Amazon Braket 任务的计算。 如果客户评估不同参数的不同用例，成本因素主要涉及来自 Amazon Braket Hybrid Jobs 的计算。

<table border='1' style="text-align: center">
    <tr>
        <td><B>服务</td>
        <td><B>资源</td>
        <td><B>运行状态</td>
        <td><B>费用</td>
    <tr>
    <tr>
        <td>Amazon Sagemaker Notebook</td>
        <td>ml.c5.xlarge</td>
        <td>长时间运行</td>
        <td>每天4.90美元</td>
    <tr>
    <tr>
        <td>Amazon S3</td>
        <td>-</td>
        <td>小于1G</td>
        <td>0.02美元</td>
    <tr>
    <tr>
        <td>Amazon Elastic Container Registry</td>
        <td>用户实例镜像</td>
        <td>< 1G</td>
        <td>$0.02</td>
    <tr>
    <tr>
        <td rowspan="4">Amazon Braket Hybrid Jobs</td>
        <td>ml.m5.large runs 以及 ml.m5.4xlarge (Molecular unfolding)</td>
        <td>一个完整的实验包含 12 个不同参数的作业，ml.m5.large 运行 44 分钟，ml.m5.4xlarge 总共运行 44 分钟</td>
        <td>$0.76 每个完整实验</td>
    <tr>
    <tr>
        <td>ml.m5.large 以及 ml.m5.4xlarge (RNA unfolding)</td>
        <td>一个完整的实验包含 2 个不同参数的作业，ml.m5.large 运行 450 分钟，ml.m5.4xlarge 总共运行 429 分钟</td>
        <td>$7.46 每个完整实验 </td>
    <tr>
    <tr>
        <td colspan='3'>总成本</td>
        <td>$13.16 每天</td>
    <tr>
</table>
