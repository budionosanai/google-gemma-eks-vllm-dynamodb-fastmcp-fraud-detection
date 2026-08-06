## MCP Server Part 1 : SageMaker Studio, vLLM, Gemma 4 and Terraform for Fraud Detection

1. Make sure already following instruction from [this link](https://dev.to/budionosan/mcp-server-part-1-sagemaker-studio-vllm-gemma-4-and-terraform-for-fraud-detection-3k3e) from step 1 until step 5.

2. Install Terraform and kubectl following instruction number 6.

3. Clone this repository in the JupyterLab instance terminal and all files are now available.

```bash
git clone https://github.com/budionosanai/google-gemma-eks-vllm-dynamodb-fastmcp-fraud-detection.git
```

4. Write and run this shell script in **scripts** folder for pull and push vLLM image to Amazon ECR private repository.
```
cd scripts
chmod +x vllm-to-ecr.sh
./vllm-to-ecr.sh
```

5. Write and run this shell script in **mcp-server** folder for build and push MCP server folder to Amazon ECR private repository.
```
cd ..

cd mcp-server

aws ecr create-repository \
    --repository-name "mcp-server-gemma-4" \
    --image-scanning-configuration scanOnPush=false \
    --image-tag-mutability MUTABLE \
    --region "us-west-2" 2>/dev/null || echo "Repository already exists, skipping creation."

pip install sagemaker-studio-image-build

sm-docker build . --repository mcp-server-gemma-4:latest
```

6. Write and run this Terraform script in **terraform** folder for create EKS cluster, DynamoDB table and VPC networking.
```
cd ..

cd terraform

terraform init

terraform plan

terraform apply --auto-approve
```

7. Generate data and upload data to DynamoDB "Transactions" table with write this shell script.
```
cd ..

cd scripts

python generate-data.py
```

![DynamoDB data](./images/dynamodb-data.PNG)

## MCP Server Part 2 : SageMaker Studio, Kubernetes manifest, Load Balancer and MCP Client for Fraud Detection

1. Update EKS Auto Mode cluster by run this shell script.
```
cd ..

cd manifests

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

aws eks update-kubeconfig --region us-west-2 --name vllm-mcp-server

aws iam list-roles \
  --query "Roles[?contains(RoleName, 'SageMaker')].[RoleName,Arn]" \
  --output table

aws eks create-access-entry \
  --cluster-name vllm-mcp-server \
  --principal-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/service-role/AmazonSageMaker-ExecutionRole-xxxxx \
  --type STANDARD \
  --region us-west-2

aws eks associate-access-policy \
  --cluster-name vllm-mcp-server \
  --principal-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/service-role/AmazonSageMaker-ExecutionRole-xxxxx \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster \
  --region us-west-2
```

2. Run this Kubernetes manifest of this vLLM service.
```
cd vllm
kubectl apply -f ebs.yaml
kubectl apply -f pvc.yaml
kubectl apply -f nodepool.yaml
kubectl apply -f envsubst < deployment.yaml | kubectl apply -f -
kubectl apply -f service.yaml
```

![vLLM manifest](./images/vllm-manifest.PNG)

3. Create and configure an EKS Pod Identity for access to Amazon DynamoDB.
```
cd ..

cd mcp-server

cat > dynamodb-mcp-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy \
    --policy-name DynamoDBMCPPolicy \
    --policy-document file://dynamodb-mcp-policy.json
rm -f dynamodb-mcp-policy.json

cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "pods.eks.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ]
    }
  ]
}
EOF

aws iam create-role \
    --role-name MCPServerPodRole \
    --assume-role-policy-document file://trust-policy.json
rm -f trust-policy.json

aws iam attach-role-policy \
    --role-name MCPServerPodRole \
    --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/DynamoDBMCPPolicy

aws eks create-pod-identity-association \
    --cluster-name vllm-mcp-server \
    --namespace default \
    --service-account mcp-server-sa \
    --role-arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/MCPServerPodRole
```

4. Run this Kubernetes manifest of this MCP server ingress/load balancer.
```
kubectl apply -f serviceaccount.yaml
envsubst < deployment.yaml | kubectl apply -f -
kubectl apply -f service.yaml
kubectl apply -f ingressclassparams.yaml
kubectl apply -f ingressclass.yaml
kubectl apply -f ingress.yaml
```

![MCP server manifest](./images/mcp-server-manifest.PNG)

5. Go to EC2 -> Load Balancing -> Load Balancers -> checklist Load Balancer -> Details -> **Copy DNS name to MCP client code** in **mcp-client** folder.

![MCP server ALB](./images/mcp-server-alb.PNG)

6. To access the MCP server, you need an MCP client using native MCP client from FastMCP or MCP client from Langchain.
```
cd ..

cd ..

cd mcp-client
```

7A. Open mcp-with-langchain.py file in mcp-client folder then look at this line of code.
```
client = Client("http://ALB_DNS_name/mcp")
```

7B. Replace ALB_DNS_name to DNS name of load balancer that already created and run the shell script below.
```
pip install langchain-mcp-adapters

python mcp-with-langchain.py
```

8A. Open mcp-without-langchain.py file in mcp-client folder look at this line of code.
```
ALB_URL = "http://ALB_DNS_name/mcp"
```

8B. Replace ALB_DNS_name to DNS name of load balancer that already created then run MCP without Langchain client code.
```
python mcp-without-langchain.py
```

![MCP client result](./images/mcp-client-result.PNG)

9. Write and run this Terraform script in **terraform** folder for delete all AWS services such as EKS, VPC, DynamoDB and other services.
```
cd ..

cd terraform

terraform destroy --auto-approve
```

10. In SageMaker Studio JupyterLab, click "Stop space" and [delete your SageMaker Studio domain.](https://docs.aws.amazon.com/sagemaker/latest/dg/gs-studio-delete-domain.html#gs-studio-delete-domain-studio)