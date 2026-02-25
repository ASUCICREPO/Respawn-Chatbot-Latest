#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------
# ReSpawn - Adaptive Gaming ChatBot
# Deployment script for AWS CloudShell / local CLI
#
# This script:
#   1. Prompts for all required values
#   2. Creates an IAM service role for CodeBuild
#   3. Creates a CodeBuild project with all env vars
#   4. Starts the build (CDK deploy runs inside CodeBuild)
# --------------------------------------------------

# Generate unique project name with timestamp
PROJECT_NAME="ReSpawn-$(date +%Y%m%d%H%M%S)"

echo ""
echo "=================================================="
echo "  ReSpawn - Adaptive Gaming ChatBot Deployment"
echo "=================================================="
echo ""

# --------------------------------------------------
# 1. Prompt for GitHub repository URL
# --------------------------------------------------
if [ -z "${GITHUB_URL:-}" ]; then
  read -rp "Enter your GitHub repository URL
  (e.g. https://github.com/OWNER/Respawn-Chatbot-Latest): " GITHUB_URL
fi

# Normalize URL — strip .git and trailing slash
clean_url=${GITHUB_URL%.git}
clean_url=${clean_url%/}

# Parse owner and repo from HTTPS or SSH URL
if [[ $clean_url =~ ^https://github\.com/([^/]+/[^/]+) ]]; then
  path="${BASH_REMATCH[1]}"
  GITHUB_OWNER=${path%%/*}
  GITHUB_REPO=${path##*/}
elif [[ $clean_url =~ ^git@github\.com:([^/]+/[^/]+) ]]; then
  path="${BASH_REMATCH[1]}"
  GITHUB_OWNER=${path%%/*}
  GITHUB_REPO=${path##*/}
else
  echo "Unable to parse owner/repo from '$GITHUB_URL'"
  read -rp "Enter GitHub owner manually: " GITHUB_OWNER
  read -rp "Enter GitHub repo  manually: " GITHUB_REPO
fi

echo ""
echo "  Detected GitHub Owner : $GITHUB_OWNER"
echo "  Detected GitHub Repo  : $GITHUB_REPO"
read -rp "  Is this correct? (y/n): " CONFIRM
CONFIRM=$(printf '%s' "$CONFIRM" | tr '[:upper:]' '[:lower:]')
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "yes" && "$CONFIRM" != "" ]]; then
  read -rp "  Enter GitHub owner manually: " GITHUB_OWNER
  read -rp "  Enter GitHub repo  manually: " GITHUB_REPO
fi

# Always reconstruct a clean HTTPS URL
GITHUB_URL="https://github.com/$GITHUB_OWNER/$GITHUB_REPO"
echo ""
echo "  → Repository: $GITHUB_URL"

# --------------------------------------------------
# 2. Prompt for remaining required variables
# --------------------------------------------------
echo ""

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "  GitHub Personal Access Token is used to:"
  echo "  - Allow CodeBuild to clone your repository"
  echo "  - Allow Amplify to pull your repo for frontend builds"
  echo "  Create one at: https://github.com/settings/tokens"
  echo "  Required scope: repo (full control of private repositories)"
  echo ""
  read -rsp "  Enter GitHub Personal Access Token: " GITHUB_TOKEN
  echo ""
fi

if [ -z "${AWS_REGION:-}" ]; then
  read -rp "Enter AWS Region (default: us-east-1): " AWS_REGION
  AWS_REGION="${AWS_REGION:-us-east-1}"
fi

if [ -z "${AMPLIFY_BRANCH:-}" ]; then
  read -rp "Enter Git branch to deploy (default: main): " AMPLIFY_BRANCH
  AMPLIFY_BRANCH="${AMPLIFY_BRANCH:-main}"
fi

# Reuse GitHub token for Amplify — it's the same credential
AMPLIFY_OAUTH_TOKEN="$GITHUB_TOKEN"

if [ -z "${ACTION:-}" ]; then
  read -rp "Would you like to [deploy] or [destroy] the stack? (deploy/destroy): " ACTION
  ACTION=$(printf '%s' "$ACTION" | tr '[:upper:]' '[:lower:]')
fi

if [[ "$ACTION" != "deploy" && "$ACTION" != "destroy" ]]; then
  echo "[ERROR] Invalid choice: '$ACTION'. Please run again and choose deploy or destroy."
  exit 1
fi

# --------------------------------------------------
# 3. Confirm summary before proceeding
# --------------------------------------------------
echo ""
echo "  Configuration summary:"
echo "  ├─ Project Name  : $PROJECT_NAME"
echo "  ├─ Repository    : $GITHUB_URL"
echo "  ├─ Branch        : $AMPLIFY_BRANCH"
echo "  ├─ AWS Region    : $AWS_REGION"
echo "  ├─ GitHub Token  : [provided — used for CodeBuild + Amplify]"
echo "  └─ Action        : $ACTION"
echo ""
read -rp "  Proceed? (y/N): " PROCEED
if [[ ! "$PROCEED" =~ ^[Yy]$ ]]; then
  echo "  Deployment cancelled."
  exit 0
fi

# --------------------------------------------------
# 4. Ensure IAM service role exists for CodeBuild
# --------------------------------------------------
ROLE_NAME="${PROJECT_NAME}-service-role"
echo ""
echo "Checking for IAM role: $ROLE_NAME"

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  echo "  ✓ IAM role already exists"
  ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" \
    --query 'Role.Arn' --output text)
else
  echo "  Creating IAM role: $ROLE_NAME"

  TRUST_DOC='{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "codebuild.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'

  ROLE_ARN=$(aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$TRUST_DOC" \
    --query 'Role.Arn' --output text)

  echo "  Creating and attaching CDK deployment policy..."

  CUSTOM_POLICY_NAME="${PROJECT_NAME}-cdk-policy"
  CUSTOM_POLICY_ARN=$(aws iam create-policy \
    --policy-name "$CUSTOM_POLICY_NAME" \
    --policy-document '{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "cloudformation:*",
            "iam:*",
            "lambda:*",
            "s3:*",
            "bedrock:*",
            "aoss:*",
            "amplify:*",
            "codebuild:*",
            "logs:*",
            "apigateway:*",
            "ssm:*",
            "sts:GetCallerIdentity",
            "ecr:GetAuthorizationToken",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage"
          ],
          "Resource": "*"
        },
        {
          "Effect": "Allow",
          "Action": ["sts:AssumeRole"],
          "Resource": "arn:aws:iam::*:role/cdk-*"
        }
      ]
    }' \
    --query 'Policy.Arn' --output text)

  aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$CUSTOM_POLICY_ARN"

  echo "  ✓ IAM role created: $ROLE_ARN"
  echo "  Waiting 10 seconds for IAM role to propagate..."
  sleep 10
