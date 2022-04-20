量子计算探索之药物发现方案（Quantum Ready Architecture for Drug Discovery）旨在帮助客户研究药物发现问题，例如分子对接，蛋白质折叠等。通过[Amazon Braket][braket]调用量子计算资源进行实验，同时调用经典计算资源进行对比，从而让客户提升研究效率，获取研究的新思路。

本方案主要包括以下功能：

- 一键部署包含量子计算和经典计算工作流的混合架构
- 基于完全托管的Jupyter笔记本，设计和调试药物发现算法
- 基于[AWS Step Functions][step-functions]和[AWS Batch][batch]的工作流，批量验证算法性能
- 通过[Amazon Quicksight][quicksight]展示批量验证的结果
- 自定义其它药物发现问题的算法并进行复用

同时，该方案还提供配套的[动手实验](workshop/background.md)，以由Mato, Kevin, et al.[<sup>1</sup>](#original-author)提出的分子展开算法为例，介绍相关背景知识，建模和优化方法，批量验证和自定义算法等，从而帮助您更快了解如何运用量子计算技术研究药物发现问题。

本实施指南介绍在亚马逊云科技云中部署量子计算探索之药物发现方案的架构信息和具体配置步骤。它包含指向[CloudFormation][cloudformation]模板的链接，这些模板使用亚马逊云科技在安全性和可用性方面的最佳实践来启动和配置本解决方案所需的亚马逊云科技服务。

本指南面向药物发现领域的研究人员、数据科学家和算法工程师以及具有亚马逊云科技架构实践经验的量子计算爱好者。

# 参考
<div id='original-author'></div>
 
 - 1. Mato, Kevin, et al. "Quantum Molecular Unfolding." arXiv preprint arXiv:2107.13607 (2021).


[braket]: https://aws.amazon.com/braket/
[step-functions]: https://aws.amazon.com/step-functions/
[batch]: https://aws.amazon.com/batch/
[quicksight]: https://aws.amazon.com/quicksight/
[cloudformation]: https://aws.amazon.com/en/cloudformation/