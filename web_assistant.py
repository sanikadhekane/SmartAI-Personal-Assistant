import os
import re
import webbrowser
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string
from groq import Groq

app = Flask(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
conversation_history = []

HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartAI - Personal AI Assistant</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #eef3f8;
            color: #172033;
        }
        .app {
            max-width: 900px;
            margin: 0 auto;
            min-height: 100vh;
            background: white;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: #102a43;
            color: white;
            padding: 18px 20px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo {
            width: 45px;
            height: 45px;
            border-radius: 12px;
            background: #2f80ed;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 20px;
        }
        .title { font-size: 21px; font-weight: bold; }
        .subtitle { font-size: 11px; opacity: .75; letter-spacing: 1px; }
        .status {
            margin-top: 12px;
            font-size: 12px;
            color: #b8f2c8;
        }
        .welcome {
            margin: 18px;
            padding: 18px;
            border-radius: 14px;
            background: #eaf3ff;
            border: 1px solid #cfe3ff;
        }
        .welcome h2 { margin: 0 0 7px; font-size: 20px; }
        .welcome p { margin: 0; color: #52606d; font-size: 14px; }
        #chat {
            flex: 1;
            padding: 0 18px 18px;
            min-height: 420px;
            overflow-y: auto;
        }
        .message {
            margin: 10px 0;
            padding: 12px 14px;
            border-radius: 14px;
            max-width: 88%;
            white-space: pre-wrap;
            line-height: 1.45;
            font-size: 15px;
        }
        .user {
            margin-left: auto;
            background: #2f80ed;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .ai {
            margin-right: auto;
            background: #f0f4f8;
            color: #172033;
            border-bottom-left-radius: 4px;
        }
        .quick {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 0 18px 12px;
        }
        .quick button {
            white-space: nowrap;
            border: 1px solid #cbd5e1;
            background: white;
            padding: 9px 12px;
            border-radius: 20px;
            cursor: pointer;
        }
        .input-area {
            display: flex;
            gap: 8px;
            padding: 12px;
            border-top: 1px solid #e2e8f0;
            background: white;
            position: sticky;
            bottom: 0;
        }
        #question {
            flex: 1;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 13px;
            font-size: 15px;
            outline: none;
        }
        #send {
            border: none;
            border-radius: 12px;
            background: #2f80ed;
            color: white;
            padding: 0 18px;
            font-weight: bold;
            cursor: pointer;
        }
        .bottom {
            display: flex;
            gap: 8px;
            padding: 0 12px 12px;
        }
        .bottom button {
            flex: 1;
            border: none;
            border-radius: 10px;
            padding: 10px;
            cursor: pointer;
        }
        #clear { background: #edf2f7; }
        #exit { background: #fee2e2; color: #991b1b; }
        @media (max-width: 600px) {
            .title { font-size: 18px; }
            #chat { min-height: 48vh; }
            .message { max-width: 94%; }
        }
    </style>
</head>
<body>
<div class="app">
    <div class="header">
        <div class="brand">
            <div class="logo">AI</div>
            <div>
                <div class="title">SmartAI</div>
                <div class="subtitle">PERSONAL AI ASSISTANT</div>
            </div>
        </div>
        <div class="status">● Online</div>
    </div>

    <div class="welcome">
        <h2>Hello! I'm SmartAI 👋</h2>
        <p>Ask me questions, calculate things, check date/time, or ask general questions.</p>
    </div>

    <div id="chat">
        <div class="message ai">Hello! I am your Smart AI Personal Assistant. How can I help you?</div>
    </div>

    <div class="quick">
        <button onclick="quickAsk('What is Python?')">What is Python?</button>
        <button onclick="quickAsk('What is AI?')">What is AI?</button>
        <button onclick="quickAsk('What is MCA?')">What is MCA?</button>
        <button onclick="quickAsk('Calculate 25*4')">Calculate 25*4</button>
    </div>

    <div class="input-area">
        <input id="question" type="text" placeholder="Type your question..." autocomplete="off">
        <button id="send" onclick="sendQuestion()">Send</button>
    </div>

    <div class="bottom">
        <button id="clear" onclick="clearChat()">Clear Chat</button>
        <button id="exit" onclick="exitAssistant()">Exit</button>
    </div>
</div>

