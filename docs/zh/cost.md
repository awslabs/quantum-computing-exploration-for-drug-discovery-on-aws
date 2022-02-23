您需要承担运行此解决方案时使用亚马逊云科技服务的费用。截至2022年3月，运行此解决方案，
成本约为每小时¥158.98。

整个话费包含5种类型：

* 笔记本
* 计算
* 存储
* 分析
* 任务调度

实际成本取决于执行的任务和复杂性。拿制备样品 (117_idel.mol2) 的分子展开应用为
一个例子。以下计算基于客户一直使用笔记本学习示例代码, 同时使用解决方案运行
一次完整的对量子计算和经典计算整的批量评估，以及在 Amazon QuickSight 中可视化结果。
如果客户仅使用解决方案来研究示例代码，成本为笔记本和来自 Amazon Braket 的计算。

!!! notice

    在部署此解决方案之前创建账单告警是一种很好的做法。参考这个 [链接](https://docs.aws.amazon.com/zh_cn/AmazonCloudWatch/latest/monitoring/monitor_estimated_charges_with_cloudwatch.html)

<table border='1' style="text-align: center">
    <tr>
        <td><B>类型</B></td>
        <td><B>服务</td>
        <td><B>资源大小</td>
        <td><B>运行状态</td>
        <td><B>花费</td>
    <tr>
    <tr>
        <td>笔记本</td>
        <td>Amazon Sagemaker Notebook</td>
        <td>ml.c5.xlarge</td>
        <td>长时间运行</td>
        <td>每小时¥31.0</td>
    <tr>
    <tr>
        <td rowspan="16">计算</td>
        <td>Amazon Braket</td>
        <td>D-Wave - DW_2000Q_6</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>¥55.64</td>
    <tr>
    <tr>
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system4.1</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>¥55.64</td>
    <tr>
    <tr>
        <td>Amazon Batch (Fargate) </td>
        <td>2 VCPU 4G MEM</td>
        <td>比如像构建模型的任务, 8分钟(小于20分钟)</td>
        <td>¥6.45</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>2 VCPU 2G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>¥0.57</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>4 VCPU 4G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>¥1.07</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>8 VCPU 8G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>¥2.15</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>16 VCPU 16G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>¥4.30</td>
    <tr>
    <tr>
        <td>AWS Lambda </td>
        <td>-</td>
        <td>小于100次调用</td>
        <td>¥0</td>
    <tr>
    <tr>
        <td>存储</td>
        <td>Amazon S3</td>
        <td>-</td>
        <td>小于1G</td>
        <td>¥0.13</td>
    <tr>
    <tr>
        <td rowspan='4'>分析</td>
        <td>Amazon Athena</td>
        <td>-</td>
        <td>小于20次调用, 100M数据</td>
        <td>¥0.18</td>
    <tr>
    <tr>
        <td>Amazon QuickSight</td>
        <td>1个读取器</td>
        <td>长时间运行</td>
        <td>每个月¥50.58</td>
    <tr>
    <tr>
        <td>任务调度</td>
        <td>AWS Step Functions</td>
        <td>-</td>
        <td>小于100运行</td>
        <td>¥0</td>
    <tr>
    <tr>
        <td colspan='4'>总花费</td>
        <td>每天¥158.82</td>
    <tr>
</table>