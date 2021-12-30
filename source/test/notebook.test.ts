import {
    App
} from '@aws-cdk/core';
import {
    // Capture,
    // Match,
    Template
} from "@aws-cdk/assertions";
import {
    MainStack
} from '../src/molecule-unfolding/cdk/stack-main';
describe("Notebook", () => {
    test("has 1 notebook", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::SageMaker::NotebookInstance", 1)
    })

    test("the notebook has a lifecycle", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::SageMaker::NotebookInstanceLifecycleConfig", 1)
    })

})