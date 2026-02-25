# ReSpawn - Deployment Guide

This guide covers deploying ReSpawn using the automated script via AWS CloudShell and CodeBuild — no local tools required.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Using AWS CloudShell and CodeBuild](#deployment-using-aws-cloudshell-and-codebuild)
3. [Post-Deployment Setup](#post-deployment-setup)
4. [Updating the Knowledge Base ID](#updating-the-knowledge-base-id)
5. [Destroying the Stack](#destroying-the-stack)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- An AWS account with access to **CloudShell** and **CodeBuild**
- A **forked copy** of this repository on your GitHub account
- A **GitHub Personal Access Token** with `repo` scope
  - This token is used by both CodeBuild (to clone your repo) and Amplify (to pull code for frontend builds)
  - Create one at: https://github.com/settings/tokens → Generate new token (classic) → select `repo`
- **Bedrock model access** enabled (see Step 1 below)

---

## Deployment Using AWS CloudShell and CodeBuild

### Step 1: Enable Bedrock Model Access

This is a one-time manual step that must be done before deployment.

1. Go to **AWS Console → Amazon Bedrock → Model access**
2. Click **Manage model access**
3. Enable the following models:
   - **Amazon Nova Lite** — used for chat responses
   - **Titan Embeddings G1 - Text v2** — used for vector embeddings
4. Click **Save changes** and wait for status to show **Access granted**

### Step 2: Open AWS CloudShell

1. Log in to your AWS Console
2. Click the **CloudShell icon** (terminal icon) in the top navigation bar
3. Wait for the environment to initialize

### Step 3: Clone Your Forked Repository

Replace `<YOUR-USERNAME>` with your GitHub username:

```bash
git clone https://github.com/<YOUR-USERNAME>/Respawn-Chatbot-Latest && cd Respawn-Chatbot-Latest
```

### Step 4: Run the Deployment Script

The script prompts for all required values interactively — no environment variables to set manually:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

You will be prompted for:

| Prompt | Description | Example |
|--------|-------------|---------|
| GitHub repository URL | Your forked repo URL | `https://github.com/YOUR-USERNAME/Respawn-Chatbot-Latest` |
| GitHub Personal Access Token | Used by CodeBuild to clone the repo and by Amplify to pull code for frontend builds | `ghp_xxxxxxxxxxxx` |
| AWS Region | Deployment region | `us-east-1` |
| Git branch | Branch to deploy | `main` |
| Action | Deploy or destroy the stack | `deploy` |

After confirming, the script automatically:
1. Parses and validates your GitHub repository URL
2. Creates an IAM service role for CodeBuild with the required CDK deployment permissions
3. Creates a CodeBuild project with all variables pre-configured
4. Starts the build — CDK deploys the full stack inside CodeBuild

### Step 5: Monitor the Build

After the script completes, monitor your build in the AWS Console:

1. Go to **AWS Console → CodeBuild → Build projects**
2. Find your project — it will be named `ReSpawn-<timestamp>`
3. Click the project → click the running build to view live logs
4. The full deployment takes approximately **10–15 minutes**

The build deploys:
- **API Gateway** — HTTP API endpoint for the chat backend
- **Lambda function** — Python handler connecting to Bedrock
- **Amplify app** — hosts the Next.js frontend with auto-build on push

### Step 6: Get Your App URL

Once the build completes:

1. Go to **AWS Console → AWS Amplify → adaptive-gaming-guide**
2. Click your branch (e.g. `main`)
3. The app URL is shown at the top of the branch page
4. Wait for the Amplify build to finish (triggered automatically, ~2–3 minutes)

---

## Post-Deployment Setup

### 1. Create Your Knowledge Base

The Knowledge Base is created separately in the AWS Console:

1. Go to **Amazon Bedrock → Knowledge Bases → Create knowledge base**
2. Configure:
   - Name: `adaptive-gaming-guide-kb`
   - IAM role: Create a new role or use an existing one
   - Embedding model: **Titan Embeddings G1 - Text v2**
3. Add a data source:
   - Type: **Web Crawler**
   - Seed URLs:
     - `https://www.gamingreadapted.com/`
     - `https://gameaccess.info/`
4. Vector store: **Amazon OpenSearch Serverless** (create new)
5. Click **Create knowledge base**
6. Once created, note the **Knowledge Base ID** (e.g. `XNARQAQAFV`)

### 2. Sync the Knowledge Base

After creating the KB, start the web crawler ingestion:

1. Go to **Amazon Bedrock → Knowledge Bases → your KB**
2. Under **Data sources**, select your web crawler source
3. Click **Sync**
4. Wait for the sync to complete — status will show **Ready** (5–10 minutes)

### 3. Update the Lambda with Your Knowledge Base ID

After the KB is created, wire it to the Lambda function:

**Option A: AWS Console**
1. Go to **AWS Lambda → AdaptiveGamingChatbotStack-AiAgentFn**
2. Click **Configuration → Environment variables → Edit**
3. Update `BEDROCK_KB_ID` with your Knowledge Base ID
4. Click **Save**

**Option B: AWS CLI**
```bash
# Get the Lambda function name
FUNCTION_NAME=$(aws lambda list-functions \
  --query "Functions[?starts_with(FunctionName, 'AdaptiveGamingChatbotStack-AiAgentFn')].FunctionName | [0]" \
  --output text --region us-east-1)

# Update the environment variable
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --environment "Variables={BEDROCK_KB_ID=YOUR_KB_ID,BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0}" \
  --region us-east-1
```

### 4. Test the Application

```bash
# Get your API Gateway URL from CloudFormation outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name AdaptiveGamingChatbotStack \
  --query "Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue" \
  --output text --region us-east-1)

# Test health endpoint
curl $API_URL/health

# Test chat endpoint
curl -X POST $API_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "language": "en"}'
```

---

## Updating the Knowledge Base ID

If you need to update the KB ID after initial deployment (e.g. recreated the KB):

```bash
aws lambda update-function-configuration \
  --function-name <FUNCTION_NAME> \
  --environment "Variables={BEDROCK_KB_ID=<NEW_KB_ID>,BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0}" \
  --region us-east-1
```

---

## Destroying the Stack

To tear down all deployed resources, run the deployment script again and choose `destroy` when prompted:

```bash
./scripts/deploy.sh
# When prompted for Action: type "destroy"
```

Or manually via CDK:

```bash
# In CloudShell, from the repo root
cd backend/infrastructure/cdk
npm install
npx cdk destroy --region us-east-1
```

---

## Troubleshooting

**CodeBuild build fails at CDK bootstrap**
- Ensure the CodeBuild IAM role has `cloudformation:*`, `iam:*`, and `s3:*` permissions
- The script creates the role automatically — check IAM console for `ReSpawn-<timestamp>-service-role`

**Amplify build fails**
- Check build logs: **Amplify → adaptive-gaming-guide → your branch → build logs**
- Verify `NEXT_PUBLIC_API_URL` is set in Amplify environment variables (set automatically by CDK)

**Chat returns empty or error responses**
- Verify `BEDROCK_KB_ID` is set on the Lambda function
- Confirm the Knowledge Base sync completed successfully
- Check Lambda logs: **CloudWatch → Log groups → /aws/lambda/AdaptiveGamingChatbotStack-AiAgentFn**

**Lambda timeout errors**
- The Lambda timeout is set to 60 seconds
- If Bedrock responses are slow, check Knowledge Base sync status and OpenSearch collection health

**Bedrock access denied**
- Confirm model access is granted in **Amazon Bedrock → Model access**
- Allow a few minutes after granting access before retrying

---

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [AWS Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)

---

**For support, contact: ai-cic@amazon.com**
