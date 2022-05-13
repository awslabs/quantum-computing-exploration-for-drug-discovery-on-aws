## 笔记本实验

本动手实验尝试在Amazon Braket上面实现[Quantum Molecular Unfolding](https://arxiv.org/abs/2107.13607)和视频[Molecular Unfolding with Quantum Annealing](https://www.youtube.com/watch?v=1NmAXIHAF2Y)中介绍的工作。

## 分子对接

分子对接（Molecular Docking, MD）是药物发现过程中的一个重要步骤，用于计算当分子彼此结合时，第一个分子对第二个分子的最优位置和形状。

分子对接侧重于通过计算的方式模拟分子的识别过程，旨在找到蛋白质（体量较大和结构较复杂的分子）和配体（体量较小和结构较简单的分子）的优化构象以及蛋白质和配体之间的相对方向，从而最小化整个系统的自由能。

在分子对接中，蛋白质（也称为对接口袋）被认为是刚体结构，配体则被认为是可以灵活变化的原子集合。

![Molecular Docking](../../images/molecule-docking.png)

图 6: 分子对接[<sup>6</sup>](#wiki-docking)

根据[Quantum Molecular Unfolding](https://arxiv.org/abs/2107.13607)的说明，分子对接通常包含三个阶段：

* 配体展开，也即分子展开（Molecular Unfolding，MU）
    * 可旋转键的识别
    * 内部距离最大化
    * 消除工具相关的偏差 (例如，SMILES-to-3D)
* 初始放置
    * 配体主要片段分解
    * 配体初始姿态识别
    * 将配体放入带有刚性旋转平移的对接口袋中
* 形状细化
    * 使用可旋转键来修饰配体形状并匹配蛋白质对接口袋
    * 对接分数最大化

## AWS云上的量子分子展开

本实验主要关注分子对接的第一个阶段：配体扩张或者分子展开。这个阶段对于改进分子对接很重要。事实上，一个具有初始先验设置的配体位姿可能会引入影响最终对接质量的形状偏差。MU是用于消除这种初始偏差的技术。本方案利用Mato et al. 提出的量子退火方法来实现分子展开，通过AWS Braket在量子计算机上研究该问题，同时也在经典计算机上运行，并进行结果对比。

## 笔记本

1. 登录[AWS CloudFormation控制台](https://console.aws.amazon.com/cloudformation/home?)。

2. 在**堆栈**页面，选择本方案的堆栈。

3. 选择**输出**页签，并点击笔记本的链接。

    ![deployment output](../../images/deploy_output_notebook.png)
    图 7: 笔记本链接

4. 打开笔记本文件**source/src/molecular-folding/molecular_unfolding.ipynbn**，并确保笔记本的核为**qcenv**。

5. 浏览整个笔记本。它由四个步骤组成：

    - 第一步：准备数据，为实验准备分子数据
    - 第二步：建立模型，建立分子展开模型
    - 第三步：优化构型，运行优化以找到最佳构型
    - 第四步：处理结果，对结果进行处理以进行评估和可视化

<!-- |步骤|内容|
|:--|:--|
|[第一步: 准备数据](workshop/a-molecular-unfolding/prepare-data.ipynb)|为实验准备分子数据|
|[第二步: 建立模型](workshop/a-molecular-unfolding/build-model.ipynb)|建立分子展开模型|
|[第三步: 优化配置](workshop/a-molecular-unfolding/optimize-config.ipynb)|运行优化以找到配置|
|[第四步: 后处理](workshop/a-molecular-unfolding/post-process.ipynb)|对结果进行后处理以进行评估和可视化| -->




# 参考
<div id='wiki-docking'></div>
- 6.[Wikipedia: Docking (molecular)](https://en.wikipedia.org/wiki/Docking_(molecular))
