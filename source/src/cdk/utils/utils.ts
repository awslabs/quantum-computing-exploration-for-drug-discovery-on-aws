/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/


import {
  CfnResource,
  IAspect,
  Fn,
} from 'aws-cdk-lib';

import {
  IConstruct,
} from 'constructs';


export class AddCfnNag implements IAspect {
  visit(node: IConstruct): void {
    if (node.node.path.endsWith('/Notebook/NotebookRole/DefaultPolicy/Resource') ||
        node.node.path.endsWith('/BucketNotificationsHandler050a0587b7544547bf325f094a3db834/Role/DefaultPolicy/Resource') ||
        node.node.path.endsWith('/CreateEventRuleFuncRole/DefaultPolicy/Resource') ||
        node.node.path.endsWith('/checkHybridExperimentStatus/ServiceRole/DefaultPolicy/Resource')
    ) {
      addCFNNagMetadata(node, 'W12', 'some permissions are not resource-level permissions');
    } else if (node.node.path.endsWith('/SNSKey/Resource')) {
      addCFNNagMetadata(node, 'F76', 'Key for SNS, add constraint in conditions');
    } else if (node.node.path.endsWith('/checkHybridExperimentStatus/Resource')) {
      addCFNNagMetadata(node, 'W89', 'The version to be released does not need to have a VPC');
    } else if (node.node.path.endsWith('/accessLogs/Resource')) {
      addCFNNagMetadata(node, 'W35', 'This resource does not need to have accessLogs');
    }
  }
}

export function genRandomDigits(): string {
  return `${Fn.select(0, Fn.split('-', Fn.select(2, Fn.split('/', Fn.ref('AWS::StackId')))))}`;
}

function addCFNNagMetadata(node: IConstruct, id: string, reason: string) {
  (node as CfnResource).addMetadata('cfn_nag', {
    rules_to_suppress: [{ id, reason }],
  });
}
