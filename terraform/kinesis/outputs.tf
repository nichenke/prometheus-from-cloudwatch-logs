output lambda_cloudwatch_log_stream_arn {
  value = "${aws_kinesis_stream.lambda_cloudwatch_logs.arn}"
}