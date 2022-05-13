您需要承担运行量子计算探索之药物发现方案时使用亚马逊云科技各个服务的成本费用。实际成本取决于具体执行的任务和复杂性。截至2022年5月，影响解决方案的成本因素主要包括以下类型：

* 笔记本
* 计算
* 存储
* 分析
* 任务调度

## 示例

以分子展开应用为例，可以提前从[Protein Data Bank (PDB)](https://www.rcsb.org/downloads/ligands)下载配体117_idel.mol2。在美国东部（弗吉尼亚北部）区域（us-east-1），假设客户一直使用笔记本学习用例，当使用方案运行一次完整的对量子计算和经典计算的批量评估，以及在Amazon QuickSight中展示可视化结果时，成本费用如下表所示。

!!! Notice "说明"

    如果客户仅使用解决方案来研究用例，则成本主要包括笔记本和Amazon Braket的计算费用。


<table border='1' style="text-align: center">
    <tr>
        <td><B>类型</B></td>
        <td><B>服务</td>
        <td><B>资源</td>
        <td><B>运行状态</td>
        <td><B>费用</td>
    <tr>
    <tr>
        <td>笔记本</td>
        <td>Amazon Sagemaker</td>
        <td>ml.c5.xlarge</td>
        <td>长时间运行</td>
        <td>每天4.90美元</td>
    <tr>
    <tr>
        <td rowspan="9">计算</td>
        <td>Amazon Braket</td>
        <td>D-Wave - DW_2000Q_6</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>8.8美元</td>
    <tr>
    <tr>
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system4.1</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>8.8美元</td>
    <tr>
    <tr>
        <td>Amazon Braket</td>
        <td>D-Wave - Advantage_system6.1</td>
        <td>4个包含不同参数的任务, 每个任务10000次执行</td>
        <td>8.8美元</td>
    <tr>
    <tr>
        <td>Amazon Batch (Fargate) </td>
        <td>2 VCPU 4G MEM</td>
        <td>构建模型的任务, 8分钟（小于20分钟）</td>
        <td>1.02美元</td>
    <tr>
    <tr>
        <td>Amazon Batch (EC2) </td>
        <td>4 VCPU 8G MEM</td>
        <td>4个不同参数的任务, 25分钟（小于60分钟）</td>
        <td>0.17美元</td>
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
        <td>0.02美元</td>
    <tr>
    <tr>
        <td rowspan="3">分析</td>
        <td>Amazon Athena</td>
        <td>-</td>
        <td>小于20次调用, 100M数据</td>
        <td>0.029美元</td>
    <tr>
    <tr>
        <td>Amazon QuickSight</td>
        <td>1个读取器</td>
        <td>长时间运行</td>
        <td>每月8美元</td>
    <tr>
    <tr>
        <td>任务调度</td>
        <td>AWS Step Functions</td>
        <td>-</td>
        <td>小于100运行</td>
        <td>0</td>
    <tr>
    <tr>
        <td rowspan='4'>网络</td>
        <td>Amazon VPC</td>
        <td>Amazon S3</br>Amazon ECR</br>Amazon Athena</br>Amazon Braket</br>终端节点</td>
        <td>长时间运行</td>
        <td>每月58.41美元</td>
    <tr>
    <tr>
        <td>Amazon VPC</td>
        <td>NAT Gateway</td>
        <td>长时间运行</td>
        <td>每月65.78美元</td>
    <tr>
    <tr>
        <td colspan='4'>总花费</td>
        <td>每天37.01美元</td>
    <tr>
</table>