# main.py
import os
import asyncio
import time
import hashlib
import re
import xml.sax.saxutils as saxutils
from typing import List, Tuple, Dict, Any
from fastapi import FastAPI, Form, Response, Request, HTTPException
from twilio.twiml.voice_response import VoiceResponse, Gather
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------
# FastAPI setup
# ---------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Disable gzip if present (Twilio prefers plain XML)
from fastapi.middleware.gzip import GZipMiddleware
for mw in list(app.user_middleware):
    if "gzip" in str(mw.cls).lower():
        app.user_middleware.remove(mw)

# ---------------------------
# Gemini / Env config
# ---------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

PUBLIC_URL = os.getenv(
    "PUBLIC_URL",
    " https://bee-hayes-mixture-photographers.trycloudflare.com"
)

# ---------------------------
# Context store (in-memory)
# ---------------------------
contexts: Dict[str, Dict[str, Any]] = {}
contexts_lock = asyncio.Lock()
CONTEXT_TTL = int(os.getenv("CONTEXT_TTL_SECONDS", "3600"))  # default 1 hour
MAX_EXCHANGES = int(os.getenv("MAX_EXCHANGES", "6"))  # keep last N exchanges per call

async def prune_contexts_loop():
    while True:
        now = time.time()
        async with contexts_lock:
            expired = [k for k, v in contexts.items() if now - v["last_updated"] > CONTEXT_TTL]
            for k in expired:
                print(f"🧹 Pruning context for CallSid={k}")
                del contexts[k]
        await asyncio.sleep(120)

@app.on_event("startup")
async def startup_tasks():
    asyncio.create_task(prune_contexts_loop())

# ---------------------------
# Helpers
# ---------------------------
def build_twiML_xml(response_obj: VoiceResponse) -> str:
    raw = str(response_obj).strip()
    header = ""
    body = raw
    if raw.startswith("<?xml"):
        idx = raw.find("?>")
        if idx != -1:
            header = raw[: idx + 2]
            body = raw[idx + 2 :].strip()
    if not body.startswith("<Response"):
        body = f"<Response>{body}</Response>"
    if not header:
        header = '<?xml version="1.0" encoding="UTF-8"?>'
    final = header + body
    final = final.strip()
    return final

def _trim_history(history: List[Tuple[str,str]]) -> List[Tuple[str,str]]:
    limit = MAX_EXCHANGES * 2
    if len(history) <= limit:
        return history
    return history[-limit:]

def add_to_context(call_sid: str, role: str, text: str):
    now = time.time()
    if call_sid not in contexts:
        contexts[call_sid] = {"history": [], "last_updated": now}
    contexts[call_sid]["history"].append((role, text))
    contexts[call_sid]["history"] = _trim_history(contexts[call_sid]["history"])
    contexts[call_sid]["last_updated"] = now

def get_context_history(call_sid: str) -> List[Tuple[str,str]]:
    if call_sid not in contexts:
        return []
    return contexts[call_sid]["history"]

def build_prompt_from_history(history: List[Tuple[str,str]], latest_user: str) -> str:
    system = (
        "You are a professional health expert. Answer in Hindi only. "
        "Be concise, clear, safety-aware, and keep responses under 80 words. "
        "If the user mentions alarming symptoms (chest pain, fainting, severe bleeding, difficulty breathing, sudden weakness/numbness), advise immediate medical attention."
    )
    parts = [system, "\n---Conversation---"]
    for role, text in history:
        if role.lower() == "user":
            parts.append(f"User: {text}")
        else:
            parts.append(f"Assistant: {text}")
    parts.append(f"User: {latest_user}")
    parts.append("\nAssistant:")
    prompt = "\n".join(parts)
    return prompt

async def get_ai_response_with_history(call_sid: str, user_text: str) -> str:
    history = get_context_history(call_sid)
    prompt = build_prompt_from_history(history, user_text)
    try:
        response = await asyncio.wait_for(model.generate_content_async(prompt), timeout=8)
        text = getattr(response, "text", None) or ""
        return text.strip() if text.strip() else "माफ़ कीजिए, मुझे उत्तर नहीं मिला।"
    except asyncio.TimeoutError:
        print(" Gemini timeout reached.")
        return "माफ़ कीजिए, सर्वर को उत्तर देने में समय लग गया। कृपया दोबारा पूछें।"
    except Exception as e:
        print(f" Gemini error: {e}")
        return "क्षमा करें, फिलहाल सर्वर में कोई तकनीकी समस्या आ गई है।"

# ---------------------------
# TwiML sanitizer (fixes XML-breaking chars and control chars)
# ---------------------------
_control_chars_re = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]')

