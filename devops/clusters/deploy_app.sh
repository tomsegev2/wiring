#!/usr/bin/env bash

# Push the Docker images to ECR and deploy Docker images to the EKS

set -o xtrace

ENV=$1 && \
CLUSTER_TYPE=$2 && \

APP=$3 && \

CLUSTER_NAME=$ENV-$CLUSTER_TYPE && \
YELLOW='\033[0;33m'
NO_COLOR='\033[0m'

# Get state from bucket if missing
BUCKET_CONFIG_EXISTS=true
aws s3api head-object --bucket dev.secrets.beamup --key $CLUSTER_NAME-eks-cluster || BUCKET_CONFIG_EXISTS=false

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

export KUBECONFIG=~/.kube/$CLUSTER_NAME-eks-cluster && \
if [[ -z "${AWS_ACCESS_KEY_ID}" ]]; then
    export AWS_ACCESS_KEY_ID=`aws configure get default.aws_access_key_id`
    export AWS_SECRET_ACCESS_KEY=`aws configure get default.aws_secret_access_key`
fi

kubectl config current-context

cd  $CLUSTER_TYPE/apps/$APP && \

CURRENT_FOLDER=${PWD##*/} && \
CONFIGS=$CLUSTER_TYPE/apps/$APP/kubernetes_configs/$ENV && \
REPOSITORY=${CURRENT_FOLDER} && \
SERVICE=${CURRENT_FOLDER/_/-} && \
cd ../../.. && \
{ # try
    # copy yaml files to temp directory
    cp -R $CONFIGS "$CONFIGS"_tmp 
    # placing aws acceess key id and secret access key values to deployment env variables
    sed -i -e "s~{{AWS_ACCESS_KEY_ID}}~$AWS_ACCESS_KEY_ID~g" -e "s~{{AWS_SECRET_ACCESS_KEY}}~$AWS_SECRET_ACCESS_KEY~g" "$CONFIGS"_tmp/01-deployment.yaml 
    # applying yaml files in directory
    kubectl apply -f "$CONFIGS"_tmp
    kubectl delete -f "$CONFIGS"_tmp/03-hpa.yaml
    (cd ../utils/docker/kubernetes/configs && ./force_deploy.sh \
        $ENV \
        $CLUSTER_TYPE \
        $REPOSITORY \
        $SERVICE
    )
    kubectl apply -f "$CONFIGS"_tmp/03-hpa.yaml
    rm -rf "$CONFIGS"_tmp
} || { # catch
    echo -e "${YELLOW}Failed deploying $d. Skipping...${NO_COLOR}"
}