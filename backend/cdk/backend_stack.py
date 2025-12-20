from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigateway,
    # aws_apigatewayv2_integrations as integrations,
    aws_cognito as cognito,
    aws_s3vectors as s3vectors,
    aws_iam as iam,
)
from constructs import Construct

class HomkareBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_pool = cognito.UserPool(
            self,
            "HomkareUserPool",
            user_pool_name="homkare-cognito-user-pool",
            self_sign_up_enabled=True,
            sign_in_case_sensitive=False,
            account_recovery=cognito.AccountRecovery.PHONE_AND_EMAIL,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False),
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        user_pool_client = user_pool.add_client(
            "HomkareUserPoolClient",
            user_pool_client_name="homkare-user-pool-client",
            auth_flows=cognito.AuthFlow(
                user_password=True,
            ),
        )

        vector_bucket = s3vectors.CfnVectorBucket(
            self,
            "HomkareVectorBucket",
            vector_bucket_name="homkare-vector-bucket",
        )

        vector_index = s3vectors.CfnIndex(
            self,
            "HomkareVectorIndex",
            index_name="homkare-vector-index",
            data_type="float32",
            dimension=1024,
            distance_metric="cosine",
            vector_bucket_name=vector_bucket.vector_bucket_name,
        )

        vector_index.add_dependency(vector_bucket)

        ingest_lambda = _lambda.Function(
            self,
            "HomkareIngestLambda",
            function_name="homkare-ingest-lambda",
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda/ingest"),
            runtime=_lambda.Runtime.PYTHON_3_10,
            environment={
                "VECTOR_BUCKET": vector_bucket.vector_bucket_name,
                "VECTOR_INDEX": vector_index.index_name,
            }
        )

        vector_iam_policy = iam.PolicyStatement(
            actions=[
                "s3vectors:PutVectors",
                "s3vectors:GetVectors",
                "s3vectors:QueryVectors",
                "bedrock:InvokeModel",
            ],
            resources=["*"],
        )

        ingest_lambda.add_to_role_policy(vector_iam_policy)

        query_lambda = _lambda.Function(
            self,
            "HomkareQueryLambda",
            function_name="homkare-query-lambda",
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda/query"),
            runtime=_lambda.Runtime.PYTHON_3_10,
            environment={
                "VECTOR_BUCKET": vector_bucket.vector_bucket_name,
                "VECTOR_INDEX": vector_index.index_name,
            }
        )

        query_lambda.add_to_role_policy(vector_iam_policy)




