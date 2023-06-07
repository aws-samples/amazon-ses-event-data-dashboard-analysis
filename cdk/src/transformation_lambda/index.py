import base64
import json


def lambda_handler(event, context):
    output = []
    print("Event:\n",event)

    # remove firehose test events
    valid_records = [x for x in event['records'] if x['data'] != ""]

    output = map(parallel_process_record, valid_records)
    output_list = list(output)
    print(f"Successfully processed {len(output_list)} records")
    return {'records': output_list}

# Process records in event in parallel
def parallel_process_record(record):
    decoded_payload = base64.b64decode(record['data']).decode('utf-8')
    payload = json.loads(decoded_payload)
    updated_payload = process_record(payload)
    adjusted_payload = json.dumps(updated_payload) + '\n'
    output_record = {
        'recordId': record['recordId'],
        'result': 'Ok',
        'data': base64.b64encode(adjusted_payload.encode('utf-8'))
    }
    return output_record

# process individual records extracting only the fields listed in the
# template defined within this function
def process_record(record):
    f = open('schema.json')
    template = json.load(f)

    # update
    rec_update(template, record)

    return template

# recursively update the json template taken as reference (template) with the values
# extracted from the event passed to the Lambda (record)
def rec_update(template, record):
    if type(record) is not dict:
        template[record] = record

    for el in record:
        if type(record[el]) is dict:
            rec_update(template, record[el])
        elif el in template:
            template[el] = record[el]