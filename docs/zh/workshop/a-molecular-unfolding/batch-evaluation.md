# 批量评估默认模型

批量评估默认模型将运行基于笔记本实验中的用例预构建的Amazon ECR镜像。

您可以通过AWS Step Functions工作流程运行批量评估，并利用Amazon QuickSight控制面板查看评估结果。

1. 登录[AWS CloudFormation控制台](https://console.aws.amazon.com/cloudformation/)。

2. 在**堆栈**页面，选择本方案的堆栈。

3. 选择**输出**页签，并点击AWS Step Functions链接。

4. 选择**启动**。
    
5. （可选）输入评估的相关内容。

     - 如果您不输入任何内容，它将使用默认输入。
     - 如果要自定义批量评估，请参考本节的[输入规范](#input-specification)。

6. 点击**启动**，开始批量评估。默认批量评估大约需要25分钟。

7. 批量评估完成后，从CloudFormation输出中获取仪表板链接，点击链接导航至仪表板，您可以在AWS QuickSight中查看整体的实验结果。

6. 在仪表盘中查看实验结果：

    - Experiments history：显示所有实验的历史信息。您也可以单击每条实验名称，查看每个实验的历史信息。
    - Comparison of end to end time of the quantum solver with classical solver：通过不同模型复杂度（X轴）比较QC和CC任务在不同求解器上端到端执行时间（Y轴）（如果没有选择实验，则计算平均时间）。
    - Comparison of running time of the quantum solver with classical solver：通过不同模型复杂度（X轴）比较QC和CC任务在不同求解器上实际运行时间（Y轴）（如果没有选择实验，则计算平均时间）。 
    - Experiments data：列出所选实验中每个任务的详细信息（如果没有选择实验，则列出所有）。

        | 字段  | 说明  |
        |---|---|
        | compute_type  | 计算类型。CC或QC。  |
        | complexity |模型复杂度。等于D*M的值。 |
        | end_to_end_time |端到端时间，单位为秒。 |
        | running_time | 实际执行时间，单位为秒。 |
        | resource  | 资源名称。对于不同QPU设备的QC，对于不同内存-vCPU的CC。  |
        | model_param  | 模型参数。</br>**M**：扭转次数； </br>**D**：旋转角度精度；</br> **HQ**：hubo-qubo 值，能量惩罚；</br> **A**：惩罚项 |
        | opt_param  | 优化器参数。  |
        | time_info |  对于QC，不同维度的QC任务时间，`local_time`是**end_to_end_time**，`total_time`是**running_time**；对于CC `local_time`是**end_to_end_time**，也是**running_time**。 |
        | execution_id  |Step Functions执行ID。 |
        | experiment_name  | 实验名称，如果输入`experimentName`不为空，则为`execution start time + input experimentName`，否则为`execution start time +execution_id`。  |
        | result_detail  | 分子展开前后的体积大小。  |
        | result_location | 展开后的分子mol2文件。  |

## 输入规范

您可以使用json输入自定义评估参数。

输入模式：

```json
{
    "version": "string",
    "runMode": "string",
    "mol2文件": "string",
    "modelVersion": "string",
    "experimentName": "string",
    "optParams": {
        "qa": {
            "shots": "int"
        },
        "sa": {
            "shots": "int"
        }
    },
    "modelParams": {
        "M": "int []",
        "D": "int []"
    },
    "devicesArns": "string []",
    "ccResources": "[int, int] []",
}

```

!!! Notice "说明"

    所有字段都是可选的。

定义：

  * **version**：输入模式的版本，当前仅支持值为`1`
  * **runMode**：运行模式，值可以是`ALL`、`CC`或`QC`，默认：`ALL`； `CC` - 仅运行 CC 任务，`QC` 仅运行 QC 任务，`ALL` - 运行两个任务
  * **mol2文件**: mol2文件的S3 URL
  * **modelVersion**：模型版本，默认为`latest`
  * **experimentName**：批量评估的名称
  * **optParams**：优化器参数，为QC(qa)和CC(sa)任务设置shots值
  * **modelParams**：模型参数，M：扭转数，D：旋转角度精度。详情请参考[建立模型-技术细节](./build-model-detail.md)。有效值：

         M: [1, 2, 3, 4, 5, 6, 7]
         D：[4] 或 [8]

    !!! Caution "注意"

        M 的最大值取决于 D、QPU 设备和输入 molFile 的值。在输入校验中，M最大值为100。
        在实际执行过程中，如果M值超过设备容量，执行会失败。
            
        如果使用自己的mol2文件，会跳过输入校验，如果值超过设备容量，会执行失败。

* **devicesArns**：QPU设备arn。有效值：
  
        arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6
        arn:aws:braket:::device/qpu/d-wave/Advantage_system4
        arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6
      
  * **ccResources**：vCPU（第一个元素）和 GiB中的内存（第二个元素），例如4个vCPU，8GiB内存是：`[4, 8]`

使用默认mol2文件的输入示例：

```json
{
    "version": "1",
    "runMode": "ALL",
    "optParams": {
        "qa": {
            "shots": 10000
        },
        "sa": {
            "shots": 10000
        }
    },
    "modelParams": {
        "M": [1, 2, 3, 4, 5],
        "D": [8]
    },
    "devicesArns": [
        "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        "arn:aws:braket:::device/qpu/d-wave/Advantage_system4",
        "arn:aws:braket:us-west-2::device/qpu/d-wave/Advantage_system6"
    ],
    "ccResources": [
        [4, 8]
    ]
```

如果您有mol2文件，可以按照以下步骤批量评估：

1. 将您的mol2文件上传到CloudFormation输出中的S3存储桶，或您自己的S3存储桶。如果您想使用自己的S3存储桶，存储桶名称必须遵循以下格式：`braket-*` 或 `amazon-braket-*`。

2. 在Step Functions输入中将mol2文件的S3 uri指定为`molFile` 的值。

     
        {
            "molFile" : "<您的 mol2 文件的 s3 uri>"
        }
   

       例如
    
        {
           “molFile”：“s3://amazon-braket-gcr-qc-sol-common/qc/raw_model/117_ideal.mol2”
        }

    

