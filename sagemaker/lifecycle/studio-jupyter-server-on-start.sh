#!/bin/bash

set -eux

######################## Configure GIT ##############################
#####################################################################
cat > ~/.aws-credential-helper.py <<EOL
#!/opt/conda/envs/studio/bin/python3
import sys
import json
import boto3
import botocore
GIT_PROVIDER='$GIT_PROVIDER'
AWS_REGION='$AWS_REGION'
AWS_SECRET_NAME='$AWS_SECRET_NAME'
if len(sys.argv) < 2 or sys.argv[1] != 'get':
    exit(0)
credentials = {}
for line in sys.stdin:
    if line.strip() == "":
        break
    key, value = line.split('=')[0:2]
    credentials[key.strip()] = value.strip()
if credentials.get('host', '') == GIT_PROVIDER:
    client = boto3.client('secretsmanager', region_name=AWS_REGION)
    try:
        response = client.get_secret_value(SecretId=AWS_SECRET_NAME)
    except botocore.exceptions.ClientError as e:
        exit(1)
    if 'SecretString' in response:
        secret = response['SecretString']
        secret_dict = json.loads(secret)
        credentials['username'] = secret_dict['username']
        credentials['password'] = secret_dict['password']
for key, value in credentials.items():
    print('{}={}'.format(key, value))
EOL

chmod +x ~/.aws-credential-helper.py
git config --global credential.helper ~/.aws-credential-helper.py
#####################################################################
