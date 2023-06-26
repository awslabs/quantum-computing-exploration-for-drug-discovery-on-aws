Quantum Computing Exploration for Drug Discovery on AWS (QCEDD) helps you study drug discovery problems using quantum computing (Amazon Braket), such as molecular docking and protein folding. You can use [Amazon Braket][braket] to call quantum computing resources for experiments, and support user-customized algorithms to adapt to research findings in more scenarios.

This solution includes the following features:

- One-click deployment of the Jupyter environment required for quantum computing algorithms.
- A fully managed Jupyter Notebook, which can be used to design and debug drug discovery algorithms.
- Ability to customize algorithms for other drug discovery problems and reuse them.

This implementation guide includes a [workshop](workshop/background.md) with a series of notebook experimentation. For example, the workshop introduces the molecular unfolding algorithm from Mato, Kevin, et al.[<sup>1</sup>](#original-author) to illustrate the background information, how to build a model, optimize its configuration, and batch evaluate the experiment results.

This implementation guide describes architectural considerations and configuration steps for deploying the Quantum Computing Exploration for Drug Discovery on AWS in the Amazon Web Services (AWS) cloud. It includes links to [CloudFormation][cloudformation] templates that
launches and configures the AWS services required to deploy this solution using AWS best practices for security and availability.

The guide is intended for researchers, data scientists, algorithm engineers in the drug discovery field and quantum computing advocates with architecture hands-on experience in the AWS Cloud.

# Reference

<div id='original-author'></div>
 
 - 1.Mato, Kevin, et al. "Quantum Molecular Unfolding." arXiv preprint arXiv:2107.13607 (2021).

[sagemaker]: https://aws.amazon.com/sagemaker/
[braket]: https://aws.amazon.com/braket/
[ecr]: https://aws.amazon.com/ecr/
[s3]: https://aws.amazon.com/s3/
[eventbridge]: https://aws.amazon.com/eventbridge/
[sns]: https://aws.amazon.com/sns/
[cloudformation]: https://aws.amazon.com/en/cloudformation/
