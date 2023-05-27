## 笔记本实验

本笔记本基于Amazon Braket实现了[Quantum Speedup for Protein Structure Prediction](https://ieeexplore.ieee.org/document/9374469)。这主要由[Renata Wong](https://scholar.google.com/citations?user=XVFoBw4AAAAJ&hl=en) 和 [Weng-Long Chang](https://ieeexplore.ieee.org/author/37273919400)贡献。

## 使用Grover算法的蛋白质折叠

蛋白质折叠是蛋白质分子呈现其三维形状的过程，
这对其正常功能至关重要。
蛋白质由氨基酸的线性链组成，
它们的最终结构由氨基酸的序列和它们之间的相互作用决定。

在蛋白质折叠过程中，线性氨基酸链折叠成独特的三维结构，通过各种类型的相互作用（例如氢键、静电力和范德华力）来稳定该结构。蛋白质折叠的过程非常复杂，涉及多个阶段，包括二级结构的形成，例如 alpha 螺旋和 beta 折叠，以及将这些结构包装成最终的三维形状。

![Protein](../../images/protein-folding.png)

图13: 折叠前后的蛋白质[<sup>8</sup>](#wiki-protein)

在这项工作中，基于快速量子算法
建议使用 Grover 搜索。蛋白质结构
预测问题在研究
体心立方晶格的三维疏水-亲水模型。
结果显示二次加速
超过其经典同行。

![bcc](../../images/bcc.png)

图14: 体心立方晶格[<sup>11</sup>]

Grover 算法是一种量子算法，它
可用于搜索未分类的数据库
O(sqrt(N)) 时间内的 N 项。这是一个
显着加速相比
经典算法，需要 O(N) 时间来搜索未排序的数据库。

## 笔记本概览

1. 登录 [AWS CloudFormation 控制台](https://console.aws.amazon.com/cloudformation/home?)。
2. 在 **Stacks** 页面上，选择解决方案的根堆栈。
3. 选择 **Outputs** 选项卡并打开笔记本的链接。

    ![部署输出](../../images/deploy_output_notebook.png)

    图 15：堆栈输出选项卡上的笔记本 URL

4. 打开
**healthcare-and-life-sciences/c-2-protein-folding-grover-search/protein-folding-gs.ipynb**并选择内核
**qc_hcls_protein_folding_gs**。

# 参考
<div id='wiki-protein'></div>

- 10.[Wiki: Protein](https://en.wikipedia.org/wiki/Protein_folding)

- 11.[QFold: Quantum Walks and Deep Learning to Solve Protein Folding](https://iopscience.iop.org/article/10.1088/2058-9565/ac4f2f)