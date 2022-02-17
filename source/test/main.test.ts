import {
    App
} from 'aws-cdk-lib';

import { Template } from "aws-cdk-lib/assertions";

import {
    SolutionStack
} from '../src/stack';

import {
    MainStack
} from '../src/molecular-unfolding/cdk/stack-main';

test('can create base stack', () => {
    const app = new App();
    const stack = new SolutionStack(app, 'test');
    Template.fromStack(stack);
});

test('can create MainStack', () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    expect(stack).not.toBeNull()
});

test("synthesizes the way we expect", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    expect(template).toBeTruthy()
})

test("has 1 s3 bucket", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('AWS::S3::Bucket', 1)
})

test("s3 bucket can be deleted", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('Custom::S3AutoDeleteObjects', 1)
})

test("has 1 vpc", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource('AWS::EC2::VPC', 1)
})

test("has 4 subnets", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource("AWS::EC2::Subnet", 4)
})

test("has 1 flowLog", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasResource("AWS::EC2::FlowLog", 1)
})

test("has output - bucketName", () => {
    const app = new App();
    const stack = new MainStack(app, 'test');
    const template = Template.fromStack(stack);
    template.hasOutput('bucketName', {})
})