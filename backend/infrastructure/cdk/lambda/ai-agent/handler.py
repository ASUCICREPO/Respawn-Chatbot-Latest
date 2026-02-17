import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cache account ID
_account_id_cache = None


def get_account_id(context=None):
    """Get AWS account ID from Lambda context or STS"""
    global _account_id_cache
    if _account_id_cache:
        return _account_id_cache
    
    if context and hasattr(context, 'invoked_function_arn'):
        _account_id_cache = context.invoked_function_arn.split(":")[4]
        return _account_id_cache
    
    # Fallback to STS
    try:
        sts = boto3.client('sts')
        _account_id_cache = sts.get_caller_identity()['Account']
        return _account_id_cache
    except Exception:
        return ""


def get_model_arn(model_id, region, account_id="", model_arn_override=""):
    """Get the correct model ARN based on model ID format"""
    if model_arn_override:
        return model_arn_override
    
    if model_id.startswith("us.") or model_id.startswith("global."):
        # This is an inference profile ID
        return f"arn:aws:bedrock:{region}:{account_id}:inference-profile/{model_id}"
    else:
        # This is a foundation model ID
        return f"arn:aws:bedrock:{region}::foundation-model/{model_id}"


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "access-control-allow-origin": "*",
        },
        "body": json.dumps(body),
    }


def is_greeting(message):
    """Check if the message is a greeting"""
    greetings = [
        "hi", "hello", "hey", "hola", "buenos dias", "buenas tardes", 
        "good morning", "good afternoon", "good evening", "greetings",
        "howdy", "what's up", "whats up", "sup"
    ]
    msg_lower = message.lower().strip()
    # Check if message is just a greeting (less than 20 chars and contains greeting word)
    if len(msg_lower) < 20:
        return any(greeting in msg_lower for greeting in greetings)
    return False


def get_greeting_response(language):
    """Return a friendly greeting response"""
    if language == "es":
        return """¡Hola! Soy tu guía de juegos adaptativos. Estoy aquí para ayudarte a hacer que los videojuegos sean accesibles para personas con diferentes habilidades físicas.

Puedo ayudarte con:
- Seleccionar controladores adaptativos apropiados
- Configurar equipos de juego accesibles
- Encontrar juegos compatibles con tecnologías de asistencia
- Optimizar configuraciones para necesidades específicas de movilidad
- Conectar controladores a diferentes consolas

¿En qué puedo ayudarte hoy?"""
    
    return """Hello! I'm your Adaptive Gaming Guide. I'm here to help you make video games accessible for people with varying physical abilities.

I can assist you with:
- Selecting appropriate adaptive controllers
- Setting up accessible gaming equipment
- Finding games compatible with assistive technologies
- Optimizing setups for specific mobility needs
- Connecting controllers to different consoles

What can I help you with today?"""


