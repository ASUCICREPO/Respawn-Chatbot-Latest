# ReSpawn - Adaptive Gaming ChatBot

A comprehensive AI-powered chatbot application that provides intelligent guidance and support for adaptive gaming in therapy and rehabilitation settings, powered by AWS Bedrock Knowledge Base and cutting-edge AI technologies.

## Demo

Watch the full walkthrough of ReSpawn – Adaptive Gaming ChatBot in action:

https://github.com/user-attachments/assets/a725c03d-ba6c-4e51-932b-491a3ff2527f

## Disclaimers
Customers are responsible for making their own independent assessment of the information in this document.

This document:

(a) is for informational purposes only,

(b) references AWS product offerings and practices, which are subject to change without notice,

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided "as is" without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers, and

(d) is not to be considered a recommendation or viewpoint of AWS.

Additionally, you are solely responsible for testing, security and optimizing all code and assets on GitHub repo, and all such code and assets should be considered:

(a) as-is and without warranties or representations of any kind,

(b) not suitable for production environments, or on production or other critical data, and

(c) to include shortcuts in order to support rapid prototyping such as, but not limited to, relaxed authentication and authorization and a lack of strict adherence to security best practices.

All work produced is open source. More information can be found in the GitHub repo.

## Index

- [Overview](#overview)
- [Live Demo](#live-demo)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Post-Deployment Setup](#post-deployment-setup)
- [Usage](#usage)
- [Infrastructure](#infrastructure)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Credits](#credits)
- [License](#license)

## Overview

ReSpawn is an intelligent chatbot designed to assist therapists, rehabilitation specialists, and healthcare professionals in implementing adaptive gaming solutions for patients with physical limitations. The application combines natural language processing with AWS Bedrock Knowledge Base to deliver accurate, context-aware responses in both English and Spanish.

Built on a serverless architecture with real-time streaming communication, secure knowledge base integration, and an intuitive chat interface, ReSpawn makes adaptive gaming guidance accessible and actionable.




### Key Features

- **Multi-Language Support**: Seamless English and Spanish conversation with automatic language detection
- **AWS Bedrock Knowledge Base Integration**: Powered by Amazon Nova Lite and Titan embeddings for intelligent responses
- **Real-time Streaming Responses**: Server-sent events (SSE) for smooth, progressive answer delivery
- **Contextual Conversation Memory**: Maintains conversation history across sessions for coherent multi-turn dialogues
- **Intelligent FAQ System**: Pre-loaded with 10 common adaptive gaming questions in both languages
- **Web Crawler Data Source**: Automatically ingests and indexes content from specified URLs
- **Responsive Chat Interface**: Modern Next.js frontend with floating chat widget
- **Serverless Architecture**: Fully managed AWS infrastructure with API Gateway, Lambda, and OpenSearch Serverless

## Architecture

![Architecture Diagram](documents/AdaptiveGamingBotArc.jpg)

The application implements a serverless, event-driven architecture with AWS Bedrock at its core:

### Core Components

1. **Frontend (Next.js + React + TypeScript)**
   - Responsive chat widget with floating button interface
   - Real-time streaming message display
   - Language toggle (EN/ES)
   - FAQ sidebar with collapsible panel
   - Conversation state management

2. **Backend (AWS Lambda + Python)**
   - RESTful API endpoints (`/api/chat`, `/health`)
   - Bedrock Agent Runtime integration
   - Conversation session management
   - Language-aware prompt engineering

3. **Knowledge Base (AWS Bedrock + OpenSearch Serverless)**
   - Vector embeddings using Amazon Titan
   - Web crawler data source for content ingestion
   - Semantic search and retrieval
   - RAG (Retrieval Augmented Generation) pipeline

4. **Infrastructure (AWS CDK + TypeScript)**
   - Infrastructure as Code for reproducible deployments
   - API Gateway HTTP API with CORS support
   - CloudWatch Logs for monitoring
   - AWS Amplify for frontend hosting

### Data Flow

1. User submits a question through the chat interface
2. Frontend sends POST request to API Gateway `/api/chat` endpoint
3. Lambda function receives request and calls Bedrock Agent Runtime
4. Bedrock retrieves relevant context from Knowledge Base (OpenSearch Serverless)
5. LLM generates response using retrieved context and conversation history
6. Response streams back to frontend via Server-Sent Events (SSE)
7. Chat widget displays formatted response with suggestions

## Technology Stack

### Frontend
- **Framework**: Next.js 16.1.6 (React 19.2.3)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **Build Tool**: Vite
- **Deployment**: AWS Amplify Hosting

### Backend
- **Runtime**: Python 3.11
- **Framework**: AWS Lambda
- **API**: API Gateway HTTP API
- **AI/ML**: AWS Bedrock (Nova Lite, Titan Embeddings)
- **Vector Store**: OpenSearch Serverless

### Infrastructure
- **IaC**: AWS CDK 2.175.0
- **Language**: TypeScript
- **Services**: Lambda, API Gateway, Bedrock, OpenSearch Serverless, Amplify, CloudWatch

## Prerequisites

Before deploying or running locally, ensure you have the required tools and accounts.

### Quick Prerequisites Checklist

- **Node.js**: v20 or higher
- **Python**: 3.11 or higher
- **AWS CLI**: v2.x configured with valid credentials
- **AWS CDK**: v2.175.0 or higher
- **Git**: For version control
- **AWS Account**: With Bedrock model access enabled
- **GitHub Account**: With Personal Access Token (repo scope)

### Detailed Setup Instructions

For complete installation and configuration instructions, including:
- Step-by-step tool installation for macOS, Linux, and Windows
- AWS account setup and credential configuration
- GitHub token creation
- Environment variable configuration
- Verification steps

See the **[Setup Guide](documents/SETUP_GUIDE.md)** for detailed instructions.

## Local Development

For local development and testing before deployment.

### Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/ASUCICREPO/Respawn-Chatbot-Latest.git
   cd Respawn-Chatbot-Latest
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your configuration
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend Setup** (in a new terminal)
   ```bash
   cd frontend
   npm install
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   npm run dev
   ```

4. **Test Locally**
   - Open `http://localhost:3000`
   - Click the chat button and test functionality

### Detailed Setup Instructions

For complete local development setup, including:
- Virtual environment configuration
- Dependency installation
- Environment variable setup
- Running backend and frontend servers
- Troubleshooting common issues

See the **[Setup Guide - Local Development Setup](documents/SETUP_GUIDE.md#local-development-setup)** section.

## Deployment

ReSpawn offers multiple deployment options to suit your needs:

### Quick Deployment (Recommended)

Use the automated deployment script for the fastest setup:

```bash
# Set environment variables
export AWS_PROFILE="your-aws-profile"
export AWS_REGION="us-east-1"
export AMPLIFY_REPOSITORY="https://github.com/ASUCICREPO/Respawn-Chatbot-Latest"
export AMPLIFY_OAUTH_TOKEN="your-github-token"
export WEB_CRAWL_SEED_URLS="https://www.gamingreadapted.com/,https://gameaccess.info/"
export AMPLIFY_BRANCH="main"

# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Deployment Options

Choose the deployment method that works best for you:

1. **Quick Deployment with Script** - Automated one-command deployment
2. **Manual Deployment** - Step-by-step control over the deployment process
3. **AWS CloudShell Deployment** - Deploy directly from AWS Console without local setup
4. **AWS CodeBuild Deployment** - Automated CI/CD pipeline for continuous deployment

### Detailed Deployment Guides

For comprehensive deployment instructions, see:
- **[Deployment Guide](documents/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions for all methods
- **[Setup Guide](documents/SETUP_GUIDE.md)** - Prerequisites and environment setup

### Quick Start

1. **Prerequisites**: AWS CLI, Node.js 20+, Python 3.11+, GitHub token
2. **Clone Repository**: `git clone https://github.com/ASUCICREPO/Respawn-Chatbot-Latest.git`
3. **Run Deployment**: `./scripts/deploy.sh` (after setting environment variables)
4. **Configure**: Enable Bedrock models and start Knowledge Base ingestion

### Deployment Outputs

After successful deployment, you'll receive:
- `HttpApiUrl`: Your API Gateway endpoint
- `KnowledgeBaseId`: Bedrock Knowledge Base ID
- `OpenSearchCollectionName`: OpenSearch Serverless collection name
- `AmplifyAppId`: Amplify application ID
- `AmplifyAppUrl`: Your live application URL (saved to `amplify-url.txt`)

## Post-Deployment Setup

After deploying the infrastructure, complete these essential configuration steps:

### Quick Post-Deployment Checklist

1. **Enable Bedrock Model Access** (AWS Console)
   - Go to Amazon Bedrock → Model access
   - Enable: Amazon Nova Lite and Titan Embeddings G1 - Text v2

2. **Start Knowledge Base Ingestion**
   ```bash
   # Get data source ID and start ingestion
   aws bedrock-agent list-data-sources --knowledge-base-id <KB_ID> --region us-east-1
   aws bedrock-agent start-ingestion-job --knowledge-base-id <KB_ID> --data-source-id <DS_ID> --region us-east-1
   ```

3. **Verify Amplify Deployment**
   - Check AWS Console → Amplify → adaptive-gaming-guide
   - Ensure build status is "Deployed"

4. **Test the Application**
   - Open the Amplify URL (from deployment outputs or `amplify-url.txt`)
   - Test chat functionality in both English and Spanish

### Detailed Instructions

For complete post-deployment configuration steps, including:
- Bedrock model access setup
- Knowledge Base ingestion monitoring
- Amplify environment variable configuration
- API endpoint testing
- Troubleshooting common issues

See the **[Deployment Guide - Post-Deployment Configuration](documents/DEPLOYMENT_GUIDE.md#post-deployment-configuration)** section.

## Usage

### Chat Interface

1. **Open Chat**: Click the floating chat button (bottom-right corner)
2. **Select Language**: Toggle between EN (English) and ES (Spanish)
3. **Ask Questions**: 
   - Click an FAQ question from the sidebar
   - Type your own question in the input field
4. **View Responses**: Responses stream in real-time with formatted sections:
   - Summary
   - Recommendations
   - Next questions (clickable suggestions)
5. **Continue Conversation**: Ask follow-up questions to maintain context
6. **Clear Chat**: Click the refresh icon to start a new conversation

## Infrastructure

### AWS Services Used

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **API Gateway** | HTTP API for frontend-backend communication | CORS enabled, CloudWatch logging |
| **Lambda** | Serverless compute for chat logic | Python 3.11, 1024MB memory, 30s timeout |
| **Bedrock** | AI/ML foundation models | Nova Lite (LLM), Titan Embeddings |
| **OpenSearch Serverless** | Vector database for embeddings | VECTORSEARCH collection, public access |
| **Amplify** | Frontend hosting and CI/CD | Auto-build on push, environment variables |
| **CloudWatch** | Logging and monitoring | 7-day retention for API and Lambda logs |
| **IAM** | Access control | Least-privilege roles for Lambda and Bedrock |

### Cost Considerations

- **Lambda**: Pay per request and compute time
- **API Gateway**: Pay per million requests
- **Bedrock**: Pay per input/output tokens
- **OpenSearch Serverless**: Pay per OCU (OpenSearch Compute Unit)
- **Amplify**: Pay per build minute and data transfer

Estimated monthly cost for moderate usage: $50-$150

### Security

- **API Gateway**: CORS configured for secure cross-origin requests
- **Lambda**: Execution role with minimal required permissions
- **Bedrock**: IAM-based access control
- **OpenSearch**: Network and encryption policies enforced
- **Secrets**: GitHub token stored securely in CloudFormation parameters (NoEcho)

## Project Structure

```
.
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # Next.js app router pages
│   │   ├── components/         # React components
│   │   │   └── chat/          # Chat widget component
│   │   └── types/             # TypeScript type definitions
│   ├── public/                # Static assets
│   │   ├── frontpage.jpg      # Landing page image
│   │   └── ReSpawn_logo.png   # Brand logo
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                     # Python backend (for local dev)
│   ├── app/
│   │   └── main.py            # FastAPI application
│   ├── requirements.txt
│   └── env.example
│
├── infrastructure/              # AWS CDK infrastructure
│   └── cdk/
│       ├── bin/
│       │   └── app.ts         # CDK app entry point
│       ├── lib/
│       │   └── adaptive-gaming-chatbot-stack.ts  # Main stack
│       ├── lambda/
│       │   └── ai-agent/      # Lambda function code
│       │       ├── handler.py
│       │       └── requirements.txt
│       ├── cdk.json
│       └── package.json
│
├── amplify.yml                  # Amplify build specification
├── documents/                   # Documentation assets
│   ├── AdaptiveGamingBotArc.jpg # Architecture diagram
│   └── Respawn Demo.mov         # Demo video
├── README.md
└── .gitignore
```

## Configuration

### Environment Variables

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
```

#### Backend (.env - for local development)
```env
PORT=8000
CORS_ORIGIN=http://localhost:3000
BEDROCK_KB_ID=your-knowledge-base-id
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
BEDROCK_MODEL_ARN=  # Optional override
```

#### Lambda (Set by CDK)
- `BEDROCK_KB_ID`: Knowledge Base ID
- `BEDROCK_MODEL_ID`: Model identifier
- `BEDROCK_MODEL_ARN`: Optional model ARN override
- `AWS_REGION`: Deployment region

### CDK Context (cdk.json)
```json
{
  "bedrockModelId": "amazon.nova-lite-v1:0",
  "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
}
```

## Troubleshooting

### Common Issues

#### 1. Bedrock Access Denied
**Error**: `AccessDeniedException: Could not access model`

**Solution**: Enable model access in Bedrock console (see Post-Deployment Setup)

#### 2. Knowledge Base Returns No Results
**Error**: Empty or generic responses

**Solution**: 
- Verify ingestion job completed successfully
- Check web crawler seed URLs are accessible
- Ensure OpenSearch index was created

#### 3. CORS Errors in Frontend
**Error**: `Access-Control-Allow-Origin` errors

**Solution**:
- Verify API Gateway CORS configuration
- Check `NEXT_PUBLIC_API_URL` environment variable
- Ensure Amplify environment variables are set

#### 4. Lambda Timeout
**Error**: Task timed out after 30 seconds

**Solution**:
- Increase Lambda timeout in CDK stack
- Optimize Bedrock query parameters
- Check Knowledge Base performance

#### 5. Amplify Build Fails
**Error**: Build fails during deployment

**Solution**:
- Check Amplify build logs
- Verify `amplify.yml` configuration
- Ensure `NEXT_PUBLIC_API_URL` is set in Amplify environment variables

### Debug Commands

```bash
# Check Lambda logs
aws logs tail /aws/lambda/AdaptiveGamingChatbotStack-AiAgentFn --follow

# Check API Gateway logs
aws logs tail /aws/apigateway/AdaptiveGamingChatbotStack-ChatApi --follow

# Test API endpoint
curl -X POST https://your-api-url/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "language": "en"}'

# Check Knowledge Base status
aws bedrock-agent get-knowledge-base \
  --knowledge-base-id <your-kb-id> \
  --region us-east-1
```

## Documentation

Comprehensive guides for setup, deployment, and configuration:

### Setup and Installation
- **[Setup Guide](documents/SETUP_GUIDE.md)** - Complete setup instructions for local development and AWS prerequisites
  - Local development environment setup
  - AWS account configuration
  - GitHub setup and token creation
  - Environment variable configuration
  - Verification steps and troubleshooting

### Deployment
- **[Deployment Guide](documents/DEPLOYMENT_GUIDE.md)** - Multiple deployment options with detailed instructions
  - Quick deployment with automated script
  - Manual step-by-step deployment
  - AWS CloudShell deployment (no local setup required)
  - AWS CodeBuild CI/CD deployment
  - Post-deployment configuration
  - Troubleshooting and cleanup

### Architecture and Design
- **[Architecture Diagram](documents/AdaptiveGamingBotArc.jpg)** - Visual representation of the system architecture
- **[Demo Video](https://github.com/user-attachments/assets/a725c03d-ba6c-4e51-932b-491a3ff2527f)** - Full walkthrough of the application

### Quick Links
- [Local Development Setup](documents/SETUP_GUIDE.md#local-development-setup)
- [AWS Account Setup](documents/SETUP_GUIDE.md#aws-account-setup)
- [Quick Deployment](documents/DEPLOYMENT_GUIDE.md#quick-deployment-with-script)
- [CloudShell Deployment](documents/DEPLOYMENT_GUIDE.md#aws-cloudshell-deployment)
- [CodeBuild Deployment](documents/DEPLOYMENT_GUIDE.md#aws-codebuild-deployment)
- [Post-Deployment Configuration](documents/DEPLOYMENT_GUIDE.md#post-deployment-configuration)

---

## Credits

This application was architected and developed by [Sayantika Paul](https://www.linkedin.com/in/sayantikapaul12/) and [Omdevsinh Zala](https://www.linkedin.com/in/omdevsinhzala/) with solutions architect [Arun Arunachalam](https://www.linkedin.com/in/arunarunachalam/), program manager [Thomas Orr](https://www.linkedin.com/in/thomas-orr/) and product manager [Rachel Hayden](https://www.linkedin.com/in/rachelhayden/). Thanks to the ASU Cloud Innovation Centre and Career Services' Technical and Project Management teams for their guidance and support.

## License

See [LICENSE](LICENSE) file for details.

---

**Built by Arizona State University's AI Cloud Innovation Center (AI CIC)**  
**Powered by AWS**
