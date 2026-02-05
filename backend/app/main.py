import json
import logging
import os
import time
import uuid
from typing import Generator, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import JSONResponse, StreamingResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adaptive-gaming-backend")


class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None
    language: Optional[str] = "en"


def new_conversation_id() -> str:
    return str(uuid.uuid4())


def is_greeting(message: str) -> bool:
    cleaned = message.strip().lower()
    if not cleaned:
        return False
    return cleaned in {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "hola",
        "buenas",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
    }


def build_prompt(message: str, language: str, force_help: bool = False, mode: str = "default") -> str:
    refusal_guard = (
        "Si la pregunta es un saludo o es general, responde con un saludo breve, "
        "una frase corta ofreciendo ayuda y una sola pregunta de orientación. "
        "No incluyas información técnica ni detalles de la base de conocimiento."
        if language == "es"
        else "If the question is a greeting or general, respond with a brief greeting, "
        "one short offer of help, and one guiding question. Do not include technical details "
        "or knowledge-base content."
    )
    force_line = (
        "Debes responder de forma útil incluso si la pregunta es vaga. "
        "No uses frases de rechazo."
        if language == "es"
        else "You must provide a helpful response even if the question is vague. Avoid refusal language."
    )
    extra_policy = f"\n{refusal_guard}\n" + (f"{force_line}\n" if force_help else "")

    greeting_only = (
        "Este es un saludo. Ignora el contenido de la base de conocimiento y responde "
        "solo con un saludo breve, una frase de ayuda y una pregunta concreta para orientar."
        if language == "es"
        else "This is a greeting. Ignore knowledge-base content and respond only with a brief "
        "greeting, one helpful line, and one concrete guiding question."
    )

    if language == "es":
        return f"""IMPORTANTE: Debes responder ÚNICAMENTE en español. Si el contenido de referencia está en inglés, tradúcelo antes de responder. No incluyas texto en inglés.

Usa la base de conocimiento como fuente principal. Si la base no contiene suficiente información, ofrece orientación general breve y pide un detalle adicional. Nunca te niegues ni digas que no puedes ayudar.
La respuesta debe ser clara, bien redactada y breve (máximo 4–6 líneas).
No incluyas "Action:", "Response:", ni texto de sistema. No uses Markdown (sin **, #, ni código). Texto plano.
Si el usuario solo saluda o hace una pregunta muy general, responde solo con un saludo breve, una frase de ayuda y una pregunta concreta para guiar el tema. No incluyas contenido de la base de conocimiento en saludos.
Evita frases como "no puedo ayudar", "no tengo información" o "no estoy autorizado".
{extra_policy}
{greeting_only if mode == "greeting" else ""}

Formato requerido (usa exactamente estos encabezados):
Resumen:
- 1–2 puntos breves.
Recomendaciones:
- 2–3 viñetas concretas y accionables.
Siguientes preguntas:
- 2 viñetas relacionadas con la pregunta del usuario.

Pregunta del usuario: {message}

Responde completamente en español."""
    return f"""IMPORTANT: You must respond ONLY in English. If any reference content is in another language, translate it before responding.

Use the knowledge base as your primary source. If the KB lacks enough info, provide brief general guidance and ask one clarifying question. Never refuse or say you cannot help.
The response must be well-written and concise (max 4–6 lines).
Do not include "Action:", "Response:", or any system text. Do not use Markdown (no **, #, or code). Plain text only.
If the user only greets or asks a very general question, respond only with a brief friendly greeting, one helpful sentence, and a concrete guiding question. Do not include knowledge-base content in greetings.
Avoid phrases like "unable to assist", "cannot help", or "no information available".
{extra_policy}
{greeting_only if mode == "greeting" else ""}

Required format (use these exact headings):
Summary:
- 1–2 brief points.
Recommendations:
- 2–3 concrete, actionable bullets.
Next questions:
- 2 bullets related to the user’s question.

User question: {message}

Respond completely in English."""


def stream_reply(reply: str, conversation_id: Optional[str]) -> Generator[str, None, None]:
    # Stream SSE events so the UI can render tokens incrementally.
    yield f"event: meta\ndata: {json.dumps({'conversationId': conversation_id})}\n\n"
    for chunk in reply.split():
        yield f"event: delta\ndata: {json.dumps({'text': chunk + ' '})}\n\n"
        time.sleep(0.02)
    yield "event: done\ndata: {}\n\n"


def bedrock_client():
    return boto3.client("bedrock-agent-runtime")


def bedrock_runtime_client():
    return boto3.client("bedrock-runtime")


def build_greeting_prompt(message: str, language: str) -> str:
    if language == "es":
        return f"""Responde SOLO con un saludo breve, una frase corta explicando que eres la Guía de Juegos Adaptativos y una pregunta concreta para orientar.
Usa exactamente este formato y texto plano, sin Markdown.

Resumen:
Hola, soy tu Guía de Juegos Adaptativos.
Recomendaciones:
Puedo ayudarte con recomendaciones y configuración de juegos adaptativos.
Siguientes preguntas:
¿Qué tipo de jugador o paciente quieres apoyar?
¿Qué consola o juego estás usando?

Mensaje del usuario: {message}
"""
    return f"""Respond ONLY with a brief greeting, one short line explaining this is the Adaptive Gaming Guide, and one concrete guiding question.
Use this exact format and plain text only, no Markdown.

Summary:
Hello, I’m your Adaptive Gaming Guide.
Recommendations:
I can help with adaptive gaming recommendations and setup guidance.
Next questions:
What type of player or patient are you supporting?
Which console or game are you working with?

User message: {message}
"""