def build_prompt(message, language):
    if language == "es":
        return f"""IMPORTANTE: Debes responder ÚNICAMENTE en español de manera profesional y amigable. Si el contenido de referencia está en inglés, tradúcelo al español antes de responder.

Eres un experto en juegos adaptativos y accesibilidad. Tu objetivo es proporcionar orientación clara, práctica y empática para hacer que los videojuegos sean accesibles.

INSTRUCCIONES:
1. Usa la base de conocimiento como fuente principal de información
2. Proporciona respuestas detalladas pero concisas
3. Sé específico con nombres de productos, técnicas y pasos cuando sea posible
4. Si la información es limitada, ofrece orientación general y haz preguntas de seguimiento relevantes
5. Mantén un tono profesional pero cálido y accesible
6. No uses Markdown. Solo texto plano con viñetas simples usando guiones (-)

FORMATO OBLIGATORIO - DEBES USAR EXACTAMENTE ESTA ESTRUCTURA:

Resumen:
- [Punto clave 1 que responde directamente a la pregunta]
- [Punto clave 2 con información específica y práctica]
- [Punto clave 3 si es relevante]

Recomendaciones:
- [Recomendación concreta y accionable 1]
- [Recomendación concreta y accionable 2]
- [Recomendación concreta y accionable 3]
- [Recomendación concreta y accionable 4 si es relevante]

Siguientes preguntas:
- [Pregunta de seguimiento relevante 1]
- [Pregunta de seguimiento relevante 2]

Pregunta del usuario: {message}

RECUERDA: Debes usar EXACTAMENTE los encabezados "Resumen:", "Recomendaciones:", y "Siguientes preguntas:" seguidos de viñetas con guiones. No omitas ninguna sección."""
    
    return f"""IMPORTANT: You must respond ONLY in English in a professional and friendly manner. If reference content is in another language, translate it to English before responding.

You are an expert in adaptive gaming and accessibility. Your goal is to provide clear, practical, and empathetic guidance to make video games accessible.

INSTRUCTIONS:
1. Use the knowledge base as your primary source of information
2. Provide detailed but concise responses
3. Be specific with product names, techniques, and steps when possible
4. If information is limited, offer general guidance and ask relevant follow-up questions
5. Maintain a professional yet warm and approachable tone
6. Do not use Markdown. Plain text only with simple bullet points using dashes (-)

MANDATORY FORMAT - YOU MUST USE EXACTLY THIS STRUCTURE:

Summary:
- [Key point 1 that directly answers the question]
- [Key point 2 with specific and practical information]
- [Key point 3 if relevant]

Recommendations:
- [Concrete and actionable recommendation 1]
- [Concrete and actionable recommendation 2]
- [Concrete and actionable recommendation 3]
- [Concrete and actionable recommendation 4 if relevant]

Next questions:
- [Relevant follow-up question 1]
- [Relevant follow-up question 2]

User question: {message}

REMEMBER: You MUST use EXACTLY the headings "Summary:", "Recommendations:", and "Next questions:" followed by bullet points with dashes. Do not omit any section."""


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

    # Handle greetings with a friendly welcome message
    if is_greeting(message):
        greeting_reply = get_greeting_response(language)
        return json_response(200, {"conversationId": conversation_id or str(uuid.uuid4()), "reply": greeting_reply})

    kb_id = os.getenv("BEDROCK_KB_ID", "")
    model_id = os.getenv("BEDROCK_MODEL_ID", "")
    model_arn_override = os.getenv("BEDROCK_MODEL_ARN", "")
    logger.info("Bedrock config", extra={"hasKbId": bool(kb_id), "hasModelId": bool(model_id), "hasModelArnOverride": bool(model_arn_override), "language": language, "conversationId": conversation_id})

    if not kb_id or not model_id:
        reply = f"Dijiste: {message}" if language == "es" else f"You said: {message}"
        return json_response(200, {"conversationId": conversation_id or str(uuid.uuid4()), "reply": reply})

    prompt = build_prompt(message, language)
    logger.info("Prompt prepared", extra={"preview": prompt[:240]})

    account_id = get_account_id(_context)
    model_arn = get_model_arn(model_id, os.getenv('AWS_REGION', 'us-east-1'), account_id, model_arn_override)
    logger.info("Sending RetrieveAndGenerate", extra={"kbId": kb_id, "modelArn": model_arn, "sessionId": conversation_id})

    try:
        client = boto3.client("bedrock-agent-runtime")
        
        # Build request parameters - only include sessionId if it exists
        request_params = {
            "input": {"text": prompt},
            "retrieveAndGenerateConfiguration": {
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn,
                },
            },
        }
        
        if conversation_id:
            request_params["sessionId"] = conversation_id
        
        res = client.retrieve_and_generate(**request_params)
        reply = res.get("output", {}).get("text") or ("No tengo respuesta." if language == "es" else "No answer.")
        session_id = res.get("sessionId") or conversation_id or str(uuid.uuid4())
        logger.info("Bedrock response received", extra={"hasOutput": bool(res.get("output", {}).get("text")), "outputPreview": reply[:240], "sessionId": session_id})
        return json_response(200, {"conversationId": session_id, "reply": reply})
    except client.exceptions.ValidationException as exc:
        # Handle invalid/expired session ID - retry without session ID
        error_msg = str(exc)
        if "Session with Id" in error_msg and "is not valid" in error_msg:
            logger.warning("Invalid session ID, retrying without session", extra={"oldSessionId": conversation_id})
            try:
                # Retry without session ID to start a new conversation
                request_params_retry = {
                    "input": {"text": prompt},
                    "retrieveAndGenerateConfiguration": {
                        "type": "KNOWLEDGE_BASE",
                        "knowledgeBaseConfiguration": {
                            "knowledgeBaseId": kb_id,
                            "modelArn": model_arn,
                        },
                    },
                }
                res = client.retrieve_and_generate(**request_params_retry)
                reply = res.get("output", {}).get("text") or ("No tengo respuesta." if language == "es" else "No answer.")
                session_id = res.get("sessionId") or str(uuid.uuid4())
                logger.info("Bedrock response received after retry", extra={"newSessionId": session_id})
                return json_response(200, {"conversationId": session_id, "reply": reply})
            except Exception as retry_exc:
                logger.exception("Bedrock retry failed", exc_info=retry_exc)
                return json_response(500, {"error": "Bedrock request failed."})
        logger.exception("Bedrock validation error", exc_info=exc)
        return json_response(500, {"error": "Bedrock request failed."})
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

    # Handle greetings with a friendly welcome message
    if is_greeting(message):
        greeting_reply = get_greeting_response(language)
        # Simulate streaming for greeting
        sse_events = []
        session_id = conversation_id or str(uuid.uuid4())
        sse_events.append(f"event: meta\ndata: {json.dumps({'conversationId': session_id})}\n\n")
        
        # Stream the greeting word by word
        words = greeting_reply.split()
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
    account_id = get_account_id()
    model_arn = get_model_arn(model_id, os.getenv('AWS_REGION', 'us-east-1'), account_id)

    try:
        client = boto3.client("bedrock-agent-runtime")
        
        # Build request parameters - only include sessionId if it exists
        request_params = {
            "input": {"text": prompt},
            "retrieveAndGenerateConfiguration": {
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": kb_id,
                    "modelArn": model_arn,
                },
            },
        }
        
        if conversation_id:
            request_params["sessionId"] = conversation_id
        
        # Get the full response first (API Gateway doesn't support true streaming)
        res = client.retrieve_and_generate(**request_params)
        
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
        
    except client.exceptions.ValidationException as exc:
        # Handle invalid/expired session ID - retry without session ID
        error_msg = str(exc)
        if "Session with Id" in error_msg and "is not valid" in error_msg:
            logger.warning("Invalid session ID in streaming, retrying without session", extra={"oldSessionId": conversation_id})
            try:
                # Retry without session ID
                request_params_retry = {
                    "input": {"text": prompt},
                    "retrieveAndGenerateConfiguration": {
                        "type": "KNOWLEDGE_BASE",
                        "knowledgeBaseConfiguration": {
                            "knowledgeBaseId": kb_id,
                            "modelArn": model_arn,
                        },
                    },
                }
                res = client.retrieve_and_generate(**request_params_retry)
                reply = res.get("output", {}).get("text") or ("No tengo respuesta." if language == "es" else "No answer.")
                session_id = res.get("sessionId") or str(uuid.uuid4())
                
                # Build SSE response
                sse_events = []
                sse_events.append(f"event: meta\ndata: {json.dumps({'conversationId': session_id})}\n\n")
                words = reply.split()
                for word in words:
                    sse_events.append(f"event: delta\ndata: {json.dumps({'text': word + ' '})}\n\n")
                
                logger.info("Streaming response completed after retry", extra={"newSessionId": session_id})
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
            except Exception as retry_exc:
                logger.exception("Streaming retry failed", exc_info=retry_exc)
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
        logger.exception("Streaming validation error", exc_info=exc)
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
