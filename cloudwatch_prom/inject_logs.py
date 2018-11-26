""" Inject sample log messages to CloudWatch logs to test Kinesis stream forwarding and consumers """

import logging
import os

import watchtower
from prometheus_client import Summary, Counter, generate_latest, CollectorRegistry

# Use default testing group setup by Terraform
LOG_GROUP = os.environ.get('LOG_GROUP', 'testing-dev-lambda-logs')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = watchtower.CloudWatchLogHandler(log_group=LOG_GROUP,
                                          create_log_group=False, 
                                          stream_name=__file__)
logger.addHandler(handler)

LAMBDA_REGISTRY = CollectorRegistry()
RUNTIME = Summary('runtime_seconds', 'Total runtime in seconds', registry=LAMBDA_REGISTRY)
MESSAGE_TYPE = Counter('message_types', 'Message counts by time',
                       ['format'], registry=LAMBDA_REGISTRY)


@RUNTIME.time()
def send_logs():
    """ send logs """
    logger.info("Hi")
    MESSAGE_TYPE.labels(format='text').inc()

    logger.info(dict(foo="bar", details={}))
    MESSAGE_TYPE.labels(format='json').inc()


def main():
    send_logs()
    output = generate_latest(registry=LAMBDA_REGISTRY)

    # b'' -> string
    logger.info(dict(prometheus_text=output.decode()))


if __name__ == '__main__':
    main()
    output = generate_latest(registry=LAMBDA_REGISTRY)

    print(len(output))
    print(output.decode())