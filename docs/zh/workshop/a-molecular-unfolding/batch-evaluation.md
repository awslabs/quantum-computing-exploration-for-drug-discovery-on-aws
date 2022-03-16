您可以通过AWS Step Functions工作流程运行批量评估，并利用Amazon QuickSight控制面板查看评估结果。

1. 从部署输出中获取AWS Step Functions链接，单击Step Functions链接导航至AWS Step Functions控制台。

2. 选择**启动执行**。
    
3. （可选）输入评估的相关内容。

     - 如果您不输入任何内容，它将使用默认输入。
     - 如果要自定义批量评估，请参考本节的[输入规范](#input-specification)。

4. 点击**启动执行**，开始批量评估。
    
    默认批量评估大约需要15分钟。

5. 批量评估完成后，从CloudFormation输出中获取仪表板链接，点击链接导航至仪表板，您可以在AWS QuickSight中查看整体的实验结果。

6. 您可以选择按照实验查看结果：by Experiment。

7. 单击每条实验名称，查看每个实验的批量评估结果。

    - QC vs. CC average：通过不同模型参数（X轴）比较QC和CC任务的平均执行时间（Y轴）
    - QC vs. CC by resource：通过不同模型参数（X轴）使用不同资源比较QC和CC任务的执行时间（Y轴）（对于QC是不同QPU设备，对于CC是不同的内存和vCPU） 
    - QC by devices：通过不同的模型参数（X轴）比较不同QPU设备的执行时间（Y轴）
    - CC by resources：通过不同的模型参数（X轴）比较不同CC资源（内存和vCPU）的执行时间（Y轴）
    - Records：列出了所选实验中每个任务的详细信息（如果没有选择实验，则列出所有）。

        | 字段  | 说明  |
        |---|---|
        | compute_type  | 计算类型。CC或QC。  |
        | resource  | 资源名称。对于不同QPU设备的QC，对于不同内存-vCPU的CC。  |
        | param  | 模型参数。</br>**M**：扭转次数； </br>**D**：旋转角度精度；</br> **HQ**：hubo-qubo 值，能量惩罚；</br> **A**：惩罚项 |
        | opt_params  | 优化器参数。  |
        | task_duration  | 任务执行时间，以秒为单位。  |
        | time_info | 对于QC，不同维度的QC任务时间，`total_time`是**task_duration**，对于CC，`local_time`是**task_duration**。  |
        | execution_id  |Step Functions执行ID。 |
        | experiment_name  | 实验名称，如果输入`experimentName`不为空，则为`execution start time + input experimentName`，否则为`execution start time +execution_id`。  |
        | task_id  | 对于QC任务，为Braket任务id；对于CC，为空。 |
        | result_detail  | 分子展开前后的体积大小。  |
        |  result_location | 展开后的分子mol2文件。  |


8. 您也可以切换维度按照资源查看结果：by Resource。
    
    您可以查看每个资源和QPU设备的批量评估结果。

    * 计算类型和资源
   
    它列出了批处理评估中的所有资源，对于QC来说，资源是QPU设备，对于CC来说，资源是内存和vCPU。表格中的项目是可点击的，当您单击一个项目（意味着您选择它）时，此工作表中的指标将切换到该项目。如果未选择任何项目，则显示平均指标。


    * 实验历史
    
    它使用不同的模型参数按实验名称（X轴，按时间排序）显示所选资源的执行时间（Y轴）。

    * 记录表
   
    此表与按实验查看结果的表相同。

### 输入规范

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

!!! 说明

    所有字段都是可选的。

定义：

  * **version**：输入模式的版本，当前仅支持值为`1`
  * **runMode**：运行模式，值可以是`ALL`、`CC`或`QC`，默认：`ALL`； `CC` - 仅运行 CC 任务，`QC` 仅运行 QC 任务，`ALL` - 运行两个任务
  * **mol2文件**: mol2文件的S3 URL
  * **modelVersion**：模型版本，默认为`latest`
  * **experimentName**：批量评估的名称
  * **optParams**：优化器参数, 为QC(qa)和CC(sa)任务设置shots值
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
      
  * **ccResources**：GiB 中的内存（第一个元素）和 vCPU（第二个元素），例如4GiB 内存和 2 个 vCPU 是：`[4, 2]`

典型（默认）输入：

```json
{
    "version": "1",
    "runMode": "ALL",
    "optParams": {
        "qa": {
            "shots": 1000
        },
        "sa": {
            "shots": 1000
        }
    },
    "modelParams": {
        "M": [1, 2, 3, 4],
        "D": [4]
    },
    "devicesArns": [
        "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
        "arn:aws:braket:::device/qpu/d-wave/Advantage_system4"
    ],
    "ccResources": [
        [2, 2],
        [4, 4],
        [8, 8],
        [16, 16]
    ]
}
```
