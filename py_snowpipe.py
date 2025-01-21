import os, sys, logging
import json
import uuid
import snowflake.connector
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import tempfile
from services.connect_snow import connect_snow

from dotenv import load_dotenv
from snowflake.ingest import SimpleIngestManager
from snowflake.ingest import StagedFile

from cryptography.hazmat.primitives import serialization

logging.basicConfig(level=logging.WARN)

PIPENAME = "LIFT_TICKETS_PY_SNOWPIPE"

def save_to_snowflake(snow, batch, temp_dir, ingest_manager):
    logging.debug('inserting batch to db')
    pandas_df = pd.DataFrame(batch, columns=["TXID","RFID","RESORT","PURCHASE_TIME", "EXPIRATION_TIME","DAYS","NAME","ADDRESS","PHONE","EMAIL", "EMERGENCY_CONTACT"])
    arrow_table = pa.Table.from_pandas(pandas_df)
    file_name = f"{str(uuid.uuid1())}.parquet"
    out_path = f"{temp_dir}/{file_name}"
    pq.write_table(arrow_table, out_path, use_dictionary=False,compression='SNAPPY')
    snow.cursor().execute("PUT 'file://{0}' @%{1}".format(out_path,PIPENAME))
    # send the new file to snowpipe to ingest (serverless)
    resp = ingest_manager.ingest_files([StagedFile(file_name, None)])
    os.unlink(out_path)
    logging.info(f"response from snowflake for file {file_name}: {resp['responseCode']}")


if __name__ == "__main__":    
    args = sys.argv[1:]
    batch_size = int(args[0])
    snow = connect_snow()
    batch = []
    temp_dir =  tempfile.mkdtemp(dir="tmp")
    temp_dir = temp_dir.replace("\\", "/")
    print(f'Temporary directory created at: {temp_dir}')
    private_key = "-----BEGIN PRIVATE KEY-----\n" + os.getenv("PRIVATE_KEY") + "\n-----END PRIVATE KEY-----\n)"
    host = os.getenv("SNOWFLAKE_ACCOUNT") + ".snowflakecomputing.com"
    ingest_manager = SimpleIngestManager(account=os.getenv("SNOWFLAKE_ACCOUNT"),
                                        host=host,
                                        user=os.getenv("SNOWFLAKE_USER"),
                                        pipe=F'INGEST.INGEST.{PIPENAME}',
                                        private_key=private_key)
    for message in sys.stdin:
        if message != '\n':
            record = json.loads(message)
            batch.append((record['txid'],record['rfid'],record["resort"],record["purchase_time"],record["expiration_time"],record['days'],record['name'],record['address'],record['phone'],record['email'], record['emergency_contact']))
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir, ingest_manager)
                batch = []
        else:
            break    
    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir, ingest_manager)
    snow.close()
    logging.info("Ingest complete")