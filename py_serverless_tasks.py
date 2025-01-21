
"""
Hint: create the following objects in Snowflake before running this script

USE ROLE ACCOUNTADMIN;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE INGEST;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE INGEST;

USE ROLE INGEST;
CREATE OR REPLACE TABLE LIFT_TICKETS_PY_SERVERLESS (TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);

CREATE OR REPLACE TASK LIFT_TICKETS_PY_SERVERLESS 
USER_TASK_MANAGED_INITIAL_WAREHOUSE_SIZE='XSMALL' 
AS
COPY INTO LIFT_TICKETS_PY_SERVERLESS
FILE_FORMAT=(TYPE='PARQUET') 
MATCH_BY_COLUMN_NAME=CASE_SENSITIVE 
PURGE=TRUE;
"""

import json
import logging
import sys
import tempfile
import os

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import uuid


from services.connect_snow import connect_snow


logging.basicConfig(level=logging.WARN)


TASK_NAME = "LIFT_TICKETS_PY_SERVERLESS"

def save_to_snowflake(snow, batch, temp_dir):
    logging.debug('inserting batch to db')
    pandas_df = pd.DataFrame(batch, columns=["TXID","RFID","RESORT","PURCHASE_TIME", "EXPIRATION_TIME",
                                            "DAYS","NAME","ADDRESS","PHONE","EMAIL", "EMERGENCY_CONTACT"])
    arrow_table = pa.Table.from_pandas(pandas_df)
    out_path =  f"{temp_dir}/{str(uuid.uuid1())}.parquet"
    pq.write_table(arrow_table, out_path, use_dictionary=False,compression='SNAPPY')
    snow.cursor().execute("PUT 'file://{0}' @%{1}".format(out_path,TASK_NAME))
    os.unlink(out_path)
    # this will be skipped if the task is already scheduled, no warehouse will be used
    # when ran, the task will run as serverless
    snow.cursor().execute(f"EXECUTE TASK {TASK_NAME}")
    logging.debug(f"{len(batch)} tickets in stage")


if __name__ == "__main__":    
    args = sys.argv[1:]
    batch_size = int(args[0])
    snow = connect_snow()
    batch = []
    temp_dir = tempfile.mkdtemp(dir='tmp')
    temp_dir = temp_dir.replace("\\", "/")
    for message in sys.stdin:
        if message != '\n':
            record = json.loads(message)
            batch.append((record['txid'],record['rfid'],record["resort"],record["purchase_time"],record["expiration_time"],
                        record['days'],record['name'],record['address'],record['phone'],record['email'], record['emergency_contact']))
            if len(batch) == batch_size:
                save_to_snowflake(snow, batch, temp_dir)
                batch = []
        else:
            break    
    if len(batch) > 0:
        save_to_snowflake(snow, batch, temp_dir)
    snow.close()
    logging.info("Ingest complete")