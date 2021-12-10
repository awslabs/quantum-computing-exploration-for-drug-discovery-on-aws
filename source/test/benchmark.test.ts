import {
    App
} from '@aws-cdk/core';
import {
    //Capture,
    Match,
    Template
} from "@aws-cdk/assertions";
import {
    MainStack
} from '../src/molecule-unfolding/cdk/stack-main';
describe("Benchmarak", () => {
    test("has 1 batch ComputeEnvironment", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::Batch::ComputeEnvironment", 1)
    })

    test("has 1 batch JobQueue", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::Batch::JobQueue", 1)
    })
    test("has 2 batch JobDefinitions", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::Batch::JobDefinition", 2)
    })

    test("has 1 SNS", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::SNS::Topic", 1)
    })

    test("bechmark StateMachine", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        //const startAtCapture = new Capture();
        //const statesCapture = new Capture();

        template.resourceCountIs("AWS::StepFunctions::StateMachine", 5)
    })


    test("bechmark main StateMachine", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        //const startAtCapture = new Capture();
        //const statesCapture = new Capture();

        template.hasResourceProperties("AWS::StepFunctions::StateMachine", {
            DefinitionString: Match.objectLike({
                "Fn::Join": [
                    "",
                    [
                        "{\"StartAt\":\"Get Task Parameters\",\"States\":{\"Get Task Parameters\":{\"Next\":\"ParallelHPCJobs\",\"Retry\":[{\"ErrorEquals\":[\"Lambda.ServiceException\",\"Lambda.AWSLambdaException\",\"Lambda.SdkClientException\"],\"IntervalSeconds\":2,\"MaxAttempts\":6,\"BackoffRate\":2}],\"Type\":\"Task\",\"OutputPath\":\"$.Payload\",\"Resource\":\"arn:",
                        {
                            "Ref": "AWS::Partition"
                        },
                        ":states:::lambda:invoke\",\"Parameters\":{\"FunctionName\":\"",
                        {
                            "Fn::GetAtt": [
                                Match.anyValue(),
                                "Arn"
                            ]
                        },
                        "\",\"Payload\":{\"s3_bucket\":\"",
                        {
                            "Ref": Match.anyValue()
                        },
                        "\",\"param_type\":\"PARAMS_FOR_HPC\",\"execution_id.$\":\"$.execution_id\",\"context.$\":\"$$\"}}},\"ParallelHPCJobs\":{\"Type\":\"Map\",\"ResultPath\":\"$.parallelHPCJobsMap\",\"End\":true,\"Parameters\":{\"ItemIndex.$\":\"$$.Map.Item.Index\",\"ItemValue.$\":\"$$.Map.Item.Value\",\"execution_id.$\":\"$.execution_id\"},\"Iterator\":{\"StartAt\":\"Run HPC Batch Task\",\"States\":{\"Run HPC Batch Task\":{\"End\":true,\"Type\":\"Task\",\"Resource\":\"arn:aws:states:::batch:submitJob.sync\",\"Parameters\":{\"JobDefinition\":\"",
                        {
                            "Ref": Match.anyValue()
                        },
                        "\",\"JobName.$\":\"States.Format('HPCTask{}-{}', $.ItemIndex, $.ItemValue.task_name)\",\"JobQueue\":\"",
                        {
                            "Ref": Match.anyValue()
                        },
                        "\",\"ContainerOverrides\":{\"Command.$\":\"$.ItemValue.params\",\"ResourceRequirements\":[{\"Type\":\"VCPU\",\"Value.$\":\"States.Format('{}',$.ItemValue.vcpus)\"},{\"Type\":\"MEMORY\",\"Value.$\":\"States.Format('{}', $.ItemValue.memory)\"}]}},\"ResultSelector\":{\"JobId.$\":\"$.JobId\",\"JobName.$\":\"$.JobName\"}}}},\"ItemsPath\":\"$.hpcTaskParams\",\"MaxConcurrency\":20}}}"
                    ]
                ]
            })
        })
    })

    test("has 7 lambdas", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        //const startAtCapture = new Capture();
        //const statesCapture = new Capture();

        template.resourceCountIs("AWS::Lambda::Function", 7)
    
    })

    test("has lambdas with image package type", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        //const startAtCapture = new Capture();
        //const statesCapture = new Capture();

        template.hasResourceProperties("AWS::Lambda::Function", {
            "PackageType": "Image"
        })
    })

    test("has lambdas in vpc", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        //const startAtCapture = new Capture();
        //const statesCapture = new Capture();

        template.hasResourceProperties("AWS::Lambda::Function", {
            "VpcConfig": Match.anyValue()
        })
    })
})