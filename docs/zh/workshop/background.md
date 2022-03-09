---
title: 药物研发的量子计算动手实验
chapter: true
---

# 背景信息
<<<<<<< HEAD

药物研发量子计算解决方案是量子计算应用于药物发现问题的云原生解决方案。该解决方案试图将量子技术提供的新颖的计算模型和工业实际应用结合起来，并将根据近期的报告持续实施概念证明 (PoC)。它是一个开源项目，任何人都可以为其贡献代码，添加更多功能。

药物发现问题属于生物医药学的范畴，而生物医药学是直接受量子计算影响的科学类别之一。量子计算代表了新颖的计算模式，虽然该技术仍处于早期阶段，我们对其真正影响尚未完全了解。但是，目前我们已经进入量子计算的高速发展时期，这值得我们用真实的量子计算机开展研究和实验，对比不同的技术，从而探索让量子计算对业务产生真正价值的可能性。有关量子计算的多个用例，请参考[链接](https://www.forbes.com/sites/chuckbrooks/2021/03/21/the-emerging-paths-of-quantum-computing/?sh=765b2ed6613e)。
=======

药物研发量子计算解决方案是量子计算应用于药物发现的云原生解决方案。该解决方案试图将量子技术提供的新颖的计算模型和工业实际应用结合起来，并将不断根据最近的报告实施概念证明 (PoC)。它是一个开源项目，任何人都可以为添加更多相关解决方案的功能做出贡献。

药物发现问题属于生物医药学的范畴，而生物医药学是直接受量子计算影响的科学类别之一。量子计算代表了新颖的计算模式，虽然该技术仍处于早期阶段，我们对其真正影响尚未完全了解。但是，目前我们已经进入量子计算的高速发展时期，这值得我们用真实的量子计算机开展研究和实验，对比不同的技术，从而探索让量子计算对业务产生真正价值的可能性。量子计算有很多用例，请参考这个[链接](https://www.forbes.com/sites/chuckbrooks/2021/03/21/the-emerging-paths-of-quantum-computing/?sh=765b2ed6613e)。

>>>>>>> 0bc099045fa074a877542bc2a7d310f07d309952


<center>
![Drug Discovery](../images/drug-discovery.png)
图 1: 生物制药研发流程[<sup>1</sup>](#drug-discovery)
</center>

<<<<<<< HEAD
如图1所示，生物制药研发也是一个高风险且耗时的流程。从药物发现的众多候选药物到一颗经过FDA批准的药物，至少需要平均10年的时间，以及平均26亿美元的研发成本（以 2013 年美元计）。其中进入临床1期的候选药物只有不到12%会经过FDA批准。在过去 16 年的阿尔茨海默病治疗研究中，在临床研究中测试的 123 次治疗尝试中，只有四种新药被批准用于治疗阿尔茨海默病。这是3％的批准率。
(https://catalyst.phrma.org/the-drug-development-and-approval-process-is-about-much-more-than-the-final-okay)

但是，生物制药研发是一个高回报的领域。一个突破性疗法可以为数百万患者生活带来巨大的改变，并产生数十亿美元的利润。让我们考虑一下阿尔茨海默病治疗的案例。等到2025年批准的方法，该方法将阿尔兹海默病的并发症延迟至少五年。这会将该病的患者数量降低大概40%同时节省 3670 亿美元。
=======
制药是一个高回报的领域。一个突破性疗法可以为数百万患者生活带来巨大的改变，并产生数十亿美元的利润。
让我们考虑一下阿尔茨海默病治疗的案例。等到2025年批准的方法，该方法将阿尔兹海默病的并发症延迟至少五年。这会将该病的患者数量降低大概40%同时节省 3670 亿美元。但是，生物制药研发也是一个高风险且耗时的流程。如图1所示，从药物发现得到的众多候选药物到得到一颗经过FDA批准的药物，至少需要平均10年的时间，以及平均26亿美元的研发成本
（以 2013 年美元计）。其中进入临床1期的候选药物只有不到12%会经过FDA批准。在过去 16 年的阿尔茨海默病治疗研究中，在临床研究中测试的 123 次治疗尝试中，只有四种新药被批准用于治疗阿尔茨海默病。这是3％的批准率。
(https://catalyst.phrma.org/the-drug-development-and-approval-process-is-about-much-more-than-the-final-okay)
>>>>>>> 0bc099045fa074a877542bc2a7d310f07d309952

<center>
![CADD](../images/cadd.png)
图 2: CADD[<sup>2</sup>](#cadd)
</center>

<<<<<<< HEAD
如图2所示，研究人员利用计算机辅助药物设计 (CADD) 来提高药物发现的生产效率。这样可以更快更准确地找到候选药物，进而缩短整个制药周期。
=======
如图2所示，为了解决上述问题，研究人员利用计算机辅助药物设计 (CADD) 来提高药物发现的生产效率。这样有希望更快更准确地找到候选药物，进而缩短整个制药周期。
>>>>>>> 0bc099045fa074a877542bc2a7d310f07d309952

<center>
![CADD-QC](../images/cadd-qc.png)
图 3: CADD流程里面的量子计算用例[<sup>3</sup>](#cadd)
</center>

<<<<<<< HEAD
如图3所示，CADD有很多方法，例如，基于结构的和基于配基的。量子计算有希望被应用到其中的一些具体环节以提高效率，而研究人员已经列出了对应的技术以及应用的环节。比如将VQE求解器应用到分子对接等。
=======
如图3所示，CADD有很多方法，基于结构的和基于配基的。量子计算有希望被应用到其中的一些具体环节以提高效率，而研究人员已经列出了对应的技术以及应用的环节。比如将VQE求解器应用到分子对接等。
>>>>>>> 0bc099045fa074a877542bc2a7d310f07d309952
虽然我们还没有足够资源构造一个强大的量子计算机，即图3中的容错量子计算机（Fault-tolerant quantum computing, FTQC)。但是我们已经能够通过Amazon Braket访问嘈杂的中尺寸量子计算机（Noisy intermediate-scale quantum computing，NISQ）。这使得我们可以更方便开展药物发现与量子计算的研究课题，建立专业知识，和积累知识产权。
start with QC to research application, to
build expertise, and secure IP

# 参考
<div id='drug-discovery'></div>
- 1.“Cost of Developing a New Drug”. Tufts CSDD & School of Medicine and US FDA Infographics, Nov.2014
- 2.Sliwoski, Gregory, et al. "Computational methods in drug discovery." Pharmacological reviews 66.1 (2014): 334-395
- 3.Cao, Yudong, Jhonathan Romero, and Alán Aspuru-Guzik. "Potential of quantum computing for drug discovery." IBM Journal of Research and Development 62.6 (2018): 6-1.