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
  App,
} from 'aws-cdk-lib';

import { Template } from 'aws-cdk-lib/assertions';

import {
  DashboardStack,
} from '../src/molecular-unfolding/cdk/stack-dashboard';

describe('Dashboard', () => {
  test('has 1 datasource', () => {
    const app = new App();
    const stack = new DashboardStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::QuickSight::DataSource', 1);
  });

  test('has 1 dataset', () => {
    const app = new App();
    const stack = new DashboardStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::QuickSight::DataSet', 1);
  });

  test('has 1 template', () => {
    const app = new App();
    const stack = new DashboardStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::QuickSight::Template', 1);
  });


  test('has 1 dashboard', () => {
    const app = new App();
    const stack = new DashboardStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::QuickSight::Dashboard', 1);
  });

  test('has 1 analysis', () => {
    const app = new App();
    const stack = new DashboardStack(app, 'test');
    const template = Template.fromStack(stack);
    template.resourceCountIs('AWS::QuickSight::Analysis', 1);
  });

  test('dataset is configed correctly', () => {
    const app = new App();
    const stack = new DashboardStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResourceProperties('AWS::QuickSight::DataSet', {
      PhysicalTableMap: {
        ATHENATable: {
          CustomSql: {
            Columns: [{
              Name: 'execution_id',
              Type: 'STRING',
            },
            {
              Name: 'compute_type',
              Type: 'STRING',
            },
            {
              Name: 'resolver',
              Type: 'STRING',
            },
            {
              Name: 'complexity',
              Type: 'INTEGER',
            },
            {
              Name: 'end_to_end_time',
              Type: 'DECIMAL',
            },
            {
              Name: 'running_time',
              Type: 'DECIMAL',
            },
            {
              Name: 'time_info',
              Type: 'STRING',
            },
            {
              Name: 'start_time',
              Type: 'STRING',
            },
            {
              Name: 'experiment_name',
              Type: 'STRING',
            },
            {
              Name: 'task_id',
              Type: 'STRING',
            },
            {
              Name: 'model_name',
              Type: 'STRING',
            },
            {
              Name: 'model_filename',
              Type: 'STRING',
            },
            {
              Name: 'scenario',
              Type: 'STRING',
            },
            {
              Name: 'resource',
              Type: 'STRING',
            },
            {
              Name: 'model_param',
              Type: 'STRING',
            },
            {
              Name: 'opt_param',
              Type: 'STRING',
            },
            {
              Name: 'create_time',
              Type: 'STRING',
            },
            {
              Name: 'result_detail',
              Type: 'STRING',
            },
            {
              Name: 'result_location',
              Type: 'STRING',
            }],
          },
        },
      },
    });
  });
});