<<<<<<< HEAD
您需要承担运行药物研发量子计算解决方案时使用亚马逊云科技各个服务的成本费用。实际成本还取决于具体执行的任务和复杂度。截至2022年3月，影响解决方案的成本因素主要包括以下类型：
=======
您需要承担运行药物研发量子计算解决方案时使用亚马逊云科技各个服务的成本费用。实际成本取决于具体执行的任务和复杂性。截至2022年3月，影响解决方案的成本因素主要包括以下类型：
>>>>>>> 0bc099045fa074a877542bc2a7d310f07d309952

* 笔记本
* 计算
* 存储
* 分析
* 任务调度

## 示例

<<<<<<< HEAD
以分子展开应用为例，假设客户一直使用笔记本学习示例代码，当客户使用解决方案运行一次完整的对量子计算和经典计算的批量评估，以及在Amazon QuickSight中展示可视化结果时，成本费用如下表所示。
=======
以分子展开应用为例，假设客户一直使用笔记本学习示例代码, 当客户使用解决方案运行一次完整的对量子计算和经典计算的批量评估，以及在Amazon QuickSight中可视化结果时，成本费用如下表所示。
>>>>>>> 0bc099045fa074a877542bc2a7d310f07d309952

!!! 注意

    如果客户仅使用解决方案来研究示例代码，则成本主要包括笔记本和Amazon Braket的计算费用。


<table border='1' style="text-align: center">
    <tr>
        <td><B>类型</B></td>
        <td><B>服务</td>
        <td><B>资源大小</td>
        <td><B>运行状态</td>
        <td><B>费用</td>
    <tr>
    <tr>
        <td>笔记本</td>
        <td>Amazon Sagemaker Notebook</td>
        <td>ml.c5.xlarge</td>
        <td>长时间运行</td>
        <td>每天4.90美金</td>
    <tr>
    <tr>
        <td rowspan="16">计算</td>
        <td>Amazon Braket</td>
        <td>D-Wave - DW_2000Q_6</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>8.8美金</td>
    <tr>
    <tr>
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system4.1</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>8.8美金</td>
    <tr>
    <tr>
        <td>Amazon Batch (Fargate) </td>
        <td>2 VCPU 4G MEM</td>
        <td>比如像构建模型的任务, 8分钟(小于20分钟)</td>
        <td>1.02美金</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>2 VCPU 2G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>0.09美金</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>4 VCPU 4G MEM</td>
        <td>4个不同参数的任务, 19分钟(小于60分钟)</td>
        <td>0.17美金</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>8 VCPU 8G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>0.34美金</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>16 VCPU 16G MEM</td>
        <td>4个包含不同参数的任务, 19分钟(小于60分钟)</td>
        <td>0.68美金</td>
    <tr>
    <tr>
        <td>AWS Lambda </td>
        <td>-</td>
        <td>小于100次调用</td>
        <td>0</td>
    <tr>
    <tr>
        <td>存储</td>
        <td>Amazon S3</td>
        <td>-</td>
        <td>小于1G</td>
        <td>0.02美金</td>
    <tr>
    <tr>
        <td rowspan='4'>分析</td>
        <td>Amazon Athena</td>
        <td>-</td>
        <td>小于20次调用, 100M数据</td>
        <td>0.029美金</td>
    <tr>
    <tr>
        <td>Amazon QuickSight</td>
        <td>1个读取器</td>
        <td>长时间运行</td>
        <td>每个月8美金</td>
    <tr>
    <tr>
        <td>任务调度</td>
        <td>AWS Step Functions</td>
        <td>-</td>
        <td>小于100运行</td>
        <td>0</td>
    <tr>
    <tr>
        <td colspan='4'>总花费</td>
        <td>每天25.12美金</td>
    <tr>
</table>