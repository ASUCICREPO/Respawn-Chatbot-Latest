import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "access-control-allow-origin": "*",
        },
        "body": json.dumps(body),
    }


def build_prompt(message, language):
    if language == "es":
        return f"""IMPORTANTE: Debes responder ÚNICAMENTE en español, sin importar el idioma de la pregunta o del contenido de referencia. Si el contenido de referencia está en inglés, tradúcelo al español antes de responder. NUNCA incluyas texto en inglés en tu respuesta.

Usa la base de conocimiento como fuente principal. Si la base no contiene suficiente información, ofrece orientación general breve y pide un detalle adicional. No digas "no puedo ayudar".
Mantén la respuesta corta y precisa (máximo 6–8 líneas).
No incluyas "Action:", "Response:", ni texto de sistema. No uses Markdown (sin **, #, ni código). Texto plano.

Formato requerido (usa exactamente estos encabezados):
Resumen:
- 1–2 puntos breves.
Recomendaciones:
- 2–4 viñetas concretas.
Siguientes preguntas:
- 1–2 viñetas.

Pregunta del usuario: {message}

Responde completamente en español."""
    return f"""IMPORTANT: You must respond ONLY in English. If any reference content is in another language, translate it to English before responding.

Use the knowledge base as your primary source. If the KB lacks enough info, provide brief general guidance and ask one clarifying question. Do not say you cannot help.
Keep the response short and precise (max 6–8 lines).
Do not include "Action:", "Response:", or any system text. Do not use Markdown (no **, #, or code). Plain text only.

Required format (use these exact headings):
Summary:
- 1–2 brief points.
Recommendations:
- 2–4 concrete bullets.
Next questions:
- 1–2 bullets.

User question: {message}

Respond completely in English."""


def handler(event, _context):
    logger.info("Request received", extra={"path": event.get("rawPath"), "method": event.get("requestContext", {}).get("http", {}).get("method")})

    # Handle streaming endpoint
    if event.get("rawPath") == "/api/chat/stream":
        return handle_streaming_chat(event)

    if event.get("rawPath") in ("/", ""):
        return json_response(
            200,
            {
                "ok": True,
                "message": "Adaptive Gaming Guide API",
                "routes": {
                    "health": {"method": "GET", "path": "/health"},
                    "chat": {"method": "POST", "path": "/api/chat", "body": {"message": "string", "language": "en|es"}},
                    "chat_stream": {"method": "POST", "path": "/api/chat/stream", "body": {"message": "string", "language": "en|es"}},
                },
            },
        )

    if event.get("rawPath") == "/health":
        return json_response(200, {"ok": True})

    if event.get("rawPath") == "/api/chat" and event.get("requestContext", {}).get("http", {}).get("method") == "GET":
        return json_response(405, {"error": "Method Not Allowed", "hint": "Use POST /api/chat with JSON body."})

    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return json_response(400, {"error": "Invalid JSON body."})

    message = payload.get("message") if isinstance(payload.get("message"), str) else ""
    message = message.strip()
    conversation_id = payload.get("conversationId") if isinstance(payload.get("conversationId"), str) else None
    language = "es" if payload.get("language") == "es" else "en"

    if not message:
        return json_response(400, {"error": "`message` is required."})

    kb_id = os.getenv("BEDROCK_KB_ID", "")
    model_id = os.getenv("BEDROCK_MODEL_ID", "")
    model_arn_override = os.getenv("BEDROCK_MODEL_ARN", "")
    logger.info("Bedrock config", extra={"hasKbId": bool(kb_id), "hasModelId": bool(model_id), "hasModelArnOverride": bool(model_arn_override), "language": language, "conversationId": conversation_id})

    if not kb_id or not model_id:
        reply = f"Dijiste: {message}" if language == "es" else f"You said: {message}"
        return json_response(200, {"conversationId": conversation_id or str(uuid.uuid4()), "reply": reply})

    prompt = build_prompt(message, language)
    logger.info("Prompt prepared", extra={"preview": prompt[:240]})

    model_arn = model_arn_override or f"arn:aws:bedrock:{os.getenv('AWS_REGION')}::foundation-model/{model_id}"
    logger.info("Sending RetrieveAndGenerate", extra={"kbId": kb_id, "modelArn": model_arn, "sessionId": conversation_id})

    try:
        client = boto3.client("bedrock-agent-runtime")
        res = client.retrieve_and_generate(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn,
                },
            },
            sessionId=conversation_id,
        )
        reply = res.get("output", {}).get("text") or ("No tengo respuesta." if language == "es" else "No answer.")
        session_id = res.get("sessionId") or conversation_id or str(uuid.uuid4())
        logger.info("Bedrock response received", extra={"hasOutput": bool(res.get("output", {}).get("text")), "outputPreview": reply[:240], "sessionId": session_id})
        return json_response(200, {"conversationId": session_id, "reply": reply})
    except Exception as exc:
        logger.exception("Bedrock request failed", exc_info=exc)
        return json_response(500, {"error": "Bedrock request failed."})


def handle_streaming_chat(event):
    """Handle streaming chat requests with SSE format (simulated for API Gateway)"""
    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return json_response(400, {"error": "Invalid JSON body."})

    message = payload.get("message") if isinstance(payload.get("message"), str) else ""
    message = message.strip()
    conversation_id = payload.get("conversationId") if isinstance(payload.get("conversationId"), str) else None
    language = "es" if payload.get("language") == "es" else "en"

    if not message:
        return json_response(400, {"error": "`message` is required."})

    kb_id = os.getenv("BEDROCK_KB_ID", "")
    model_id = os.getenv("BEDROCK_MODEL_ID", "")
    
    if not kb_id or not model_id:
        reply = f"Dijiste: {message}" if language == "es" else f"You said: {message}"
        # Simulate streaming for echo response
        sse_events = []
        session_id = conversation_id or str(uuid.uuid4())
        sse_events.append(f"event: meta\ndata: {json.dumps({'conversationId': session_id})}\n\n")
        
        # Stream the reply word by word
        words = reply.split()
        for word in words:
            sse_events.append(f"event: delta\ndata: {json.dumps({'text': word + ' '})}\n\n")
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
            "body": "".join(sse_events)
        }

    prompt = build_prompt(message, language)
    model_arn = f"arn:aws:bedrock:{os.getenv('AWS_REGION')}::foundation-model/{model_id}"

    try:
        client = boto3.client("bedrock-agent-runtime")
        
        # Get the full response first (API Gateway doesn't support true streaming)
        res = client.retrieve_and_generate(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn,
                },
            },
            sessionId=conversation_id,
        )
        
        reply = res.get("output", {}).get("text") or ("No tengo respuesta." if language == "es" else "No answer.")
        session_id = res.get("sessionId") or conversation_id or str(uuid.uuid4())
        
        # Build SSE response - simulate streaming by breaking into words
        sse_events = []
        sse_events.append(f"event: meta\ndata: {json.dumps({'conversationId': session_id})}\n\n")
        
        # Stream word by word
        words = reply.split()
        for word in words:
            sse_events.append(f"event: delta\ndata: {json.dumps({'text': word + ' '})}\n\n")
        
        logger.info("Streaming response completed", extra={"textLength": len(reply), "sessionId": session_id})
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
            "body": "".join(sse_events)
        }
        
    except Exception as exc:
        logger.exception("Streaming request failed", exc_info=exc)
        error_event = f"event: error\ndata: {json.dumps({'error': 'Streaming failed'})}\n\n"
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",
            },
            "body": error_event
        }