<script>
    const input = document.getElementById("question");
    const chat = document.getElementById("chat");

    input.addEventListener("keydown", function(e) {
        if (e.key === "Enter") sendQuestion();
    });

    function addMessage(text, type) {
        const div = document.createElement("div");
        div.className = "message " + type;
        div.textContent = text;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    }

    function quickAsk(text) {
        input.value = text;
        sendQuestion();
    }

    async function sendQuestion() {
        const question = input.value.trim();
        if (!question) return;

        addMessage(question, "user");
        input.value = "";

        const thinking = document.createElement("div");
        thinking.className = "message ai";
        thinking.textContent = "Thinking...";
        thinking.id = "thinking";
        chat.appendChild(thinking);
        chat.scrollTop = chat.scrollHeight;

        try {
            const response = await fetch("/ask", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({question: question})
            });

            const data = await response.json();
            thinking.remove();
            addMessage(data.answer, "ai");
        } catch (error) {
            thinking.remove();
            addMessage("Sorry, I couldn't connect to the assistant.", "ai");
        }
    }

    async function clearChat() {
        await fetch("/clear", {method: "POST"});
        chat.innerHTML = '<div class="message ai">Chat cleared. How can I help you?</div>';
    }

    function exitAssistant() {
        addMessage("You can close this browser tab now. Goodbye!", "ai");
    }
</script>
</body>
</html>
"""

def get_ai_response(user):
    global conversation_history
    command = user.lower().strip()

    if command in ["hi", "hello", "hey"]:
        return "Hello! How can I help you?"

    if "today" in command and "date" in command:
        return datetime.now().strftime("Today's date is %d %B %Y")

    if "yesterday" in command:
        return (datetime.now() - timedelta(days=1)).strftime(
            "Yesterday's date was %d %B %Y"
        )

    if "tomorrow" in command or "tommorrow" in command or "tommorrows" in command:
        return (datetime.now() + timedelta(days=1)).strftime(
            "Tomorrow's date will be %d %B %Y"
        )

    if "time" in command and "hour" in command:
        match = re.search(r"(\d+)\s*hours?", command)
        if match:
            hours = int(match.group(1))
            future_time = datetime.now() + timedelta(hours=hours)
            return future_time.strftime(
                f"The time after {hours} hour(s) will be %I:%M %p"
            )

    if "time" in command:
        return "The current time is " + datetime.now().strftime("%I:%M %p")

    if any(symbol in command for symbol in ["+", "-", "*", "/"]):
        try:
            expression = command.replace("what is", "")
            expression = expression.replace("calculate", "").strip()
            # Simple college-demo calculator
            if re.fullmatch(r"[0-9+\-*/(). %]+", expression):
                return str(eval(expression, {"__builtins__": {}}, {}))
        except:
            pass

    conversation_history.append({"role": "user", "content": user})

    try:
        # Use Groq browser search for questions that need fresh information.
        fresh_terms = [
            "today", "current", "currently", "latest", "recent",
            "news", "current affairs", "real time", "realtime",
            "this week", "this month", "2026", "price", "weather",
            "stock", "match", "score", "live"
        ]
        needs_web = any(term in command for term in fresh_terms)

        request_data = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are SmartAI, a helpful personal AI assistant. "
                        "Answer clearly and simply. Give student-friendly explanations. "
                        "Remember previous messages and use them to understand follow-up questions. "
                        "When browser search is available, use current web information for "
                        "time-sensitive questions and clearly distinguish current facts from older knowledge."
                    )
                }
            ] + conversation_history[-10:],
            "max_completion_tokens": 1024
        }

        if needs_web:
            request_data["tool_choice"] = "required"
            request_data["tools"] = [{"type": "browser_search"}]

        response = client.chat.completions.create(**request_data)

        answer = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": answer})
        return answer

    except Exception as e:
        print("Error:", e)
        return "Sorry, I couldn't connect to the AI service. Please check the internet connection or API key."

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please type a question."})

    answer = get_ai_response(question)
    return jsonify({"answer": answer})

@app.route("/clear", methods=["POST"])
def clear():
    global conversation_history
    conversation_history.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    print("======================================")
    print("        SmartAI Web Assistant")
    print("======================================")
    print("Open on this laptop: http://127.0.0.1:5000")
    print("For mobile, use your laptop's Wi-Fi IP address.")
    print("Keep this terminal running.")
    app.run(host="0.0.0.0", port=5000, debug=False)
