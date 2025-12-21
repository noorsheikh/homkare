from aws_cdk import (
  aws_lambda as _lambda,
  aws_lambda_python_alpha as python_lambda,
)
from constructs import Construct

class LayerConstruct(Construct):
  _layer: python_lambda.PythonLayerVersion

  def __init__(self, scope: Construct, id, entry: str, layer_name: str):
    super().__init__(scope, id)

    self._layer = python_lambda.PythonLayerVersion(
      self,
      "Layer",
      layer_version_name=f"{layer_name}-lambda-layer",
      entry=entry,
      compatible_runtimes=_lambda.Runtime.PYTHON_3_13,
    )
