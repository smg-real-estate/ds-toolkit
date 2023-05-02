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
################### Configure Auto-shutdown #########################
# timeout in minutes
export TIMEOUT_IN_MINS=10
cd /home/sagemaker-user
mkdir -p .auto-shutdown

# Create the command-line script for setting the idle timeout
cat > .auto-shutdown/set-time-interval.sh << EOF
#!/opt/conda/bin/python
import json
import requests
TIMEOUT=${TIMEOUT_IN_MINS}
session = requests.Session()
# Getting the xsrf token first from Jupyter Server
response = session.get("http://localhost:8888/jupyter/default/tree")
# calls the idle_checker extension's interface to set the timeout value
response = session.post("http://localhost:8888/jupyter/default/sagemaker-studio-autoshutdown/idle_checker",
            json={"idle_time": TIMEOUT, "keep_terminals": False},
            params={"_xsrf": response.headers['Set-Cookie'].split(";")[0].split("=")[1]})
if response.status_code == 200:
    print("Succeeded, idle timeout set to {} minutes".format(TIMEOUT))
else:
    print("Error!")
    print(response.status_code)
EOF
chmod +x .auto-shutdown/set-time-interval.sh

extension_name=sagemaker_studio_autoshutdown-0.1.5

curl -s -L -o .auto-shutdown/${extension_name}.tar.gz \
  https://github.com/aws-samples/sagemaker-studio-auto-shutdown-extension/raw/main/${extension_name}.tar.gz

cd .auto-shutdown && tar xzf ${extension_name}.tar.gz
cd ${extension_name}

# activate stuidio conda environment and install the extension
eval "$(${CONDA_DIR}/bin/conda shell.bash hook 2> /dev/null)"
conda activate studio

pip install --no-dependencies --no-build-isolation -e .
jupyter serverextension enable --py sagemaker_studio_autoshutdown
conda deactivate

# Restarts the jupyter server
nohup supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart jupyterlabserver

# Waiting for 30 seconds to make sure the Jupyter Server is up and running
sleep 30

# Calling the script to set the idle-timeout and active the extension
/home/sagemaker-user/.auto-shutdown/set-time-interval.sh

#####################################################################
