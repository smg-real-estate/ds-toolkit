#!/bin/bash

set -eux
ln -sf /root /home/sagemaker-user

PRE_COMMIT_HOME=${HOME}/.cache/pre-commit
KERNELS_DIR=${HOME}/.kernels

if [ ! -d $HOME/.micromamba ]; then
  source $HOME/.micromamba/bashrc-studio.sh
fi

for env in $KERNELS_DIR/*; do
    micromamba run -r $KERNELS_DIR/$env \
      python -m ipykernel install --user --name "$BASENAME" \
      --display-name "Python (${BASENAME})"
done
