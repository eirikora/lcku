import json
import base64
import os

# Load environment variable
encoded_key = os.getenv("GOOGLE_SHEETS_CREDS_JSON")

if encoded_key is None:
    print("FAILED to find environment variable GOOGLE_SHEETS_CREDS_JSON ! Unable to load Google Document!")
    exit()
    #return 'Failed to find key in GOOGLE_SHEETS_CREDS_JSON'
else:
    print('Encoded KEY is ' + encoded_key)

# Decode
decoded_key = base64.b64decode(encoded_key).decode('utf-8')

# Unpack JSON
original_service_key= json.loads(decoded_key)

print(json.dumps(original_service_key))
#print(original_service_key['private_key_id'])