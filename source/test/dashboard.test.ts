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
describe("Dashboard", () => {
    test("has 1 datasource", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::QuickSight::DataSource", 1)
    })

    test("has 1 dataset", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::QuickSight::DataSet", 1)
    })

    test("has 1 template", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::QuickSight::Template", 1)
    })


    test("has 1 dashboard", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::QuickSight::Dashboard", 1)
    })

    test("has 1 analysis", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.resourceCountIs("AWS::QuickSight::Analysis", 1)
    })

    test("dataset is configed correctly", () => {
        const app = new App();
        const stack = new MainStack(app, 'test');
        const template = Template.fromStack(stack);
        template.hasResourceProperties('AWS::QuickSight::DataSet', {
            PhysicalTableMap: {
                "ATHENATable": {
                    "CustomSql": {
                        "Columns": [{
                                "Name": "execution_id",
                                "Type": "STRING"
                            },
                            {
                                "Name": "compute_type",
                                "Type": "STRING"
                            },
                            {
                                "Name": "resource",
                                "Type": "STRING"
                            },
                            {
                                "Name": "params",
                                "Type": "STRING"
                            },
                            {
                                "Name": "opt_params",
                                "Type": "STRING"
                            },
                            {
                                "Name": "task_duration",
                                "Type": "DECIMAL"
                            },
                            {
                                "Name": "time_info",
                                "Type": "STRING"
                            },
                            {
                                "Name": "start_time",
                                "Type": "STRING"
                            },
                            {
                                "Name": "experiment_name",
                                "Type": "STRING"
                            },
                            {
                                "Name": "task_id",
                                "Type": "STRING"
                            },
                            {
                                "Name": "model_name",
                                "Type": "STRING"
                            },
                            {
                                "Name": "model_filename",
                                "Type": "STRING"
                            },
                            {
                                "Name": "scenario",
                                "Type": "STRING"
                            },
                            {
                                "Name": "create_time",
                                "Type": "STRING"
                            },
                            {
                                "Name": "result_detail",
                                "Type": "STRING"
                            },
                            {
                                "Name": "result_location",
                                "Type": "STRING"
                            },
                            {
                                "Name": "end_time",
                                "Type": "STRING"
                            }
                        ]
                    }
                }
            }
        })
    })
})