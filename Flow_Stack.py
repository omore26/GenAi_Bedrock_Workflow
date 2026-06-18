from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_bedrock as bedrock,
)

from constructs import Construct

class BedrockOpaFlowStack(Stack):
    def __init__(self, scope: Construct, construct_id : str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        #IAM Role used by Bedrock.
        bedrock_role = iam.Role(
            self,
            "BedrockFlowRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com")
        )

        # Allow model invocation
        bedrock_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )

        # Rego Generation Prompt
        prompt = """
You are an expert DevSecOps Engineer specializing in AWS security and OPA Rego policy generation.

Generate ONLY the required OPA Rego policy based on the user requirement below.

{{requirement}}

Rules:
- Output must start with: package main
- Use package main only once.
- Use deny contains msg if syntax.
- Do not include markdown, explanation, or code fences.
- Do not use unsafe variables.
- Do not use undefined helper functions.
- Use input.Resources[_] to read CloudFormation resources.
- Return only valid rego code.
- Generate only the requested policy. Do not add extra checks.

Return only the final Rego policy.
"""

        # Bedrock Flow Defination
        flow = bedrock.CfnFlow(
            self,
            "OpaPolicyFlow",
            name="Generate_OPA_Policies_Flow",
            description="Bedrock Flow to generate OPA policies for Kafka security checks.",
            execution_role_arn=bedrock_role.role_arn,
            definition={
                "nodes":[
                    # Flow Input
                    {
                        "name": "FlowInputNode",
                        "type": "Input",
                        "outputs": [
                            {
                                "name": "document",
                                "type": "String"
                            }
                        ]
                    },

                    # Generate policy using claude
                    {
                        "name": "PromptNode",
                        "type": "Prompt",
                        "inputs": [
                            {
                                "name": "requirement",
                                "type": "String",
                                "expression": "$.data"
                            }
                        ],
                        "outputs": [
                            {
                                "name": "modelCompletion",
                                "type": "String"
                            }
                        ],
                        "configuration": {
                            "prompt": {
                                "sourceConfiguration":{
                                    "inline": {
                                        "modelId": "us.anthropic.claude-sonnet-4-6",
                                        "templateType": "TEXT",
                                        "templateConfiguration":{
                                            "text": {
                                                "text": prompt,
                                                "inputVariables": [
                                                    {
                                                        "name": "requirement"
                                                    }
                                                ]
                                            }
                                        },
                                        "inferenceConfiguration":{
                                            "text": {
                                                "temperature": 0,
                                                "maxTokens": 3000
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },

                    # Return Generated Policy
                    {
                        "name": "FlowOutputNode",
                        "type": "Output",
                        "inputs": [
                            {
                                "name": "document",
                                "type": "String",
                                "expression": "$.data"
                            }
                        ]
                    }
                ],
                "connections": [
                    {
                        "name": "InputToPrompt",
                        "source": "FlowInputNode",
                        "target": "PromptNode",
                        "type": "Data",
                        "configuration": {
                            "data": {
                                "sourceOutput": "document",
                                "targetInput": "requirement"
                            }
                        }
                    },
                    {
                        "name": "PromptToOutput",
                        "source": "PromptNode",
                        "target": "FlowOutputNode",
                        "type": "Data",
                        "configuration": {
                            "data": {
                                "sourceOutput": "modelCompletion",
                                "targetInput": "document"
                            }
                        }
                    }
                ]
            }
        )

        # Stack Output
        CfnOutput(self, "FlowId", value=flow.attr_id)
        CfnOutput(self, "FlowArn", value=flow.attr_arn)