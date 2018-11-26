""" Watch Kinesis for incoming CloudWatch messages and turn into prometheus stats 

More information here: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html

The Data attribute in an Kinesis record is Base64 encoded and compressed with
the gzip format.

The incoming events look like this, they are 

{
    "owner": "111111111111",
    "logGroup": "CloudTrail",
    "logStream": "111111111111_CloudTrail_us-east-1",
    "subscriptionFilters": [
        "Destination"
    ],
    "messageType": "DATA_MESSAGE",
    "logEvents": [
        {
            "id": "31953106606966983378809025079804211143289615424298221568",
            "timestamp": 1432826855000,
            "message": "{\"eventVersion\":\"1.03\",\"userIdentity\":{\"type\":\"Root\"}"
        },
        {
            "id": "31953106606966983378809025079804211143289615424298221569",
            "timestamp": 1432826855000,
            "message": "{\"eventVersion\":\"1.03\",\"userIdentity\":{\"type\":\"Root\"}"
        },
        {
            "id": "31953106606966983378809025079804211143289615424298221570",
            "timestamp": 1432826855000,
            "message": "{\"eventVersion\":\"1.03\",\"userIdentity\":{\"type\":\"Root\"}"
        }
    ]
}


"""

# TODO
# state in DynamoDB for processing checkpoint

import datetime
import json
import logging
import os
from gzip import decompress


from kinesis.consumer import KinesisConsumer
from prometheus_client import start_http_server, Summary, CollectorRegistry, REGISTRY
from prometheus_client.parser import text_string_to_metric_families

STREAM_NAME = os.environ.get('LOG_STREAM_NAME', 'testing-dev-lambda-logs')

LAMBDA_REGISTRY = CollectorRegistry()
REGISTRY.register(LAMBDA_REGISTRY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


def update_prometheus_stats(prom_stats):
    """ take incoming metric text, parse, and update the global stats we are exposing """

    # TODO figure out how to lookup metrics we are already exporting and add the incoming samples
    metrics = text_string_to_metric_families(prom_stats)
    for metric in metrics:
        # Let the registry handle duplicate detection
        LAMBDA_REGISTRY.register(metric)


def main():
    """ run forever, processing just as fast as you can can can """
    consumer = KinesisConsumer(stream_name=STREAM_NAME)
    for message in consumer:

        # kinesis message containing one or more cloudwatch log events
        data = message['Data']
        tstamp = message['ApproximateArrivalTimestamp']

        # TODO what if not gzip'd or parseable - handle errors? 
        # What does this consumer do once we have state checkpointing?
        info = decompress(data)

        cw_data = json.loads(info)

        if cw_data['messageType'] != 'DATA_MESSAGE':
            print(f"skipping message: {cw_data}")
            continue

        # TODO Can we use the log group/stream/subscriptionFilters to lookup formatting ?

        group = cw_data['logGroup']
        stream = cw_data['logStream']
        subs = cw_data['subscriptionFilters']
        print(f"{tstamp}: Messages seen on {group}/{stream} subscription: {subs}")

        log_events = cw_data['logEvents']
        for log in log_events:
            logger.info('log event: %s', log)
            log_time = log['timestamp']

            # arrives in ms since epoch
            log_tstamp = datetime.datetime.utcfromtimestamp(log_time//1000)

            try:
                log_msg = json.loads(log['message'])
                prom_stats = log_msg.get('prometheus_text', '')

                update_prometheus_stats(prom_stats)

            except json.decoder.JSONDecodeError:
                log_msg = log['message']

            print(f"{log_tstamp}: Received message: {log_msg}")

if __name__ == '__main__':
    start_http_server(8000)
    main()