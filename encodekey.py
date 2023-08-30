import json
import base64
import os
#from dotenv import load_dotenv, find_dotenv

service_key = ''
try:
    with open('GOOGLE_KEY.json', 'r') as file:
        service_key = json.load(file)
except FileNotFoundError:
    print("ERROR: Could not find JSON file.")
    exit()

# convert json to a string
service_key = json.dumps(service_key)

# encode service key
encoded_service_key = base64.b64encode(service_key.encode('utf-8'))

print(encoded_service_key)
# b'many_characters_here'