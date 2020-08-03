#!/usr/bin/env bash

set -o xtrace

ENV=$1 && \
APP=$2 && \
REPOSITORY=$3 && \
SERVICE=$4 && \

ACCOUNT=515538109774 && \
REGION=us-east-1 && \
CLUSTER_NAME=$ENV-$APP && \
NAMESPACE=$APP && \

# Get state from bucket if missing
BUCKET_CONFIG_EXISTS=true && \
aws s3api head-object --bucket dev.secrets.beamup --key $CLUSTER_NAME-eks-cluster || BUCKET_CONFIG_EXISTS=false && \

LOCAL_CONFIG_EXISTS=true
if [ ! -f ~/.kube/$CLUSTER_NAME-eks-cluster ]; then
  LOCAL_CONFIG_EXISTS=false
fi

if [ "$BUCKET_CONFIG_EXISTS" = true ]; then
    echo "Configuration found in bucket dev.secrets.beamup/${CLUSTER_NAME}-eks-cluster" && \
    aws s3 cp s3://dev.secrets.beamup/$CLUSTER_NAME-eks-cluster ~/.kube/$CLUSTER_NAME-eks-cluster
elif [ "$LOCAL_CONFIG_EXISTS" = true ]; then
    echo "Configuration exists locally"
else
    echo "${YELLOW}Configuration not found, exiting${NO_COLOR}" && \
    exit 1
fi

# Setup kubectl
export KUBECONFIG=~/.kube/$CLUSTER_NAME-eks-cluster && \

# Add some metadata to the deployment yaml to force rollout without changing image tag
kubectl -n ${NAMESPACE} patch deployment ${SERVICE} --patch \
"{\"spec\":{\"template\":{\"metadata\":{\"labels\":{\"date\":\"`date +'%s'`\"}}}}}"

# See deployment status
kubectl -n ${NAMESPACE} rollout status deployment ${SERVICE}

# Verify services
kubectl get services --namespace $NAMESPACE
kubectl describe services --namespace $NAMESPACE