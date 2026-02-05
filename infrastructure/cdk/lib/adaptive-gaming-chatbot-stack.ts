import {
  Duration,
  RemovalPolicy,
  Stack,
  StackProps,
  CfnOutput,
  CfnResource,
  CfnParameter
} from "aws-cdk-lib";
import { Construct } from "constructs";
import * as amplify from "aws-cdk-lib/aws-amplify";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as apigwv2Integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";

/**
 * NOTE:
 * Bedrock Knowledge Bases + OpenSearch Serverless resources are currently best
 * modeled via L1 CloudFormation resources. This stack lays down the core API + Lambda
 * and placeholders for KB wiring; you’ll fill KB/OSS details once account/region
 * specifics are confirmed.
 */
export class AdaptiveGamingChatbotStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const bedrockModelArn = this.node.tryGetContext("bedrockModelArn") as string | undefined;

    const bedrockModelId =
      this.node.tryGetContext("bedrockModelId") ??
      // Default to a first-party Bedrock model that does NOT require AWS Marketplace subscription.
      "amazon.nova-lite-v1:0";

    const embeddingModelArn =
      this.node.tryGetContext("embeddingModelArn") ??
      `arn:aws:bedrock:${this.region}::foundation-model/amazon.titan-embed-text-v2:0`;

    const webSeedUrls = new CfnParameter(this, "WebCrawlSeedUrls", {
      type: "CommaDelimitedList",
      description: "Comma-delimited list of seed URLs for the Bedrock web crawler."
    });

    /**
     * Vector store: OpenSearch Serverless (VECTORSEARCH collection).
     * Using L1 resources to keep compatibility with the newest service features.
     */
    const collectionName = "adaptive-gaming-vector";
    const aossCollection = new CfnResource(this, "VectorCollection", {
      type: "AWS::OpenSearchServerless::Collection",
      properties: {
        Name: collectionName,
        Type: "VECTORSEARCH",
        Description: "Vector store for Adaptive Gaming Guide chatbot"
      }
    });

    const encryptionPolicy = new CfnResource(this, "VectorEncryptionPolicy", {
      type: "AWS::OpenSearchServerless::SecurityPolicy",
      properties: {
        Name: "adaptive-gaming-encryption",
        Type: "encryption",
        Policy: JSON.stringify({
          Rules: [{ ResourceType: "collection", Resource: [`collection/${collectionName}`] }],
          AWSOwnedKey: true
        })
      }
    });
    aossCollection.node.addDependency(encryptionPolicy);

    const networkPolicy = new CfnResource(this, "VectorNetworkPolicy", {
      type: "AWS::OpenSearchServerless::SecurityPolicy",
      properties: {
        Name: "adaptive-gaming-network",
        Type: "network",
        Policy: JSON.stringify([
          {
            Rules: [
              { ResourceType: "collection", Resource: [`collection/${collectionName}`] },
              { ResourceType: "dashboard", Resource: [`collection/${collectionName}`] }
            ],
            AllowFromPublic: true
          }
        ])
      }
    });
    aossCollection.node.addDependency(networkPolicy);

    // Role assumed by Bedrock Knowledge Base to read S3 and write to AOSS.
    const kbRole = new iam.Role(this, "BedrockKbRole", {
      assumedBy: new iam.ServicePrincipal("bedrock.amazonaws.com")
    });
    kbRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["aoss:APIAccessAll"],
        resources: ["*"]
      })
    );

    // Bedrock Knowledge Base (VECTOR) storing embeddings in OpenSearch Serverless.
    const kbVectorIndexName = "adaptive-gaming-index";
    const knowledgeBase = new CfnResource(this, "KnowledgeBase", {
      type: "AWS::Bedrock::KnowledgeBase",
      properties: {
        Name: "adaptive-gaming-guide-kb",
        RoleArn: kbRole.roleArn,
        KnowledgeBaseConfiguration: {
          Type: "VECTOR",
          VectorKnowledgeBaseConfiguration: {
            EmbeddingModelArn: embeddingModelArn
          }
        },
        StorageConfiguration: {
          Type: "OPENSEARCH_SERVERLESS",
          OpensearchServerlessConfiguration: {
            CollectionArn: aossCollection.getAtt("Arn").toString(),
            VectorIndexName: kbVectorIndexName,
            FieldMapping: {
              VectorField: "vector",
              TextField: "text",
              MetadataField: "metadata"
            }
          }
        }
      }
    });
    knowledgeBase.node.addDependency(aossCollection);

    // Data source: Web crawler (subdomains scope, rate limit 30, regex inclusion filter).
    const webDataSource = new CfnResource(this, "KnowledgeBaseWebDataSource", {
      type: "AWS::Bedrock::DataSource",
      properties: {
        Name: "adaptive-gaming-guide-web",
        KnowledgeBaseId: knowledgeBase.getAtt("KnowledgeBaseId").toString(),
        DataSourceConfiguration: {
          Type: "WEB",
          WebConfiguration: {
            SourceConfiguration: {
              UrlConfiguration: {
                SeedUrls: webSeedUrls.valueAsList.map((url) => ({ Url: url }))
              }
            },
            CrawlerConfiguration: {
              Scope: "SUBDOMAINS",
              CrawlerLimits: {
                RateLimit: 30
              },
              InclusionFilters: [".*\\.(mp4|mov|mkv|webm|flv|mpeg|mpg|wmv|3gp|avi)$"]
            }
          }
        }
      }
    });
    webDataSource.node.addDependency(knowledgeBase);

    // Allow the KB role to access the collection. (Simplified access policy)
    const accessPolicy = new CfnResource(this, "VectorAccessPolicy", {
      type: "AWS::OpenSearchServerless::AccessPolicy",
      properties: {
        Name: "adaptive-gaming-access",
        Type: "data",
        Policy: JSON.stringify([
          {
            Rules: [
              {
                ResourceType: "collection",
                Resource: [`collection/${collectionName}`],
                Permission: [
                  "aoss:DescribeCollectionItems",
                  "aoss:CreateCollectionItems",
                  "aoss:UpdateCollectionItems"
                ]
              },
              {
                ResourceType: "index",
                Resource: [`index/${collectionName}/*`],
                Permission: [
                  "aoss:DescribeIndex",
                  "aoss:CreateIndex",
                  "aoss:UpdateIndex",
                  "aoss:ReadDocument",
                  "aoss:WriteDocument"
                ]
              }
            ],
            Principal: [kbRole.roleArn]
          }
        ])
      }
    });
    accessPolicy.node.addDependency(aossCollection);

    const agentFn = new lambda.Function(this, "AiAgentFn", {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset("lambda/ai-agent"),
      handler: "handler.handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      logRetention: logs.RetentionDays.ONE_WEEK,
      environment: {
        BEDROCK_KB_ID: knowledgeBase.getAtt("KnowledgeBaseId").toString(),
        BEDROCK_MODEL_ID: bedrockModelId,
        BEDROCK_MODEL_ARN: bedrockModelArn?.trim() ? bedrockModelArn.trim() : ""
      }
    });

    // Lambda only queries Bedrock; no direct read access is needed.

    // Permissions for Bedrock Agent Runtime (KB retrieval+generation).
    agentFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate",
          "bedrock:InvokeModel",
          "bedrock:GetInferenceProfile",
          "bedrock:ListInferenceProfiles",
          // Some third-party models require a Marketplace subscription enablement step.
          "aws-marketplace:ViewSubscriptions",
          "aws-marketplace:Subscribe"
        ],
        resources: ["*"]
      })
    );

    const httpApi = new apigwv2.HttpApi(this, "ChatApi", {
      corsPreflight: {
        allowCredentials: false,
        allowHeaders: ["content-type"],
        allowMethods: [apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.GET, apigwv2.CorsHttpMethod.OPTIONS],
        allowOrigins: ["*"]
      }
    });

    const httpAccessLogs = new logs.LogGroup(this, "ChatApiAccessLogs", {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: RemovalPolicy.DESTROY
    });
    const defaultStage = httpApi.defaultStage?.node.defaultChild as apigwv2.CfnStage;
    if (defaultStage) {
      defaultStage.accessLogSettings = {
        destinationArn: httpAccessLogs.logGroupArn,
        format: JSON.stringify({
          requestId: "$context.requestId",
          httpMethod: "$context.httpMethod",
          path: "$context.path",
          status: "$context.status",
          responseLength: "$context.responseLength"
        })
      };
    }

    httpApi.addRoutes({
      path: "/api/chat",
      methods: [apigwv2.HttpMethod.POST],
      integration: new apigwv2Integrations.HttpLambdaIntegration(
        "ChatIntegration",
        agentFn
      )
    });

    const amplifyRepo = new CfnParameter(this, "AmplifyRepository", {
      type: "String",
      description: "Git repository URL for Amplify (e.g., https://github.com/org/repo)."
    });
    const amplifyOauthToken = new CfnParameter(this, "AmplifyOauthToken", {
      type: "String",
      noEcho: true,
      description: "OAuth token for Amplify to access the repository."
    });
    const amplifyBranchName = new CfnParameter(this, "AmplifyBranch", {
      type: "String",
      default: "main",
      description: "Git branch name for Amplify builds."
    });

    const amplifyRole = new iam.Role(this, "AmplifyServiceRole", {
      assumedBy: new iam.ServicePrincipal("amplify.amazonaws.com")
    });
    amplifyRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName("AdministratorAccess-Amplify")
    );

    const amplifyApp = new amplify.CfnApp(this, "AdaptiveGamingAmplifyApp", {
      name: "adaptive-gaming-guide",
      repository: amplifyRepo.valueAsString,
      oauthToken: amplifyOauthToken.valueAsString,
      platform: "WEB_COMPUTE",
      iamServiceRole: amplifyRole.roleArn,
      environmentVariables: [
        {
          name: "NEXT_PUBLIC_API_URL",
          value: httpApi.apiEndpoint
        }
      ]
    });

    new amplify.CfnBranch(this, "AdaptiveGamingAmplifyBranch", {
      appId: amplifyApp.attrAppId,
      branchName: amplifyBranchName.valueAsString,
      enableAutoBuild: true
    });

    httpApi.addRoutes({
      path: "/api/chat",
      methods: [apigwv2.HttpMethod.GET],
      integration: new apigwv2Integrations.HttpLambdaIntegration(
        "ChatGetIntegration",
        agentFn
      )
    });

    httpApi.addRoutes({
      path: "/health",
      methods: [apigwv2.HttpMethod.GET],
      integration: new apigwv2Integrations.HttpLambdaIntegration(
        "HealthIntegration",
        agentFn
      )
    });

    httpApi.addRoutes({
      path: "/",
      methods: [apigwv2.HttpMethod.GET],
      integration: new apigwv2Integrations.HttpLambdaIntegration(
        "RootIntegration",
        agentFn
      )
    });

    new CfnOutput(this, "HttpApiUrl", {
      value: httpApi.apiEndpoint
    });
    new CfnOutput(this, "KnowledgeBaseId", {
      value: knowledgeBase.getAtt("KnowledgeBaseId").toString()
    });
    new CfnOutput(this, "OpenSearchCollectionName", {
      value: collectionName
    });
    new CfnOutput(this, "AmplifyAppId", {
      value: amplifyApp.attrAppId
    });
  }
}


