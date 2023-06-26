## 笔记本实验

这个笔记本实现了
使用变分量子本征求解器 (vqe)来进行蛋白质折叠研究。

## 使用VQE的蛋白质折叠

蛋白质折叠是蛋白质分子呈现其三维形状的过程，
这对其正常功能至关重要。
蛋白质由氨基酸的线性链组成，
它们的最终结构由氨基酸的序列和它们之间的相互作用决定。

在蛋白质折叠过程中，线性氨基酸链折叠成独特的三维结构，通过各种类型的相互作用（例如氢键、静电力和范德华力）来稳定该结构。蛋白质折叠的过程非常复杂，涉及多个阶段，包括二级结构的形成，例如 alpha 螺旋和 beta 折叠，以及将这些结构包装成最终的三维形状。

![Protein](../../images/protein-folding.png)

图10: 折叠前后的蛋白质[<sup>8</sup>](#wiki-protein)

VQE是一种可以使用的量子算法
模拟分子的行为，
包括蛋白质。 VQE 的工作原理是近似
分子的基态能量使用
一台量子计算机，可用于
预测分子的性质。

要使用 VQE 进行蛋白质折叠，人们会
首先需要将蛋白质结构编码成一种格式，可以表示为
量子态。这可以使用
称为量子位化方法的技术，
它将蛋白质结构映射到一组可以由量子计算机操纵的量子位上。

部署完成后，您可以在**堆栈**页面选择解决方案的根堆栈，选择**输出（Outputs）**，打开笔记本的链接。请到**healthcare-and-life-sciences/c-2-protein-folding-variational-quantum-eigensolver/protein-folding-vqe.ipynb**查看细节。

# 参考
<div id='wiki-protein'></div>

- 10.[Wiki: Protein](https://en.wikipedia.org/wiki/Protein_folding)