def sanitize_for_twiML(text: str, max_len: int = 500) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len]
    # remove control characters
    text = _control_chars_re.sub("", text)
    # escape XML special chars (& < > " ')
    text = saxutils.escape(text)
    return text

# ---------------------------
# Endpoints
# ---------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/voice", response_class=Response)
async def handle_incoming_call(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid")
    caller = form.get("From")
    print(f"➡ /voice invoked, CallSid={call_sid}, From={caller}")

    if call_sid:
        async with contexts_lock:
            if call_sid not in contexts:
                contexts[call_sid] = {"history": [], "last_updated": time.time()}
                add_to_context(call_sid, "assistant", f"Starting call with caller {caller or 'unknown'}.")

    response = VoiceResponse()
    # greeting is static and safe, but sanitize anyway
    greeting = sanitize_for_twiML("नमस्ते! आपका स्वागत है एआई हेल्थ असिस्टेंट में। मैं आपकी किस तरह मदद कर सकती हूँ?")
    response.say(greeting, voice="Polly.Kajal-Neural", language="hi-IN")

    gather = Gather(
        input="speech",
        action=f"{PUBLIC_URL}/gather",
        language="hi-IN",
        speech_timeout="auto",
        timeout=6,
    )
    response.append(gather)
    response.redirect(f"{PUBLIC_URL}/voice")

    xml_str = build_twiML_xml(response)
    print("---- TwiML /voice ----")
    print(xml_str)
    print("----------------------")

    return Response(content=xml_str, media_type="text/xml")

@app.post("/gather", response_class=Response)
async def handle_speech_result(
    SpeechResult: str = Form(None),
    SpeechResultLanguage: str = Form("hi-IN"),
    CallSid: str = Form(None),
    request: Request = None
):
    print(f"➡ /gather invoked: CallSid={CallSid} SpeechResult={SpeechResult}")
    response = VoiceResponse()

    if not CallSid:
        print(" No CallSid provided — context will not be stored.")
    else:
        async with contexts_lock:
            if CallSid not in contexts:
                contexts[CallSid] = {"history": [], "last_updated": time.time()}

    if SpeechResult:
        if CallSid:
            async with contexts_lock:
                add_to_context(CallSid, "user", SpeechResult)

        ai_reply = await get_ai_response_with_history(CallSid or "no-call", SpeechResult)
        print(f" AI reply (raw): {ai_reply}")

        # SANITIZE before inserting into TwiML
        safe_reply = sanitize_for_twiML(ai_reply, max_len=500)
        print(f"AI reply (sanitized): {safe_reply}")

        response.say(safe_reply, voice="Polly.Kajal-Neural", language="hi-IN")
        response.pause(length=1)
        follow = sanitize_for_twiML("आप और क्या पूछना चाहेंगे?", max_len=200)
        response.say(follow, voice="Polly.Kajal-Neural", language="hi-IN")

        # store assistant reply in context (store raw ai_reply for context, not escaped)
        if CallSid:
            async with contexts_lock:
                add_to_context(CallSid, "assistant", ai_reply)

        gather = Gather(
            input="speech",
            action=f"{PUBLIC_URL}/gather",
            language="hi-IN",
            speech_timeout="auto",
            timeout=6,
        )
        response.append(gather)
        response.redirect(f"{PUBLIC_URL}/voice")
    else:
        fallback = sanitize_for_twiML("माफ़ कीजिए, मैं आपकी बात समझ नहीं पाई। कृपया दोबारा बोलिए।")
        response.say(fallback, voice="Polly.Kajal-Neural", language="hi-IN")
        response.redirect(f"{PUBLIC_URL}/voice")

    xml_str = build_twiML_xml(response)
    print("---- TwiML /gather ----")
    print(xml_str)
    print("------------------------")

    return Response(content=xml_str, media_type="text/xml")

@app.post("/status", response_class=Response)
async def call_status(CallSid: str = Form(None), CallStatus: str = Form(None)):
    print(f"➡ /status: CallSid={CallSid} CallStatus={CallStatus}")
    if not CallSid:
        return Response("No CallSid", media_type="text/plain")

    terminal_states = {"completed", "canceled", "failed", "busy", "no-answer"}
    if CallStatus and CallStatus.lower() in terminal_states:
        async def _remove():
            async with contexts_lock:
                if CallSid in contexts:
                    print(f" Removing context for CallSid={CallSid} due to status={CallStatus}")
                    del contexts[CallSid]
        asyncio.create_task(_remove())

    return Response("OK", media_type="text/plain")

@app.post("/debug", response_class=Response)
async def debug_request(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    print(" Raw Twilio Request Body:", body.decode(errors="ignore"))
    print(" Raw Twilio Request Headers:", headers)
    return Response("OK", media_type="text/plain")

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
