import json
import boto3
from botocore.config import Config as BotoConfig
from .config import Config

retry_config = BotoConfig(
    retries={
        "max_attempts": 10,
        "mode": "adaptive",
    },
    connect_timeout=10,
    read_timeout=10,
)

bedrock = boto3.client("bedrock-runtime", config=retry_config)


def get_embedding(text: str):
    """Generats a 1024-dimensional vector embedding for the given text."""
    body = json.dumps(
        {
            "inputText": text,
            "dimensions": 1024,
        }
    )

    response = bedrock.invoke_model(
        modelId=Config.EMBEDDING_MODEL,
        body=body,
        contentType="application/json",
    )
    return json.loads(response["body"].read())["embedding"]
