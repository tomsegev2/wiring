SERVICE=$1

echo "build single image of: ${SERVICE}"

IMAGE_TAG=$CIRCLE_BRANCH

echo "image is ${SERVICE}:${IMAGE_TAG}"
docker build -t ${SERVICE}:${IMAGE_TAG} --build-arg SERVICE_NAME=${SERVICE} -f Dockerfile .
