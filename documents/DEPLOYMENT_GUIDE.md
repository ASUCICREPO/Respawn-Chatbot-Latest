# ReSpawn - Deployment Guide

This guide provides multiple deployment options for the ReSpawn Adaptive Gaming ChatBot application.

## Table of Contents

1. [Quick Deployment with Script](#quick-deployment-with-script)
2. [Manual Deployment](#manual-deployment)
3. [AWS CloudShell Deployment](#aws-cloudshell-deployment)
4. [AWS CodeBuild Deployment](#aws-codebuild-deployment)
5. [Post-Deployment Configuration](#post-deployment-configuration)

---

## Quick Deployment with Script

The fastest way to deploy ReSpawn is using the automated deployment script.

### Prerequisites

- AWS CLI v2.x installed and configured
- Node.js v20 or higher
- Git
- AWS account with appropriate permissions
- GitHub Personal Access Token

### Step 1: Clone the Repository

```bash
git clone https://github.com/ASUCICREPO/Respawn-Chatbot-Latest.git
cd Respawn-Chatbot-Latest
```

### Step 2: Set Environment Variables

```bash
export AWS_PROFILE="your-aws-profile"
export AWS_REGION="us-east-1"
export AMPLIFY_REPOSITORY="https://github.com/ASUCICREPO/Respawn-Chatbot-Latest"
export AMPLIFY_OAUTH_TOKEN="your-github-token"
export WEB_CRAWL_SEED_URLS="https://www.gamingreadapted.com/,https://gameaccess.info/"
export AMPLIFY_BRANCH="main"
```

### Step 3: Run Deployment Script

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Step 4: Note the Outputs

After successful deployment, the script will output:
- API Gateway URL
- Knowledge Base ID
- OpenSearch Collection Name
- Amplify App ID
- Amplify App URL

The Amplify URL will also be saved to `amplify-url.txt` in the root directory.

---

## Manual Deployment

For more control over the deployment process, follow these manual steps.

### Step 1: Install Dependencies

```bash
# Install CDK dependencies
cd backend/infrastructure/cdk
npm install
cd ../../..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 2: Configure AWS Credentials

**Option A: AWS SSO**
```bash
aws sso login --profile your-profile-name
export AWS_PROFILE=your-profile-name
```

**Option B: AWS Configure**
```bash
aws configure
# Enter your Access Key ID and Secret Access Key
```

### Step 3: Bootstrap CDK

```bash
cd backend/infrastructure/cdk

# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Bootstrap CDK
npx cdk bootstrap aws://${AWS_ACCOUNT_ID}/us-east-1
```

### Step 4: Deploy Infrastructure

```bash
npx cdk deploy \
  --parameters WebCrawlSeedUrls="https://www.gamingreadapted.com/,https://gameaccess.info/" \
  --parameters AmplifyRepository="https://github.com/ASUCICREPO/Respawn-Chatbot-Latest" \
  --parameters AmplifyOauthToken="YOUR_GITHUB_TOKEN" \
  --parameters AmplifyBranch="main" \
  --require-approval never
```

### Step 5: Verify Deployment

```bash
# List CDK outputs
npx cdk output

# Check Amplify app status
aws amplify list-apps --query "apps[?name=='adaptive-gaming-guide']"
```

---

## AWS CloudShell Deployment

Deploy directly from AWS CloudShell without installing any tools locally.

### Step 1: Open AWS CloudShell

1. Log in to AWS Console
2. Click the CloudShell icon (terminal icon) in the top navigation bar
3. Wait for CloudShell to initialize

### Step 2: Install Node.js 20

```bash
# Download and install Node.js 20
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
node --version  # Should show v20.x.x
```

### Step 3: Clone Repository

```bash
git clone https://github.com/ASUCICREPO/Respawn-Chatbot-Latest.git
cd Respawn-Chatbot-Latest
```

### Step 4: Set Environment Variables

```bash
export AWS_REGION="us-east-1"
export AMPLIFY_REPOSITORY="https://github.com/ASUCICREPO/Respawn-Chatbot-Latest"
export AMPLIFY_OAUTH_TOKEN="your-github-token"
export WEB_CRAWL_SEED_URLS="https://www.gamingreadapted.com/,https://gameaccess.info/"
export AMPLIFY_BRANCH="main"

# CloudShell uses the console session credentials, no need to set AWS_PROFILE
export AWS_PROFILE="default"
```

### Step 5: Run Deployment

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Step 6: Access Outputs

The deployment outputs will be displayed in the terminal. Copy the Amplify URL to access your application.

---

## AWS CodeBuild Deployment

Automate deployments using AWS CodeBuild for CI/CD.

### Step 1: Create CodeBuild Project

1. Go to AWS Console → CodeBuild → Create build project
2. Configure the following:

**Project Configuration:**
- Project name: `respawn-chatbot-deploy`
- Description: `Deploy ReSpawn Adaptive Gaming ChatBot`

**Source:**
- Source provider: GitHub
- Repository: `https://github.com/ASUCICREPO/Respawn-Chatbot-Latest`
- Branch: `main`
- Connect using OAuth (authorize GitHub access)

**Environment:**
- Environment image: Managed image
- Operating system: Amazon Linux 2
- Runtime: Standard
- Image: `aws/codebuild/standard:7.0`
- Service role: Create new service role or use existing

**Buildspec:**
- Build specifications: Use a buildspec file
- Buildspec name: `buildspec.yml` (we'll create this)

### Step 2: Create Buildspec File

Create `buildspec.yml` in the repository root:

```yaml
version: 0.2

env:
  parameter-store:
    AMPLIFY_OAUTH_TOKEN: /respawn/github-token
  variables:
    AWS_REGION: us-east-1
    AMPLIFY_REPOSITORY: https://github.com/ASUCICREPO/Respawn-Chatbot-Latest
    WEB_CRAWL_SEED_URLS: https://www.gamingreadapted.com/,https://gameaccess.info/
    AMPLIFY_BRANCH: main

phases:
  install:
    runtime-versions:
      nodejs: 20
      python: 3.11
    commands:
      - echo "Installing dependencies..."
      - npm install -g aws-cdk
      - cd backend/infrastructure/cdk && npm install && cd ../../..
      
  pre_build:
    commands:
      - echo "Bootstrapping CDK..."
      - export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      - export AWS_PROFILE=default
      - cd backend/infrastructure/cdk
      - npx cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_REGION} || true
      - cd ../../..
      
  build:
    commands:
      - echo "Deploying infrastructure..."
      - chmod +x scripts/deploy.sh
      - ./scripts/deploy.sh
      
  post_build:
    commands:
      - echo "Deployment completed successfully!"
      - cat amplify-url.txt || echo "Amplify URL not found"

artifacts:
  files:
    - amplify-url.txt
    - backend/infrastructure/cdk/cdk.out/**/*
```

### Step 3: Store GitHub Token in Parameter Store

```bash
aws ssm put-parameter \
  --name "/respawn/github-token" \
  --value "your-github-token" \
  --type "SecureString" \
  --region us-east-1
```

### Step 4: Update CodeBuild IAM Role

Add the following permissions to the CodeBuild service role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "lambda:*",
        "apigateway:*",
        "bedrock:*",
        "aoss:*",
        "amplify:*",
        "iam:*",
        "logs:*",
        "s3:*",
        "ssm:GetParameter"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 5: Start Build

```bash
# Start build via CLI
aws codebuild start-build --project-name respawn-chatbot-deploy

# Or use the AWS Console
# Go to CodeBuild → Build projects → respawn-chatbot-deploy → Start build
```

### Step 6: Monitor Build

```bash
# Get latest build ID
BUILD_ID=$(aws codebuild list-builds-for-project \
  --project-name respawn-chatbot-deploy \
  --query 'ids[0]' --output text)

# Watch build logs
aws codebuild batch-get-builds --ids ${BUILD_ID}
```

---

## Post-Deployment Configuration

After deploying with any method, complete these steps:

### 1. Enable Bedrock Model Access

```bash
# This must be done via AWS Console
# Go to: Amazon Bedrock → Model access → Manage model access
# Enable:
#   - Amazon Nova Lite (or your chosen LLM)
#   - Titan Embeddings G1 - Text v2
```

### 2. Start Knowledge Base Ingestion

```bash
# Get Knowledge Base ID from deployment outputs
KB_ID="your-knowledge-base-id"

# List data sources
aws bedrock-agent list-data-sources \
  --knowledge-base-id ${KB_ID} \
  --region us-east-1

# Get data source ID from output
DATA_SOURCE_ID="your-data-source-id"

# Start ingestion job
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id ${KB_ID} \
  --data-source-id ${DATA_SOURCE_ID} \
  --region us-east-1

# Monitor ingestion progress
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id ${KB_ID} \
  --data-source-id ${DATA_SOURCE_ID} \
  --region us-east-1
```

### 3. Configure Amplify Environment Variables

```bash
# Get Amplify App ID from deployment outputs
APP_ID="your-amplify-app-id"

# Get API Gateway URL from deployment outputs
API_URL="your-api-gateway-url"

# Update Amplify environment variable
aws amplify update-app \
  --app-id ${APP_ID} \
  --environment-variables NEXT_PUBLIC_API_URL=${API_URL} \
  --region us-east-1

# Trigger new build
aws amplify start-job \
  --app-id ${APP_ID} \
  --branch-name main \
  --job-type RELEASE \
  --region us-east-1
```

### 4. Test the Application

```bash
# Get Amplify URL
AMPLIFY_URL=$(cat amplify-url.txt)
echo "Application URL: ${AMPLIFY_URL}"

# Test API health endpoint
API_URL="your-api-gateway-url"
curl ${API_URL}/health

# Test chat endpoint
curl -X POST ${API_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "language": "en"}'
```

---

## Troubleshooting

### Common Issues

**Issue: CDK Bootstrap Fails**
```bash
# Solution: Ensure you have admin permissions
aws sts get-caller-identity
# Verify your account ID and permissions
```

**Issue: Amplify Build Fails**
```bash
# Solution: Check Amplify build logs
aws amplify list-jobs --app-id ${APP_ID} --branch-name main
# Get the job ID and check logs
aws amplify get-job --app-id ${APP_ID} --branch-name main --job-id ${JOB_ID}
```

**Issue: Lambda Timeout**
```bash
# Solution: Increase timeout in CDK stack
# Edit: backend/infrastructure/cdk/lib/adaptive-gaming-chatbot-stack.ts
# Change: timeout: cdk.Duration.seconds(60) to higher value
```

**Issue: Knowledge Base Not Returning Results**
```bash
# Solution: Verify ingestion completed
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id ${KB_ID} \
  --data-source-id ${DATA_SOURCE_ID} \
  --region us-east-1
# Check status is COMPLETE
```

---

## Clean Up

To remove all deployed resources:

```bash
# Destroy CDK stack
cd backend/infrastructure/cdk
npx cdk destroy

# Delete Amplify app (if needed)
aws amplify delete-app --app-id ${APP_ID}

# Delete Parameter Store values (if using CodeBuild)
aws ssm delete-parameter --name "/respawn/github-token"
```

---

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)

---

**For support, contact: ai-cic@amazon.com**
