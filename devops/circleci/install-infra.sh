# installing aws cli
echo "installing aws cli"
pip install awscli --upgrade --user
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set default.region $AWS_DEFAULT_REGION

# installing aws iam authenticatore
curl -o aws-iam-authenticator https://amazon-eks.s3-us-west-2.amazonaws.com/1.15.10/2020-02-22/bin/linux/amd64/aws-iam-authenticator
chmod +x ./aws-iam-authenticator
mkdir -p $HOME/bin && cp ./aws-iam-authenticator $HOME/bin/aws-iam-authenticator && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc

#installing kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl

echo "checking kubectl client"
kubectl version --client

# no need helm for deploying apps
# # installing helm
# echo "installing helm"
# curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > get_helm.sh
# chmod 700 get_helm.sh
# {
#     ./get_helm.sh
# } || { 
#     echo "tiller already installed on cluster"
# }

# helm version
echo "finished infrastructure installation"