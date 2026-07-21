# Configuration
REGION="us-west-2"
SOURCE_IMAGE="public.ecr.aws/deep-learning-containers/vllm:0.25.0-gpu-py312-cu130-ubuntu22.04-ec2"
TARGET_REPO_NAME="vllm-gemma-4-eks"
TARGET_TAG="0.25.0-eks"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION")

ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
TARGET_IMAGE="${ECR_REGISTRY}/${TARGET_REPO_NAME}:${TARGET_TAG}"

# Create ECR repository (skip if already exists)
aws ecr create-repository \
    --repository-name "$TARGET_REPO_NAME" \
    --image-scanning-configuration scanOnPush=false \
    --image-tag-mutability MUTABLE \
    --region "$REGION" 2>/dev/null || echo "Repository already exists, skipping creation."

# Login to ECR
aws ecr get-login-password --region "$REGION" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY"

# Pull source image
docker pull "$SOURCE_IMAGE"

# Tag image
docker tag "$SOURCE_IMAGE" "$TARGET_IMAGE"

# Push image to ECR
docker push "$TARGET_IMAGE"

echo "Done! Image successfully pushed to ECR."