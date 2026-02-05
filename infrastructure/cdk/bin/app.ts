#!/usr/bin/env node
import { App } from "aws-cdk-lib";
import { AdaptiveGamingChatbotStack } from "../lib/adaptive-gaming-chatbot-stack.js";

const app = new App();

new AdaptiveGamingChatbotStack(app, "AdaptiveGamingChatbotStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  }
});