def build_general_fallback_prompt(message: str, language: str) -> str:
    if language == "es":
        return f"""Responde de forma útil y breve incluso si la base de conocimiento es insuficiente.
Usa el formato requerido y texto plano, sin Markdown.

Resumen:
- 1–2 puntos claros y breves.
Recomendaciones:
- 2–3 viñetas concretas.
Siguientes preguntas:
- 2 viñetas relacionadas con la pregunta del usuario.

Pregunta del usuario: {message}
"""
    return f"""Provide a helpful, concise response even if the knowledge base lacks details.
Use the required format and plain text only, no Markdown.

Summary:
- 1–2 clear, brief points.
Recommendations:
- 2–3 concrete bullets.
Next questions:
- 2 bullets related to the user’s question.

User question: {message}
"""


def call_model_simple(message: str, language: str, mode: str = "greeting") -> dict:
    model_id = os.getenv("BEDROCK_MODEL_ARN", "") or os.getenv("BEDROCK_MODEL_ID", "")
    if not model_id:
        reply = "Hola, ¿en qué puedo ayudarte?" if language == "es" else "Hi! How can I help?"
        return {"conversationId": None, "reply": reply}

    prompt = (
        build_greeting_prompt(message, language)
        if mode == "greeting"
        else build_general_fallback_prompt(message, language)
    )
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }
    client = bedrock_runtime_client()
    try:
        res = client.invoke_model(modelId=model_id, body=json.dumps(payload))
        body = json.loads(res["body"].read().decode("utf-8"))
        content = body.get("content") or []
        text = ""
        if isinstance(content, list) and content:
            text = content[0].get("text", "")
        reply = text.strip() or (
            "Hola, ¿en qué puedo ayudarte?" if language == "es" else "Hi! How can I help?"
        )
        return {"conversationId": None, "reply": reply}
    except Exception:
        logger.exception("Bedrock runtime call failed; using canned reply")
        reply = "Hola, ¿en qué puedo ayudarte?" if language == "es" else "Hi! How can I help?"
        return {"conversationId": None, "reply": reply}


def call_bedrock(
    message: str,
    conversation_id: Optional[str],
    language: str,
    force_help: bool = False,
    mode: str = "default",
) -> dict:
    kb_id = os.getenv("BEDROCK_KB_ID", "")
    model_id = os.getenv("BEDROCK_MODEL_ID", "")
    model_arn_override = os.getenv("BEDROCK_MODEL_ARN", "")
    region = os.getenv("AWS_REGION", "us-east-1")

    # Without KB/model config we fall back to a local echo-style reply.
    if not kb_id or not model_id:
        reply = f"Dijiste: {message}" if language == "es" else f"You said: {message}"
        return {"conversationId": conversation_id or new_conversation_id(), "reply": reply}

    prompt = build_prompt(message, language, force_help=force_help, mode=mode)
    model_arn = model_arn_override or f"arn:aws:bedrock:{region}::foundation-model/{model_id}"

    logger.info(
        "Calling Bedrock",
        extra={
            "kb_id": kb_id,
            "model_arn": model_arn,
            "session_id": conversation_id,
            "language": language,
        },
    )

    client = bedrock_client()
    request = {
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
        request["sessionId"] = conversation_id

    try:
        res = client.retrieve_and_generate(**request)
    except ClientError as exc:
        message_text = str(exc)
        if "Session with Id" in message_text and "is not valid" in message_text:
            request.pop("sessionId", None)
            res = client.retrieve_and_generate(**request)
        else:
            raise
    except Exception:
        logger.exception("Bedrock call failed; falling back to safe reply")
        reply = f"Dijiste: {message}" if language == "es" else f"You said: {message}"
        return {"conversationId": conversation_id or new_conversation_id(), "reply": reply}

    reply = res.get("output", {}).get("text") or (
        "No tengo respuesta." if language == "es" else "No answer."
    )
    session_id = res.get("sessionId") or conversation_id or new_conversation_id()
    return {"conversationId": session_id, "reply": reply}


def looks_like_refusal(text: str) -> bool:
    lowered = text.lower()
    patterns = [
        "unable to assist",
        "cannot assist",
        "can't assist",
        "cannot help",
        "can't help",
        "sorry, i am unable",
        "no puedo ayudar",
        "no puedo asist",
        "no tengo información",
    ]
    return any(pattern in lowered for pattern in patterns)


app = FastAPI()
cors_origin = os.getenv("CORS_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cors_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/chat")
def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="`message` is required.")
    language = "es" if req.language == "es" else "en"
    greeting = is_greeting(message)
    if greeting:
        result = call_model_simple(message, language, mode="greeting")
    else:
        result = call_bedrock(
            message,
            req.conversationId,
            language,
            force_help=False,
            mode="default",
        )
        if looks_like_refusal(result["reply"]):
            result = call_bedrock(message, None, language, force_help=True, mode="default")
            if looks_like_refusal(result["reply"]):
                result = call_model_simple(message, language, mode="general")
    return JSONResponse(content=result)


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    # Streaming path used by the frontend ChatWidget.
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="`message` is required.")
    language = "es" if req.language == "es" else "en"
    greeting = is_greeting(message)
    if greeting:
        result = call_model_simple(message, language, mode="greeting")
    else:
        result = call_bedrock(
            message,
            req.conversationId,
            language,
            force_help=False,
            mode="default",
        )
        if looks_like_refusal(result["reply"]):
            result = call_bedrock(message, None, language, force_help=True, mode="default")
            if looks_like_refusal(result["reply"]):
                result = call_model_simple(message, language, mode="general")
    return StreamingResponse(
        stream_reply(result["reply"], result["conversationId"]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform"},
    )
