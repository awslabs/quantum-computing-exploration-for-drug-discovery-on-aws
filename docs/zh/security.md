当您在亚马逊云科技基础设施上构建解决方案时，安全责任由您和亚马逊云科技共同承担。此[责任共担模型](https://aws.amazon.com/compliance/shared-responsibility-model/)减少了您的操作负担，这是由于亚马逊云科技操作、管理和控制组件，包括主机操作系统、虚拟化层以及服务运行所在设施的物理安全性。有关亚马逊云科技安全的更多信息，请访问亚马逊云科技[云安全](http://aws.amazon.com/security/)。

## 安全组

此解决方案中创建的安全组旨在控制和隔离各组件间的网络流量。我们建议您检查安全组，并在部署启动并运行后根据需要进一步限制访问。

### Amazon Braket安全设置

由于在解决方案中使用了Amazon Braket，请参考与其相关的[安全措施说明](https://docs.aws.amazon.com/braket/latest/developerguide/security.html)。


### 考虑将Amazon Macie与Amazon S3结合使用
Amazon Macie是一项数据安全和数据隐私服务，它使用机器学习和模式匹配来帮助您发现、监控和保护Amazon环境中的敏感数据。Macie自动发现敏感数据[例如个人身份信息（PII）和财务数据]，让您更好地了解组织在Amazon S3中存储的数据。

Macie还为您提供S3存储桶的清单，并且它会自动评估和监控这些存储桶以实现安全性和访问控制。如果Macie检测到敏感数据或潜在的数据安全性或隐私问题，它会创建详细的调查结果供您查看并在必要时进行补救。有关更多信息，请参阅[Amazon Macie用户指南](https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html)。