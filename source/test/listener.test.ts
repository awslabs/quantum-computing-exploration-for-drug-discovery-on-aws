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
describe("Listener", () => {
    test("has s3 notification", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("Custom::S3BucketNotifications", 1)
    })

    test("s3 notification is configed correctly", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.hasResourceProperties("Custom::S3BucketNotifications", {
            NotificationConfiguration: Match.objectLike({
                "LambdaFunctionConfigurations": [{
                    "Events": [
                        "s3:ObjectCreated:*"
                    ],
                    "Filter": {
                        "Key": {
                            "FilterRules": [{
                                    "Name": "suffix",
                                    "Value": "results.json"
                                },
                                {
                                    "Name": "prefix",
                                    "Value": "molecule-unfolding/qc_task_output/"
                                }
                            ]
                        }
                    },
                    "LambdaFunctionArn": {
                        "Fn::GetAtt": [
                            Match.anyValue(),
                            "Arn"
                        ]
                    }
                }]
            })
        })
    })
})