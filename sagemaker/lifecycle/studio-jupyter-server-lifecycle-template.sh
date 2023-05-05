 export GIT_USER='<Your User>'
 export GIT_EMAIL='<your email>'
 export GIT_PROVIDER="github.com"
 export AWS_REGION="eu-central-1"
# Secret name stored in AWS Secrets Manager that contains Git Provider credentials
 export AWS_SECRET_NAME='secret/name'
 export PROJECT_URL=https://raw.githubusercontent.com/smg-real-estate/ds-toolkit
 export BRANCH=main
 export TIMEOUT_IN_MINS=120
 export SCRIPT_PATH=sagemaker/lifecycle/studio-jupyter-server-on-start.sh
 curl -s ${PROJECT_URL}/${BRANCH}/${SCRIPT_PATH} | bash -s
