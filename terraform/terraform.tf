provider "aws" {
    region  = "${var.region}"
    profile = "default"
}

module "logs_kinesis_stream" {
    source       = "./kinesis"
    region       = "${var.region}"
    subdomain    = "${var.subdomain}"
    stage        = "${var.stage}"
    tags         = "${var.tags}"
}