data "template_file" "kinesis_trust" {
  template = "${file("${path.module}/files/trust.tpl")}"

  vars {
    region     = "${var.region}"
  }
}

resource "aws_iam_role" "lambda_cloudwatch_log_role" {
  name               = "lambda-cloudwatch-log-${var.stage}"
  assume_role_policy = "${data.template_file.kinesis_trust.rendered}"
}

resource "aws_iam_policy_attachment" "lambda_cloudwatch_log" {
  name       = "lambda-cloudwatch-log-${var.stage}"
  roles      = ["${aws_iam_role.lambda_cloudwatch_log_role.name}"]
  policy_arn = "${aws_iam_policy.kinesis_policy.arn}"
}
