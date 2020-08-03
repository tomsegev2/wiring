
SERVICE=$1

echo "pushing images of ${SERVICE}"

IMAGE_TAG=$CIRCLE_BRANCH

if [ "$CIRCLE_BRANCH" == "develop" ]
then
    echo "branch is develop"
    IMAGE_TAG=development
elif [ "$CIRCLE_BRANCH" == "master" ]
then
    echo "branch is master"
    IMAGE_TAG=production
else
    echo "not pushing images of branch ${CIRCLE_BRANCH}"
    # exit 0
fi

echo "start push ing images with tag ${IMAGE_TAG}"
aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin 515538109774.dkr.ecr.us-east-1.amazonaws.com/$SERVICE
docker tag $SERVICE:$CIRCLE_BRANCH 515538109774.dkr.ecr.us-east-1.amazonaws.com/$SERVICE:$IMAGE_TAG
echo "pushing ${SERVICE}:${IMAGE_TAG} to ECR"
docker push 515538109774.dkr.ecr.us-east-1.amazonaws.com/$SERVICE:$IMAGE_TAG
