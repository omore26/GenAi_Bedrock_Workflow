import aws_cdk as cdk
from Flow_Stack import BedrockOpaFlowStack

app = cdk.App()

BedrockOpaFlowStack(
    app,
    "BedrockOpaFlowStack",
)

app.synth()