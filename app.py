import aws_cdk as cdk
from OPA_Flow.Stacks.Flow_Stack import BedrockOpaFlowStack

app = cdk.App()

BedrockOpaFlowStack(
    app,
    "BedrockOpaFlowStack",
)

app.synth()