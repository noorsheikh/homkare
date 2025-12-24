from typing import Mapping, Optional

from aws_cdk import (
	Duration,
	RemovalPolicy,
)
from aws_cdk import (
	aws_iam as iam,
)
from aws_cdk import (
	aws_lambda as _lambda,
)
from aws_cdk import (
	aws_logs as logs,
)
from constructs import Construct


class LambdaConstruct(Construct):
	_lambda_function: _lambda.Function

	def __init__(
		self,
		scope: Construct,
		id: str,
		function_name: str,
		code: _lambda.Code,
		handler: str,
		layers: Optional[list[_lambda.LayerVersion]] = None,
		environment: Optional[Mapping[str, str]] = None,
	):
		super().__init__(scope, id)

		log_group = logs.LogGroup(
			self,
			'LogGroup',
			log_group_name=f'/aws/lambda/{function_name}',
			retention=logs.RetentionDays.ONE_MONTH,
			removal_policy=RemovalPolicy.DESTROY,
		)

		self._lambda_function = _lambda.Function(
			self,
			'Function',
			function_name=function_name,
			code=code,
			handler=handler,
			layers=layers,
			runtime=_lambda.Runtime.PYTHON_3_13,
			timeout=Duration.minutes(5),
			memory_size=128,
			environment=environment,
			log_group=log_group,
		)

	def get_lambda_function(self) -> _lambda.Function:
		return self._lambda_function

	def add_to_role_policy(self, policy_statement: iam.PolicyStatement) -> None:
		self._lambda_function.add_to_role_policy(policy_statement)
