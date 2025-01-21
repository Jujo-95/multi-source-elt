
"""
sell

create a snoflake kafka connector for streaming data using snowpipe

export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_STREAMING
eval $(cat .env)

URL="https://$SNOWFLAKE_ACCOUNT.snowflakecomputing.com"
NAME="LIFT_TICKETS_KAFKA_STREAMING"

curl -i -X PUT -H "Content-Type:application/json" \
    "http://localhost:8083/connectors/$NAME/config" \
    -d '{
        "connector.class":"com.snowflake.kafka.connector.SnowflakeSinkConnector",
        "errors.log.enable":"true",
        "snowflake.database.name":"INGEST",
        "snowflake.private.key":"'$PRIVATE_KEY'",
        "snowflake.schema.name":"INGEST",
        "snowflake.role.name":"INGEST",
        "snowflake.url.name":"'$URL'",
        "snowflake.user.name":"'$SNOWFLAKE_USER'",
        "snowflake.enable.schematization": "FALSE",
        "snowflake.ingestion.method": "SNOWPIPE_STREAMING",
        "topics":"'$KAFKA_TOPIC'",
        "name":"'$NAME'",
        "value.converter":"org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable":"false",
        "buffer.count.records":"1000000",
        "buffer.flush.time":"10",
        "buffer.size.bytes":"250000000",
        "snowflake.topic2table.map":"'$KAFKA_TOPIC:LIFT_TICKETS_KAFKA_STREAMING'"
    }'

export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_STREAMING
cat data.json.gz | zcat | python ./publish_data.py

    
-- using schematization:

export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_STREAMING_SCHEMATIZED
eval $(cat .env)

URL="https://$SNOWFLAKE_ACCOUNT.snowflakecomputing.com"
NAME="LIFT_TICKETS_KAFKA_STREAMING_SCHEMATIZED"

curl -i -X PUT -H "Content-Type:application/json" \
    "http://localhost:8083/connectors/$NAME/config" \
    -d '{
        "connector.class":"com.snowflake.kafka.connector.SnowflakeSinkConnector",
        "errors.log.enable":"true",
        "snowflake.database.name":"INGEST",
        "snowflake.private.key":"'$PRIVATE_KEY'",
        "snowflake.schema.name":"INGEST",
        "snowflake.role.name":"INGEST",
        "snowflake.url.name":"'$URL'",
        "snowflake.user.name":"'$SNOWFLAKE_USER'",
        "snowflake.enable.schematization": "TRUE",
        "snowflake.ingestion.method": "SNOWPIPE_STREAMING",
        "topics":"'$KAFKA_TOPIC'",
        "name":"'$NAME'",
        "value.converter":"org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable":"false",
        "buffer.count.records":"1000000",
        "buffer.flush.time":"10",
        "buffer.size.bytes":"250000000",
        "snowflake.topic2table.map":"'$KAFKA_TOPIC:LIFT_TICKETS_KAFKA_STREAMING_SCHEMATIZED'"
    }'

export KAFKA_TOPIC=LIFT_TICKETS_KAFKA_STREAMING_SCHEMATIZED
cat data.json.gz | zcat | python ./py_publish_data.py


"""


import os
import logging
import sys
import confluent_kafka
from kafka.admin import KafkaAdminClient, NewTopic

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

kafka_brokers = os.getenv("REDPANDA_BROKERS")
topic_name = os.getenv("KAFKA_TOPIC")

def create_topic():
    admin_client = KafkaAdminClient(bootstrap_servers=kafka_brokers, client_id='publish_data')
    topic_metadata = admin_client.list_topics()
    if topic_name not in topic_metadata:
        topic = NewTopic(name=topic_name, num_partitions=10, replication_factor=1)
        admin_client.create_topics(new_topics=[topic], validate_only=False)

def get_kafka_producer():
    logging.info(f"Connecting to kafka")
    config = {'bootstrap.servers': kafka_brokers}
    return confluent_kafka.Producer(**config)

if __name__ == "__main__":  
    producer = get_kafka_producer()
    create_topic()
    for message in sys.stdin:
        if message != '\n':
            failed = True
            while failed:
                try:
                    producer.produce(topic_name, value=bytes(message, encoding='utf8'))
                    failed = False
                except BufferError as e:
                    producer.flush()
                
        else:
            break
    producer.flush()

