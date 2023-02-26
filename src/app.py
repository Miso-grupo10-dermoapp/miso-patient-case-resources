
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget
from request_validation_utils import validate_property_exist
from request_response_utils import return_error_response, return_status_ok
from aws_services import upload_file

ENV_TABLE_NAME = "dermoapp-patient-cases"
DECODE_TYPE = "utf-8"

def handler(event, context):
    try:
        print("lambda execution with context {0}".format(str(context)))
        if validate_request_query_params(event):
            parser = StreamingFormDataParser(headers=event['headers'])
            file_name = ValueTarget()
            uploaded_file = ValueTarget()
            case_id = ValueTarget()
            parser.register("photo", uploaded_file)
            parser.register("photo_name", file_name)
            parser.register("case_id", case_id)

            parser.data_received(bytes(event["body"], DECODE_TYPE))
            upload_file(case_id.value.decode(DECODE_TYPE), file_name.value.decode(DECODE_TYPE), uploaded_file.value)
            return return_status_ok(event)
        else:
            return return_error_response("missing or malformed request body", 412)
    except Exception as err:
        return return_error_response("cannot proceed with the request error: " + str(err), 500)


def validate_request_query_params(request):
    return validate_property_exist("patient_id", request['pathParameters'])
