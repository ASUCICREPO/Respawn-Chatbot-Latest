# ReSpawn - Setup Guide

Complete setup instructions for local development and AWS deployment prerequisites.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [AWS Account Setup](#aws-account-setup)
3. [GitHub Setup](#github-setup)
4. [Environment Configuration](#environment-configuration)
5. [Verification Steps](#verification-steps)

---

## Local Development Setup

### Prerequisites Installation

#### 1. Install Node.js (v20 or higher)

**macOS (using Homebrew):**
```bash
brew install node@20
node --version  # Should show v20.x.x
```

**Linux (using nvm):**
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
node --version
```

**Windows:**
- Download from [nodejs.org](https://nodejs.org/)
- Install the LTS version (v20.x.x)
- Verify: `node --version`

#### 2. Install Python 3.11

**macOS:**
```bash
brew install python@3.11
python3.11 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- Install Python 3.11.x
- Verify: `python --version`

#### 3. Install AWS CLI v2

**macOS:**
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
aws --version
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

**Windows:**
- Download from [AWS CLI installer](https://awscli.amazonaws.com/AWSCLIV2.msi)
- Run the installer
- Verify: `aws --version`

#### 4. Install AWS CDK

```bash
npm install -g aws-cdk
cdk --version  # Should show 2.175.0 or higher
```

#### 5. Install Git

**macOS:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt install git
```

**Windows:**
- Download from [git-scm.com](https://git-scm.com/)

Verify installation:
```bash
git --version
```

### Clone Repository

```bash
git clone https://github.com/ASUCICREPO/Respawn-Chatbot-Latest.git
cd Respawn-Chatbot-Latest
```

### Backend Setup

#### 1. Create Virtual Environment

```bash
cd backend
python3.11 -m venv .venv
```

#### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

```bash
cp env.example .env
```

Edit `.env` file:
```env
PORT=8000
CORS_ORIGIN=http://localhost:3000
BEDROCK_KB_ID=your-kb-id-here
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_MODEL_ARN=
```

#### 5. Run Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Configure Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Verify Local Setup

1. Open browser to `http://localhost:3000`
2. Click the chat button (bottom-right)
3. Type "Hello" and verify you get a response
4. Check backend logs for API calls

---

## AWS Account Setup

### 1. Create AWS Account

If you don't have an AWS account:
1. Go to [aws.amazon.com](https://aws.amazon.com/)
2. Click "Create an AWS Account"
3. Follow the registration process
4. Add payment method (required)

### 2. Configure AWS CLI Credentials

#### Option A: AWS SSO (Recommended for Organizations)

```bash
aws configure sso
# Follow the prompts:
# - SSO start URL: Your organization's SSO URL
# - SSO Region: us-east-1
# - Select your account and role
# - CLI default region: us-east-1
# - CLI output format: json
```

Login:
```bash
aws sso login --profile your-profile-name
export AWS_PROFILE=your-profile-name
```

#### Option B: IAM User Access Keys

```bash
aws configure
# Enter:
# - AWS Access Key ID: Your access key
# - AWS Secret Access Key: Your secret key
# - Default region: us-east-1
# - Default output format: json
```

### 3. Verify AWS Credentials

```bash
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### 4. Enable Bedrock Model Access

1. Log in to AWS Console
2. Navigate to Amazon Bedrock
3. Click "Model access" in the left sidebar
4. Click "Manage model access"
5. Enable the following models:
   - **Amazon Nova Lite** (or your preferred LLM)
   - **Titan Embeddings G1 - Text v2**
6. Click "Save changes"
7. Wait for status to change to "Access granted"

### 5. Verify Required Permissions

Your IAM user/role needs permissions for:
- CloudFormation (full access)
- Lambda (full access)
- API Gateway (full access)
- Bedrock (full access)
- OpenSearch Serverless (full access)
- Amplify (full access)
- IAM (create/update roles)
- CloudWatch Logs (create/write)
- S3 (CDK bootstrap bucket)

Recommended: Use `AdministratorAccess` policy for initial setup.

---

## GitHub Setup

### 1. Create GitHub Account

If you don't have a GitHub account:
1. Go to [github.com](https://github.com/)
2. Click "Sign up"
3. Follow the registration process

### 2. Fork Repository (Optional)

If you want to customize the code:
1. Go to [https://github.com/ASUCICREPO/Respawn-Chatbot-Latest](https://github.com/ASUCICREPO/Respawn-Chatbot-Latest)
2. Click "Fork" button
3. Select your account

### 3. Create Personal Access Token

Required for Amplify deployment:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Configure token:
   - Note: `ReSpawn Amplify Deployment`
   - Expiration: 90 days (or custom)
   - Scopes: Select `repo` (full control of private repositories)
4. Click "Generate token"
5. **Copy the token immediately** (you won't see it again)

Example token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 4. Store Token Securely

**For local deployment:**
```bash
export AMPLIFY_OAUTH_TOKEN="ghp_your_token_here"
```

**For AWS Parameter Store (CodeBuild):**
```bash
aws ssm put-parameter \
  --name "/respawn/github-token" \
  --value "ghp_your_token_here" \
  --type "SecureString" \
  --region us-east-1
```

---

## Environment Configuration

### Development Environment Variables

Create `.env` files for local development:

#### Backend `.env`
```env
# Server Configuration
PORT=8000
CORS_ORIGIN=http://localhost:3000

# AWS Bedrock Configuration
BEDROCK_KB_ID=XNARQAQAFV
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_MODEL_ARN=

# AWS Configuration (optional for local)
AWS_REGION=us-east-1
AWS_PROFILE=your-profile-name
```

#### Frontend `.env.local`
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Environment Variables

Set these for deployment:

```bash
# AWS Configuration
export AWS_PROFILE="your-aws-profile"
export AWS_REGION="us-east-1"

# GitHub Configuration
export AMPLIFY_REPOSITORY="https://github.com/ASUCICREPO/Respawn-Chatbot-Latest"
export AMPLIFY_OAUTH_TOKEN="ghp_your_token_here"
export AMPLIFY_BRANCH="main"

# Knowledge Base Configuration
export WEB_CRAWL_SEED_URLS="https://www.gamingreadapted.com/,https://gameaccess.info/"
```

### CDK Context Configuration

Edit `backend/infrastructure/cdk/cdk.json`:

```json
{
  "app": "npx ts-node --esm bin/app.ts",
  "context": {
    "bedrockModelId": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
  }
}
```

---

## Verification Steps

### 1. Verify Local Backend

```bash
# Start backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# In another terminal, test endpoints
curl http://localhost:8000/health
# Expected: {"ok": true}

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "language": "en"}'
# Expected: JSON response with conversationId and reply
```

### 2. Verify Local Frontend

```bash
# Start frontend
cd frontend
npm run dev

# Open browser to http://localhost:3000
# Click chat button
# Type "Hello" and verify response
```

### 3. Verify AWS Configuration

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check AWS region
aws configure get region

# List available Bedrock models
aws bedrock list-foundation-models --region us-east-1

# Verify Bedrock model access
aws bedrock get-foundation-model \
  --model-identifier us.anthropic.claude-sonnet-4-5-20250929-v1:0 \
  --region us-east-1
```

### 4. Verify CDK Setup

```bash
cd backend/infrastructure/cdk

# Install dependencies
npm install

# Verify CDK can synthesize
npx cdk synth

# Check for errors in output
```

### 5. Verify GitHub Token

```bash
# Test GitHub API access with token
curl -H "Authorization: token ghp_your_token_here" \
  https://api.github.com/user

# Expected: JSON with your GitHub user info
```

---

## Troubleshooting

### Issue: Python Virtual Environment Not Activating

**Solution:**
```bash
# Ensure Python 3.11 is installed
python3.11 --version

# Recreate virtual environment
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
```

### Issue: Node.js Version Mismatch

**Solution:**
```bash
# Use nvm to switch versions
nvm install 20
nvm use 20
node --version
```

### Issue: AWS CLI Not Found

**Solution:**
```bash
# Check installation
which aws

# If not found, reinstall
# macOS:
brew install awscli

# Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### Issue: CDK Bootstrap Fails

**Solution:**
```bash
# Ensure you have admin permissions
aws sts get-caller-identity

# Try manual bootstrap
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
npx cdk bootstrap aws://${AWS_ACCOUNT_ID}/us-east-1
```

### Issue: Bedrock Access Denied

**Solution:**
1. Go to AWS Console → Bedrock → Model access
2. Verify models are enabled
3. Wait 5-10 minutes for access to propagate
4. Retry your request

### Issue: GitHub Token Invalid

**Solution:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Check token hasn't expired
3. Verify `repo` scope is selected
4. Generate new token if needed

---

## Next Steps

After completing setup:

1. **For Local Development:**
   - Start backend: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
   - Start frontend: `cd frontend && npm run dev`
   - Open `http://localhost:3000`

2. **For AWS Deployment:**
   - Follow the [Deployment Guide](DEPLOYMENT_GUIDE.md)
   - Choose your preferred deployment method
   - Complete post-deployment configuration

3. **For Production:**
   - Review security best practices
   - Configure custom domain (optional)
   - Set up monitoring and alerts
   - Enable CloudWatch dashboards

---

## Additional Resources

- [AWS CLI Configuration Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
- [AWS CDK Getting Started](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
- [Node.js Installation Guide](https://nodejs.org/en/download/)

---

**For support, contact: ai-cic@amazon.com**