fi

# --------------------------------------------------
# 5. Create CodeBuild project
# --------------------------------------------------
echo ""
echo "Creating CodeBuild project: $PROJECT_NAME"

ENVIRONMENT=$(cat <<EOF
{
  "type": "LINUX_CONTAINER",
  "image": "aws/codebuild/standard:7.0",
  "computeType": "BUILD_GENERAL1_LARGE",
  "privilegedMode": true,
  "environmentVariables": [
    { "name": "GITHUB_TOKEN",        "value": "$GITHUB_TOKEN",   "type": "PLAINTEXT" },
    { "name": "GITHUB_OWNER",        "value": "$GITHUB_OWNER",   "type": "PLAINTEXT" },
    { "name": "GITHUB_REPO",         "value": "$GITHUB_REPO",    "type": "PLAINTEXT" },
    { "name": "AWS_REGION",          "value": "$AWS_REGION",     "type": "PLAINTEXT" },
    { "name": "AMPLIFY_REPOSITORY",  "value": "$GITHUB_URL",     "type": "PLAINTEXT" },
    { "name": "AMPLIFY_OAUTH_TOKEN", "value": "$GITHUB_TOKEN",   "type": "PLAINTEXT" },
    { "name": "AMPLIFY_BRANCH",      "value": "$AMPLIFY_BRANCH", "type": "PLAINTEXT" },
    { "name": "ACTION",              "value": "$ACTION",         "type": "PLAINTEXT" }
  ]
}
EOF
)

ARTIFACTS='{ "type": "NO_ARTIFACTS" }'
SOURCE='{ "type": "GITHUB", "location": "'"$GITHUB_URL"'", "buildspec": "buildspec.yml" }'

aws codebuild create-project \
  --name "$PROJECT_NAME" \
  --source "$SOURCE" \
  --artifacts "$ARTIFACTS" \
  --environment "$ENVIRONMENT" \
  --service-role "$ROLE_ARN" \
  --region "$AWS_REGION" \
  --output json \
  --no-cli-pager

echo "  ✓ CodeBuild project '$PROJECT_NAME' created successfully."

# --------------------------------------------------
# 6. Start the build
# --------------------------------------------------
echo ""
echo "Starting build..."

aws codebuild start-build \
  --project-name "$PROJECT_NAME" \
  --region "$AWS_REGION" \
  --no-cli-pager \
  --output json

echo "  ✓ Build started successfully."

# --------------------------------------------------
# 7. Show current CodeBuild projects
# --------------------------------------------------
echo ""
echo "Current CodeBuild projects in $AWS_REGION:"
aws codebuild list-projects --region "$AWS_REGION" --output table

# --------------------------------------------------
# Done
# --------------------------------------------------
echo ""
echo "=================================================="
echo "  Build submitted to CodeBuild!"
echo "=================================================="
echo ""
echo "  Monitor your build:"
echo "  → AWS Console → CodeBuild → Build projects → $PROJECT_NAME"
echo ""
echo "  After the build completes (~10-15 min):"
echo "  1. Enable Bedrock model access"
echo "     → Amazon Bedrock → Model access → Enable Nova Lite + Titan Embeddings"
echo "  2. Sync the Knowledge Base"
echo "     → Amazon Bedrock → Knowledge Bases → Select KB → Sync data source"
echo "  3. Find your app URL"
echo "     → AWS Amplify → adaptive-gaming-guide → your branch URL"
echo ""
echo "  See documents/DEPLOYMENT_GUIDE.md for full post-deployment steps."
echo ""

exit 0
