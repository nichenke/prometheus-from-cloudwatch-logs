variable "region" {
    default = "us-west-2"
}

variable "stage" {
    default = "dev"
}

variable "subdomain" {
    default = "testing"
}

variable "tags" {
  type = "map"

  default = {
    Team              = "Loggers"
  }
}
