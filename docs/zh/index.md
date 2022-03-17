药物发现量子计算解决方案（Quantum Ready Architecture for Drug Discovery）旨在帮助客户研究药物发现问题，例如分子对接，蛋白质折叠等。通过[Amazon Braket][braket]调用量子计算资源进行实验，同时调用经典计算资源进行对比，从而让客户提升研究效率，获取研究的新思路。

本解决方案主要包括以下功能：

- 一键部署包含量子计算和经典计算工作流的混合架构
- 基于完全托管的Jupyter笔记本，设计和调试药物发现算法
- 基于[AWS Step Functions][step-functions]和[AWS Batch][batch]的工作流，批量验证算法性能
- 通过[Amazon Quicksight][quicksight]展示批量验证的结果
- 自定义其它药物发现问题的算法并进行复用

同时，该方案还提供配套的[动手实验](workshop/background.md)，以分子展开为例，介绍相关背景知识，建模和优化方法，批量验证和自定义算法等，从而帮助您更快了解如何运用量子计算技术研究药物发现问题。

本实施指南介绍在亚马逊云科技云中部署药物发现量子计算解决方案的架构信息和具体配置步骤。它包含指向[CloudFormation][cloudformation]模板的链接，这些模板使用亚马逊云科技在安全性和可用性方面的最佳实践来启动和配置本解决方案所需的亚马逊云科技服务。

本指南面向具有亚马逊云科技架构实践经验的IT架构师、开发人员、DevOps、数据科学家和算法工程师、以及药物发现领域的技术人员。

[braket]: https://aws.amazon.com/braket/
[step-functions]: https://aws.amazon.com/step-functions/
[batch]: https://aws.amazon.com/batch/
[quicksight]: https://aws.amazon.com/quicksight/
[cloudformation]: https://aws.amazon.com/en/cloudformation/