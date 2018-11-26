data "template_file" "kinesis_policy" {
  template = "${file("${path.module}/files/policy.tpl")}"

  vars {
    stream_arn  = "${aws_kinesis_stream.lambda_cloudwatch_logs.arn}"
    role_arn    = "${aws_iam_role.lambda_cloudwatch_log_role.arn}"
  }
}

resource "aws_iam_policy" "kinesis_policy" {
  name        = "${var.stage}-kinesis-policy"
  description = "Policy allowing Cloudwatch log actions on this Kinesis stream"

  policy      = "${data.template_file.kinesis_policy.rendered}"
}