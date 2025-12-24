from aws_cdk import (
    RemovalPolicy,
    aws_s3vectors as s3vectors,
    aws_iam as iam,
)
from constructs import Construct


class VectorBucketConstruct(Construct):
    _vector_bucket: s3vectors.CfnVectorBucket

    _vector_index: s3vectors.CfnIndex

    def __init__(self, scope: Construct, id):
        super().__init__(scope, id)

        self._vector_bucket = s3vectors.CfnVectorBucket(
            self,
            "Bucket",
            vector_bucket_name="homkare-vector-bucket",
        )
        self._vector_bucket.apply_removal_policy(RemovalPolicy.DESTROY)

        self._vector_index = s3vectors.CfnIndex(
            self,
            "Index",
            index_name="homkare-vector-index",
            data_type="float32",
            dimension=1024,
            distance_metric="cosine",
            vector_bucket_name=self._vector_bucket.vector_bucket_name,
        )

        self._vector_index.add_dependency(self._vector_bucket)

    def get_vector_iam_policy(self) -> iam.PolicyStatement:
        return iam.PolicyStatement(
            actions=[
                "s3vectors:PutVectors",
                "s3vectors:GetVectors",
                "s3vectors:QueryVectors",
                "bedrock:InvokeModel",
            ],
            resources=["*"],
        )

    def get_vector_bucket_name(self) -> str:
        return self._vector_bucket.vector_bucket_name

    def get_index_name(self) -> str:
        return self._vector_index.index_name
