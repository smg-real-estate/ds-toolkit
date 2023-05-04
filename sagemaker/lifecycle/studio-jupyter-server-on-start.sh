#!/bin/bash

set -eux

######################## Configure GIT ##############################
#####################################################################
#
conda install -n base -y boto3 -c conda-forge
PYTHONEXEC=$(conda run -n base which python3)
cat > ~/.aws-credential-helper.py <<EOL
#!${PYTHONEXEC}
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
GIT_USER=$GIT_USER
GIT_EMAIL=$GIT_EMAIL
function git_config() {
  git config --global $1 $2
}
git_config credential.helper ~/.aws-credential-helper.py
git_config user.email "${GIT_EMAIL}"
git_config user.name "${GIT_USER}"
git_config pull.rebase true
git_config alias.a add
git_config alias.b branch
git_config alias.c commit
git_config alias.cl clone
git_config alias.co checkout
git_config alias.cp cherry-pick
git_config alias.m merge
git_config alias.p push --follow-tags
git_config alias.pu pull
git_config alias.r reset
git_config alias.s status
git_config alias.force-push push --force-with-lease
git_config alias.fp force-push
git_config init.defaultbranch main
#####################################################################
################### Configure Auto-shutdown #########################
# timeout in minutes
export TIMEOUT_IN_MINS=120
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

conda run -n studio pip install --no-dependencies --no-build-isolation -e .
conda run -n studio jupyter serverextension enable --py sagemaker_studio_autoshutdown

# Restarts the jupyter server
nohup supervisorctl -c /etc/supervisor/conf.d/supervisord.conf restart jupyterlabserver

# Waiting for 30 seconds to make sure the Jupyter Server is up and running
sleep 30

# Calling the script to set the idle-timeout and active the extension
/home/sagemaker-user/.auto-shutdown/set-time-interval.sh

#####################################################################
