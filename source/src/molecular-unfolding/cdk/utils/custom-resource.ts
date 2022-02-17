import * as cdk from 'aws-cdk-lib';
import {
  Stack
} from 'aws-cdk-lib';
import {
  Construct
} from 'constructs'

import {
  aws_iam as iam
} from 'aws-cdk-lib'

import {
  aws_ec2 as ec2
} from 'aws-cdk-lib'

import {
  NodejsFunction
} from 'aws-cdk-lib/aws-lambda-nodejs';

import {
  Runtime
} from 'aws-cdk-lib/aws-lambda';

import {
  Provider
} from 'aws-cdk-lib/custom-resources';


function createCustomResourceLambdaRole(scope: Construct, roleName: string): iam.Role {
  const account_id = Stack.of(scope).account
  const region = Stack.of(scope).region

  const role = new iam.Role(scope, `${roleName}`, {
    assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  });

  role.addToPolicy(new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    resources: [
      '*'
    ],
    actions: [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:AssignPrivateIpAddresses",
      "ec2:UnassignPrivateIpAddresses"
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      cdk.Arn.format({
        service: 'logs',
        resource: 'log-group',
        resourceName: '*',
        arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
      }, cdk.Stack.of(scope))
    ],
    actions: [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:CreateLogGroup"
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      cdk.Arn.format({
        service: 'events',
        region: 'us-west-2',
        resource: 'rule/*',
        account: account_id,
        arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
      }, cdk.Stack.of(scope))

    ],
    actions: [
      "events:DescribeRule",
      "events:DeleteRule",
      "events:PutTargets",
      "events:EnableRule",
      "events:PutRule",
      "events:RemoveTargets",
      "events:DisableRule"
    ]
  }));

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      cdk.Arn.format({
        service: 'cloudformation',
        region: 'us-west-2',
        resource: `stack/QRSFDD-BraketEventTo${region}/*`,
        account: account_id,
        arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
      }, cdk.Stack.of(scope))
    ],
    actions: [
      "cloudformation:CreateChangeSet",
      "cloudformation:DeleteChangeSet",
      "cloudformation:DescribeChangeSet",
      "cloudformation:ExecuteChangeSet",
      "cloudformation:UpdateStack",
      "cloudformation:DeleteStack",
      "cloudformation:CreateStack",
      "cloudformation:DescribeStacks"
    ]
  }));
  return role;
}

function createEventBridgeRole(scope: Construct): iam.Role {
  const account_id = Stack.of(scope).account
  const region = Stack.of(scope).region

  const role = new iam.Role(scope, 'EventBridgeRole', {
    assumedBy: new iam.ServicePrincipal('events.amazonaws.com'),
  });

  role.addToPolicy(new iam.PolicyStatement({
    resources: [
      cdk.Arn.format({
        service: 'events',
        resource: 'event-bus/default',
        region: region,
        account: account_id,
        arnFormat: cdk.ArnFormat.COLON_RESOURCE_NAME,
      }, cdk.Stack.of(scope))
    ],
    actions: [
      "events:PutEvents"
    ]
  }));

  return role
}

interface Props {
  crossEventRegionCondition: cdk.CfnCondition;
  vpc: ec2.Vpc;
  sg: ec2.SecurityGroup
}

export default (scope: Construct, props: Props) => {

  const template_file = 'src/molecular-unfolding/cdk/utils/custom-resource-lambda/create-event-rule/template.json'

  const eventBridgeRole = createEventBridgeRole(scope);
  const role = createCustomResourceLambdaRole(scope, 'CreateEventRuleFuncRole')

  eventBridgeRole.grantPassRole(role)

  const createEventRuleFunc = new NodejsFunction(scope, 'CreateEventRuleFunc', {
    entry: `${__dirname}/custom-resource-lambda/create-event-rule/index.ts`,
    handler: 'handler',
    timeout: cdk.Duration.minutes(5),
    memorySize: 256,
    runtime: Runtime.NODEJS_14_X,
    reservedConcurrentExecutions: 5,
    role,
    vpc: props.vpc,
    securityGroups: [props.sg],
    vpcSubnets: props.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE_WITH_NAT
    }),
    environment: {
      'EVENT_BRIDGE_ROLE_ARN': eventBridgeRole.roleArn
    },

    bundling: {
      commandHooks: {
        beforeBundling(inputDir: string, outputDir: string): string[] {
          return [
            `cp ${inputDir}/${template_file} ${outputDir}`,
          ];
        },
        afterBundling(_inputDir: string, _outputDir: string): string[] {
          return [];
        },
        beforeInstall() {
          return [];
        },
      },
    }
  });

  createEventRuleFunc.node.addDependency(props.vpc)

  const provider = new Provider(
    scope,
    'EventRuleCustomResourceProvider', {
      onEventHandler: createEventRuleFunc
    },
  );

  const createEventRuleCustomResource = new cdk.CustomResource(scope, 'CreateEventRuleCustomResource', {
    serviceToken: provider.serviceToken
  });

  (createEventRuleCustomResource.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
  (createEventRuleFunc.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
  (role.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
  (eventBridgeRole.node.defaultChild as cdk.CfnCustomResource).cfnOptions.condition = props.crossEventRegionCondition;
}