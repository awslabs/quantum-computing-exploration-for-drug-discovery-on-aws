---
title: 药物发现的量子计算动手实验
chapter: true
---


药物发现量子计算解决方案是量子计算应用于药物发现的云原生解决方案。该解决方案试图将量子技术提供的新颖的计算模型和工业实际应用结合起来，并将不断根据最近的报告实现概念证明 (PoC)。它是一个开源项目，任何人都可以贡献代码，添加更多相关功能。

药物发现问题属于生物医药学的范畴，而生物医药学是直接受量子计算影响的科学类别之一。量子计算技术仍处于早期阶段，我们对其真正影响尚未完全了解。但是，目前我们已经进入量子计算的高速发展时期，这值得我们用真实的量子计算机开展研究和实验，对比不同的技术，从而探索让量子计算对业务产生真正价值的可能性。量子计算有多个用例，详情可参考[链接](https://www.forbes.com/sites/chuckbrooks/2021/03/21/the-emerging-paths-of-quantum-computing/?sh=765b2ed6613e)。

生物制药是一个高风险且耗时的流程。如图1所示，从药物发现得到的众多候选药物到得到一颗经过美国食品药品监督管理局（Food and Drug Administration, FDA）批准的药物，至少需要平均10年的时间，以及平均26亿美元的研发成本（以2013年美元计）。其中进入临床1期的候选药物只有不到12%会经过FDA批准。例如，在过去16年的阿尔茨海默病治疗研究中，在临床研究中测试的123次治疗尝试中，只有四种新药被批准用于治疗阿尔茨海默病，批准率仅有3%。（以上信息来源为：[The drug development and approval process is about much more than the final “okay”](https://catalyst.phrma.org/the-drug-development-and-approval-process-is-about-much-more-than-the-final-okay))

![Drug Discovery](../images/drug-discovery.png)
图 1: 生物制药研发流程[<sup>1</sup>](#drug-discovery)

为了解决上述问题，研究人员利用计算机辅助药物设计 (CADD) 来提高药物发现的生产效率。这样有望更快更准确地找到候选药物，进而缩短整个制药周期。

如图2所示，CADD有很多方法，有基于结构的和基于配基的。量子计算有望被应用到其中的一些具体环节以提高效率，而研究人员已经列出了对应的技术以及应用的环节，比如将VQE求解器应用到分子对接等。

![CADD](../images/cadd.png)
图 2: CADD[<sup>2</sup>](#cadd)


虽然我们还没有足够的资源构造一个强大的量子计算机，即图3中的容错量子计算机（Fault-tolerant quantum computing, FTQC)，但是我们已经能够通过Amazon Braket访问嘈杂的中尺寸量子计算机（Noisy intermediate-scale quantum computing，NISQ）。因此，我们可以更方便开展药物发现与量子计算的研究课题，建立专业知识，和积累知识产权。

![CADD-QC](../images/cadd-qc.png)
图 3: CADD流程里面的量子计算用例[<sup>3</sup>](#cadd)

# 参考
<div id='drug-discovery'></div>

 1. “Cost of Developing a New Drug”. Tufts CSDD & School of Medicine and US FDA Infographics, Nov.2014

 2. Sliwoski, Gregory, et al. "Computational methods in drug discovery." Pharmacological reviews 66.1 (2014): 334-395

 3. Cao, Yudong, Jhonathan Romero, and Alán Aspuru-Guzik. "Potential of quantum computing for drug discovery." IBM Journal of Research and Development 62.6 (2018): 6-1.