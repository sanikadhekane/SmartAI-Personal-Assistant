import os
import re
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string
from groq import Groq

app = Flask(__name__)

API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "openai/gpt-oss-20b"
client = Groq(api_key=API_KEY) if API_KEY else None
conversation_history = []

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SmartAI - Personal AI Assistant</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#f4f7fb;color:#172033}.app{width:100%;max-width:900px;margin:auto;min-height:100vh;background:#fff;display:flex;flex-direction:column}.header{background:#102a56;color:#fff;padding:18px 22px;display:flex;align-items:center;justify-content:space-between}.brand{display:flex;align-items:center;gap:12px}.logo{width:45px;height:45px;border-radius:12px;background:#2f80ed;display:flex;align-items:center;justify-content:center;font-size:23px;font-weight:bold}.brand h1{margin:0;font-size:21px}.brand p{margin:3px 0 0;font-size:11px;letter-spacing:1px;opacity:.8}.status{font-size:12px}.status-dot{display:inline-block;width:8px;height:8px;background:#35c759;border-radius:50%;margin-right:5px}.welcome{margin:18px;padding:20px;border-radius:15px;background:#eef5ff;border:1px solid #d9e8ff}.welcome h2{margin:0 0 8px;color:#102a56;font-size:20px}.welcome p{margin:0;color:#536174;line-height:1.5}.chat{flex:1;padding:0 18px 18px;overflow-y:auto;min-height:350px}.message-row{display:flex;margin:13px 0}.message-row.user{justify-content:flex-end}.message-row.ai{justify-content:flex-start}.message{max-width:82%;padding:12px 15px;border-radius:15px;line-height:1.5;white-space:pre-wrap;overflow-wrap:anywhere}.message.user{background:#2f80ed;color:#fff;border-bottom-right-radius:4px}.message.ai{background:#f0f3f8;color:#172033;border-bottom-left-radius:4px}.quick{padding:0 18px 12px}.quick-title{font-size:12px;color:#697586;margin-bottom:8px}.quick-buttons{display:flex;flex-wrap:wrap;gap:8px}.quick-buttons button{border:1px solid #d5dfed;background:#fff;color:#24466f;border-radius:20px;padding:8px 12px;cursor:pointer}.quick-buttons button:hover{background:#eef5ff}.input-area{padding:12px 18px 18px;border-top:1px solid #e5e9f0;background:#fff}.input-row{display:flex;gap:9px}#messageInput{flex:1;min-width:0;border:1px solid #ccd6e5;border-radius:12px;padding:13px;font-size:15px;outline:none}#messageInput:focus{border-color:#2f80ed}.send{border:0;background:#2f80ed;color:#fff;border-radius:12px;padding:0 20px;cursor:pointer;font-weight:bold}.send:hover{background:#1769c2}.bottom-buttons{margin-top:9px}.bottom-buttons button{border:1px solid #d5dfed;background:#fff;color:#4a596d;border-radius:9px;padding:8px 12px;cursor:pointer}@media(max-width:600px){.header{padding:15px}.brand h1{font-size:18px}.status{font-size:10px}.welcome{margin:12px;padding:16px}.chat{padding:0 12px 12px}.quick{padding:0 12px 10px}.input-area{padding:10px 12px 14px}.message{max-width:90%}.send{padding:0 15px}}
</style>
</head>
<body>
<div class="app">
<div class="header"><div class="brand"><div class="logo">AI</div><div><h1>SmartAI</h1><p>PERSONAL AI ASSISTANT</p></div></div><div class="status"><span class="status-dot"></span>Online</div></div>
<div class="welcome"><h2>Hello! I'm SmartAI 👋</h2><p>Ask me questions, calculate things, check date/time, ask about current information, or ask general questions.</p></div>
<div id="chat" class="chat"><div class="message-row ai"><div class="message ai">Hello! I am your Smart AI Personal Assistant. How can I help you?</div></div></div>
<div class="quick"><div class="quick-title">Quick questions</div><div class="quick-buttons"><button onclick="askQuick('What is Python?')">What is Python?</button><button onclick="askQuick('What is AI?')">What is AI?</button><button onclick="askQuick('What is MCA?')">What is MCA?</button><button onclick="askQuick('Calculate 25*4')">Calculate 25*4</button><button onclick="askQuick('What are the current affairs in India today?')">India current affairs</button></div></div>
<div class="input-area"><div class="input-row"><input id="messageInput" type="text" placeholder="Type your question..." autocomplete="off"><button class="send" onclick="sendMessage()">Send</button></div><div class="bottom-buttons"><button onclick="clearChat()">Clear Chat</button></div></div>
</div>
<script>
const input=document.getElementById('messageInput');const chat=document.getElementById('chat');
input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();sendMessage();}});
function addMessage(text,type){const row=document.createElement('div');row.className='message-row '+type;const msg=document.createElement('div');msg.className='message '+type;msg.textContent=text;row.appendChild(msg);chat.appendChild(row);chat.scrollTop=chat.scrollHeight;}
function askQuick(q){input.value=q;sendMessage();}
async function sendMessage(){const text=input.value.trim();if(!text)return;addMessage(text,'user');input.value='';const row=document.createElement('div');row.className='message-row ai';const loading=document.createElement('div');loading.className='message ai';loading.textContent='Thinking...';row.appendChild(loading);chat.appendChild(row);chat.scrollTop=chat.scrollHeight;try{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});const data=await r.json();row.remove();addMessage(data.answer||'Sorry, I could not get an answer.','ai');}catch(e){row.remove();addMessage('Sorry, I could not connect to the assistant.','ai');}}
async function clearChat(){try{await fetch('/clear',{method:'POST'});chat.innerHTML='';addMessage('Chat cleared. How can I help you?','ai');}catch(e){addMessage('Could not clear the chat.','ai');}}
</script>
</body>
</html>'''


def normalize(text):
    return " ".join(text.lower().strip().split())


def needs_fresh_information(text):
    t = normalize(text)
    phrases = [
        "today", "today's", "todays", "current", "currently", "current affairs",
        "latest", "recent", "recently", "news", "headline", "headlines",
        "real time", "realtime", "live", "this week", "this month", "this year",
        "what happened", "what's happening", "whats happening", "right now",
        "as of now", "up to date", "up-to-date", "2026", "weather", "temperature",
        "forecast", "gold price", "silver price", "petrol price", "diesel price",
        "stock price", "share price", "market price", "exchange rate", "usd to inr",
        "inr to usd", "score", "match result", "election result", "election results"
    ]
    return any(p in t for p in phrases)


def local_response(command):
    t = normalize(command)
    if t in {"hi", "hello", "hey", "hii", "hiii"}:
        return "Hello! I am SmartAI. How can I help you?"
    if "how are you" in t:
        return "I'm doing great and ready to help!"
    if t in {"date", "what is the date", "what's the date", "what is today's date", "whats today's date", "today date"}:
        return datetime.now().strftime("Today's date is %d %B %Y.")
    if t in {"yesterday", "what was yesterday's date"}:
        return (datetime.now() - timedelta(days=1)).strftime("Yesterday was %d %B %Y.")
    if t in {"tomorrow", "what is tomorrow's date"}:
        return (datetime.now() + timedelta(days=1)).strftime("Tomorrow is %d %B %Y.")
    if t in {"time", "what is the time", "what's the time", "current time", "what time is it"}:
        return datetime.now().strftime("The current time is %I:%M %p.")

    expression = None
    for prefix in ("calculate ", "solve ", "what is "):
        if t.startswith(prefix):
            candidate = t[len(prefix):].strip()
            if re.fullmatch(r"[0-9+\-*/(). %]+", candidate):
                expression = candidate
                break
    if expression is None and re.fullmatch(r"[0-9+\-*/(). %]+", t):
        expression = t
    if expression:
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"The answer is {result}."
        except Exception:
            return "I couldn't calculate that expression."
    return None


def ask_groq(command):
    global conversation_history
    if not client:
        return "The Groq API key is not configured on the server. Please check GROQ_API_KEY in Render."

    conversation_history.append({"role": "user", "content": command})
    recent = conversation_history[-8:]
    today = datetime.now().strftime("%d %B %Y")
    fresh = needs_fresh_information(command)

    system = {
        "role": "system",
        "content": (
            f"You are SmartAI, a helpful personal AI assistant. Today is {today}. "
            "Answer clearly and simply. Use recent conversation context for follow-ups. "
            "For questions about current, latest, recent, today, news, current affairs, "
            "live information, prices, weather, scores, or other time-sensitive facts, "
            "you MUST use the browser_search tool and base the answer on current web results. "
            "Do not claim old model knowledge is current. For current-affairs questions, "
            "search the requested country or region and the current date."
        )
    }

    try:
        if fresh:
            # Groq's built-in browser search documentation supports GPT-OSS 20B.
            # We explicitly enable the tool and require a search for freshness queries.
            response = client.chat.completions.create(
                model=MODEL,
                messages=[system] + recent,
                max_completion_tokens=1024,
                temperature=1,
                tool_choice="required",
                tools=[{"type": "browser_search"}]
            )
        else:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[system] + recent,
                max_completion_tokens=512,
                temperature=1
            )

        answer = response.choices[0].message.content or "Sorry, I couldn't generate an answer."
        conversation_history.append({"role": "assistant", "content": answer})
        return answer

    except Exception as error:
        print("Groq error:", repr(error))
        if fresh:
            return "I couldn't retrieve current web information right now. Please try again after the Groq API quota is available."
        return "Sorry, I couldn't connect to the assistant right now. Please try again after the Groq API quota is available."


def get_ai_response(message):
    message = message.strip()
    if not message:
        return "Please type a question."
    local = local_response(message)
    if local is not None:
        return local
    return ask_groq(message)


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    return jsonify({"answer": get_ai_response(message)})


@app.route("/clear", methods=["POST"])
def clear():
    conversation_history.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
