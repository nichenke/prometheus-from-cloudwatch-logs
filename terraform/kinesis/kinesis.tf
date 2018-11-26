locals {
  stream_name   = "${var.subdomain}-${var.stage}-lambda-logs"
}

resource "aws_kinesis_stream" "lambda_cloudwatch_logs" {
  name             = "${local.stream_name}"
  shard_count      = 1
  retention_period = 24

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
  ]

  tags = "${var.tags}"
}

# Create log group/stream/subscription to allow for manually injecting log messages.
resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name  = "${local.stream_name}"
  tags  = "${var.tags}"
}

resource "aws_cloudwatch_log_subscription_filter" "manual_log_injection" {
  name            = "manual_log_injection"
  role_arn        = "${aws_iam_role.lambda_cloudwatch_log_role.arn}"
  log_group_name  = "${aws_cloudwatch_log_group.lambda_cloudwatch_log_group.name}"
  filter_pattern  = ""
  destination_arn = "${aws_kinesis_stream.lambda_cloudwatch_logs.arn}"
  distribution    = "ByLogStream"
}