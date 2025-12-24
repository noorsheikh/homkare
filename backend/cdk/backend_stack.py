from aws_cdk import (
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_cognito as cognito,
)
from aws_cdk import (
    aws_lambda as _lambda,
)
from constructs import Construct

from cdk.constructs.lambda_construct import LambdaConstruct
from cdk.constructs.layer_construct import LayerConstruct
from cdk.constructs.vector_bucket_construct import VectorBucketConstruct


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

        user_pool.add_client(
            "HomkareUserPoolClient",
            user_pool_client_name="homkare-user-pool-client",
            auth_flows=cognito.AuthFlow(
                user_password=True,
            ),
        )

        vector_bucket_construct = VectorBucketConstruct(self, "HomkareVectorBucket")

        rag_layer = LayerConstruct(
            self,
            "RagCoreLambdaLayer",
            layer_name="rag-core",
            entry="main/layers/rag_core_lib",
        )

        environment_variables = {
            "VECTOR_BUCKET_NAME": vector_bucket_construct.get_vector_bucket_name(),
            "VECTOR_INDEX_NAME": vector_bucket_construct.get_index_name(),
        }

        ingest_lambda = LambdaConstruct(
            self,
            "HomkareIngestLambda",
            function_name="homkare-ingest-lambda",
            code=_lambda.Code.from_asset("main/handlers/ingest"),
            handler="handler.lambda_handler",
            layers=[rag_layer.get_layer()],
            environment=environment_variables,
        )

        ingest_lambda.add_to_role_policy(
            vector_bucket_construct.get_vector_iam_policy()
        )

        query_lambda = LambdaConstruct(
            self,
            "HomkareQueryLambda",
            function_name="homkare-query-lambda",
            code=_lambda.Code.from_asset("main/handlers/query"),
            handler="handler.lambda_handler",
            layers=[rag_layer.get_layer()],
            environment=environment_variables,
        )
        query_lambda.add_to_role_policy(vector_bucket_construct.get_vector_iam_policy())
