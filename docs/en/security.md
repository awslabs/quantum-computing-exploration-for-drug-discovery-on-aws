When you build systems on AWS infrastructure, security responsibilities are shared between you and AWS. This [shared responsibility model](https://aws.amazon.com/compliance/shared-responsibility-model/) reduces your operational burden because AWS operates, manages, and controls the components including the host operating system, the virtualization layer, and the physical security of the facilities in which the services operate. For more information about AWS security, visit [AWS Cloud Security](http://aws.amazon.com/security/).

## Security groups

The security groups created in this solution are designed to control and isolate network traffic between the solution components. We recommend that you review the security groups and further restrict access as needed once the deployment is up and running.

## Amazon Braket Security 

Refer to [Security in Amazon Braket](https://docs.aws.amazon.com/braket/latest/developerguide/security.html) to learn how to apply the shared responsibility model when using Amazon Braket.

## Consider using Amazon Macie with Amazon S3

Amazon Macie is a data security and data privacy service that uses machine learning and pattern matching to help you discover, monitor, and protect sensitive data in your AWS environment. Macie automates the discovery of sensitive data, such as personally identifiable information (PII) and financial data, to provide you with a better understanding of the data that your organization stores in Amazon S3.

Macie also provides you with an inventory of your S3 buckets, and it automatically evaluates and monitors those buckets for security and access control. If Macie detects sensitive data or potential issues with the security or privacy of your data, it creates detailed findings for you to review and remediate as necessary. For more information, see [Amazon Macie User Guide](https://docs.aws.amazon.com/macie/latest/user/what-is-macie.html).