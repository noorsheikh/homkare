#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.backend_stack import HomkareBackendStack


app = cdk.App()
HomkareBackendStack(
    app,
    "HomkareBackendStack",
    stack_name="homkare-backend-stack",
    description="This stack include resources for Homkare backend infrastructure.",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or cdk.Aws.ACCOUNT_ID,
        region=app.node.try_get_context("region") or cdk.Aws.REGION,
    ),
)

app.synth()
