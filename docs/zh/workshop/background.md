---
title: 药物研发的量子计算动手实验
chapter: true
---

# 背景信息

药物研发量子计算解决方案是量子计算应用于药物发现的云原生解决方案。该解决方案试图将量子技术提供的新颖的计算模型和工业实际应用结合起来，并将不断根据最近的报告实施概念证明 (PoC)。它是一个开源项目，任何人都可以为添加更多相关解决方案的功能做出贡献。

药物发现问题属于生物医药学的范畴，而生物医药学是直接受量子计算影响的科学类别之一。量子计算代表了新颖的计算模式，虽然该技术仍处于早期阶段，我们对其真正影响尚未完全了解。但是，目前我们已经进入量子计算的高速发展时期，这值得我们用真实的量子计算机开展研究和实验，对比不同的技术，从而探索让量子计算对业务产生真正价值的可能性。量子计算有很多用例，请参考这个[链接](https://www.forbes.com/sites/chuckbrooks/2021/03/21/the-emerging-paths-of-quantum-computing/?sh=765b2ed6613e)。

这也是一个高回报的领域。一个突破性疗法可以为数百万患者生活带来巨大的改变，并产生数十亿美元的利润。
让我们考虑一下阿尔茨海默病治疗的案例。等到2025年批准的方法，该方法将阿尔兹海默病的并发症延迟至少五年。这会将该病的患者数量降低大概40%同时节省 3670 亿美元。


<center>
![Drug Discovery](../images/drug-discovery.png)
图 1: 药物研发过程[<sup>1</sup>](#drug-discovery)
</center>

药物发现是一个高风险且耗时的领域。在过去十年，经 FDA 批准的用于患者的新药的平均研发成本估计为 26 亿美元
（以 2013 年美元计）。这包括许多潜在没有通过FDA批准的药物的成本。例如，在过去 16 年的阿尔茨海默病治疗研究中，在临床研究中测试的 123 次治疗尝试中，只有四种新药被批准用于治疗阿尔茨海默病。这是3％的批准率。


<center>
![CADD](../images/cadd.png)
图 2: CADD[<sup>2</sup>](#cadd)
</center>

研究人员利用计算机辅助药物设计 (CADD) 来提告药物发现的效率，从而提高药物研发的生产效率。
的创新和进步有助于研究人员。

<center>
![CADD-QC](../images/cadd-qc.png)
图 3: CADD流程里面的量子计算用例[<sup>3</sup>](#cadd)
</center>

研究人员列出了可应用于一般工作流程中的量子技术。如上图所示，基于结构的方法和基于配体的方法可以从嘈杂的中等规模量子 (NISQ) 设备和容错技术中受益于量子计算技术。

# 参考
<div id='drug-discovery'></div>
- 1.“Cost of Developing a New Drug”. Tufts CSDD & School of Medicine and US FDA Infographics, Nov.2014
- 2.Sliwoski, Gregory, et al. "Computational methods in drug discovery." Pharmacological reviews 66.1 (2014): 334-395
- 3.Cao, Yudong, Jhonathan Romero, and Alán Aspuru-Guzik. "Potential of quantum computing for drug discovery." IBM Journal of Research and Development 62.6 (2018): 6-1.