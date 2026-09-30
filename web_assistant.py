import os
import re
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template_string
from groq import Groq

app = Flask(__name__)

# API key must be stored in Render Environment Variables.
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("WARNING: GROQ_API_KEY is not set.")

client = Groq(api_key=api_key) if api_key else None

conversation_history = []

MODEL = "openai/gpt-oss-20b"


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SmartAI - Personal AI Assistant</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: #f4f7fb;
    color: #172033;
}

.app {
    width: 100%;
    max-width: 900px;
    margin: 0 auto;
    min-height: 100vh;
    background: white;
    display: flex;
    flex-direction: column;
}

.header {
    background: #102a56;
    color: white;
    padding: 18px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
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
    font-size: 23px;
    font-weight: bold;
}

.brand h1 {
    margin: 0;
    font-size: 21px;
}

.brand p {
    margin: 3px 0 0;
    font-size: 11px;
    letter-spacing: 1px;
    opacity: 0.8;
}

.status {
    font-size: 12px;
}

.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #35c759;
    border-radius: 50%;
    margin-right: 5px;
}

.welcome {
    margin: 18px;
    padding: 20px;
    border-radius: 15px;
    background: #eef5ff;
    border: 1px solid #d9e8ff;
}

.welcome h2 {
    margin: 0 0 8px;
    color: #102a56;
    font-size: 20px;
}

.welcome p {
    margin: 0;
    color: #536174;
    line-height: 1.5;
}

.chat {
    flex: 1;
    padding: 0 18px 18px;
    overflow-y: auto;
    min-height: 350px;
}

.message-row {
    display: flex;
    margin: 13px 0;
}

.message-row.user {
    justify-content: flex-end;
}

.message-row.ai {
    justify-content: flex-start;
}

.message {
    max-width: 82%;
    padding: 12px 15px;
    border-radius: 15px;
    line-height: 1.5;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.message.user {
    background: #2f80ed;
    color: white;
    border-bottom-right-radius: 4px;
}

.message.ai {
    background: #f0f3f8;
    color: #172033;
    border-bottom-left-radius: 4px;
}

.quick {
    padding: 0 18px 12px;
}

.quick-title {
    font-size: 12px;
    color: #697586;
    margin-bottom: 8px;
}

.quick-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.quick-buttons button {
    border: 1px solid #d5dfed;
    background: white;
    color: #24466f;
    border-radius: 20px;
    padding: 8px 12px;
    cursor: pointer;
}

.quick-buttons button:hover {
    background: #eef5ff;
}

.input-area {
    padding: 12px 18px 18px;
    border-top: 1px solid #e5e9f0;
    background: white;
}

.input-row {
    display: flex;
    gap: 9px;
}

#messageInput {
    flex: 1;
    min-width: 0;
    border: 1px solid #ccd6e5;
    border-radius: 12px;
    padding: 13px;
    font-size: 15px;
    outline: none;
}

#messageInput:focus {
    border-color: #2f80ed;
}

.send {
    border: none;
    background: #2f80ed;
    color: white;
    border-radius: 12px;
    padding: 0 20px;
    cursor: pointer;
    font-weight: bold;
}

.send:hover {
    background: #1769c2;
}

.bottom-buttons {
    margin-top: 9px;
}

.bottom-buttons button {
    border: 1px solid #d5dfed;
    background: white;
    color: #4a596d;
    border-radius: 9px;
    padding: 8px 12px;
    cursor: pointer;
}

@media (max-width: 600px) {

    .header {
        padding: 15px;
    }

    .brand h1 {
        font-size: 18px;
    }

    .status {
        font-size: 10px;
    }

    .welcome {
        margin: 12px;
        padding: 16px;
    }

    .chat {
        padding: 0 12px 12px;
    }

    .quick {
        padding: 0 12px 10px;
    }

    .input-area {
        padding: 10px 12px 14px;
    }

    .message {
        max-width: 90%;
    }

    .send {
        padding: 0 15px;
    }
}
</style>
</head>

<body>

<div class="app">

    <div class="header">

        <div class="brand">

            <div class="logo">AI</div>

            <div>
                <h1>SmartAI</h1>
                <p>PERSONAL AI ASSISTANT</p>
            </div>

        </div>

        <div class="status">
            <span class="status-dot"></span>Online
        </div>

    </div>


    <div class="welcome">

        <h2>Hello! I'm SmartAI 👋</h2>

        <p>
            Ask me questions, calculate things, check date/time,
            ask about current information, or ask general questions.
        </p>

    </div>


    <div id="chat" class="chat">

        <div class="message-row ai">

            <div class="message ai">
                Hello! I am your Smart AI Personal Assistant. How can I help you?
            </div>

        </div>

    </div>


    <div class="quick">

        <div class="quick-title">
            Quick questions
        </div>

        <div class="quick-buttons">

            <button onclick="askQuick('What is Python?')">
                What is Python?
            </button>

            <button onclick="askQuick('What is AI?')">
                What is AI?
            </button>

            <button onclick="askQuick('What is MCA?')">
                What is MCA?
            </button>

            <button onclick="askQuick('Calculate 25*4')">
                Calculate 25*4
            </button>

            <button onclick="askQuick('What are the current affairs in India today?')">
                India current affairs
            </button>

        </div>

    </div>


    <div class="input-area">

        <div class="input-row">

            <input
                id="messageInput"
                type="text"
                placeholder="Type your question..."
                autocomplete="off"
            >

            <button class="send" onclick="sendMessage()">
                Send
            </button>

        </div>


        <div class="bottom-buttons">

            <button onclick="clearChat()">
                Clear Chat
            </button>

        </div>

    </div>

</div>


<script>

const input = document.getElementById("messageInput");
const chat = document.getElementById("chat");


input.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();

    }

});


function addMessage(text, type) {

    const row = document.createElement("div");

    row.className = "message-row " + type;


    const message = document.createElement("div");

    message.className = "message " + type;

    message.textContent = text;


    row.appendChild(message);

    chat.appendChild(row);


    chat.scrollTop = chat.scrollHeight;

}


function askQuick(question) {

    input.value = question;

    sendMessage();

}


async function sendMessage() {

    const text = input.value.trim();


    if (!text) {

        return;

    }


    addMessage(text, "user");

    input.value = "";


    const loadingRow = document.createElement("div");

    loadingRow.className = "message-row ai";


    const loading = document.createElement("div");

    loading.className = "message ai";

    loading.textContent = "Thinking...";


    loadingRow.appendChild(loading);

    chat.appendChild(loadingRow);


    chat.scrollTop = chat.scrollHeight;


    try {

        const response = await fetch("/ask", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: text
            })

        });


        const data = await response.json();


        loadingRow.remove();


        addMessage(
            data.answer || "Sorry, I couldn't get an answer.",
            "ai"
        );


    } catch (error) {

        loadingRow.remove();


        addMessage(
            "Sorry, I couldn't connect to the assistant.",
            "ai"
        );

    }

}


async function clearChat() {

    try {

        await fetch("/clear", {
            method: "POST"
        });


        chat.innerHTML = "";


        addMessage(
            "Chat cleared. How can I help you?",
            "ai"
        );


    } catch (error) {

        addMessage(
            "Could not clear the chat.",
            "ai"
        );

    }

}

</script>

</body>
</html>
"""


def normalize_text(text):
    return " ".join(text.lower().strip().split())


def needs_fresh_information(command):

    text = normalize_text(command)

    fresh_phrases = [

        "today",
        "todays",
        "today's",

        "current",
        "currently",
        "current affairs",

        "latest",
        "recent",
        "recently",

        "news",
        "headline",
        "headlines",

        "real time",
        "realtime",
        "live",

        "this week",
        "this month",
        "this year",

        "yesterday",

        "what happened",
        "what's happening",
        "whats happening",

        "as of now",
        "right now",

        "up to date",
        "up-to-date",
        "updated",
        "update",

        "2026",

        "weather",
        "temperature",
        "forecast",

        "stock price",
        "share price",
        "market price",

        "gold price",
        "silver price",

        "petrol price",
        "diesel price",

        "exchange rate",
        "usd to inr",
        "inr to usd",

        "score",
        "match result",

        "election result",
        "election results"

    ]

    return any(
        phrase in text
        for phrase in fresh_phrases
    )


def local_response(command):

    text = normalize_text(command)


    # Greetings

    if text in [
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii"
    ]:

        return "Hello! I am SmartAI. How can I help you?"


    if "how are you" in text:

        return "I'm doing great and ready to help!"


    # Date

    if text in [
        "date",
        "what is the date",
        "what's the date",
        "what is today's date",
        "whats today's date",
        "today date"
    ]:

        return datetime.now().strftime(
            "Today's date is %d %B %Y."
        )


    # Yesterday

    if text in [
        "yesterday",
        "what was yesterday's date"
    ]:

        yesterday = datetime.now() - timedelta(days=1)

        return yesterday.strftime(
            "Yesterday was %d %B %Y."
        )


    # Tomorrow

    if text in [
        "tomorrow",
        "what is tomorrow's date"
    ]:

        tomorrow = datetime.now() + timedelta(days=1)

        return tomorrow.strftime(
            "Tomorrow is %d %B %Y."
        )


    # Time

    if text in [
        "time",
        "what is the time",
        "what's the time",
        "current time",
        "what time is it"
    ]:

        return datetime.now().strftime(
            "The current time is %I:%M %p."
        )


    # Calculator

    calculator_prefixes = [
        "calculate ",
        "solve ",
        "what is "
    ]


    expression = None


    for prefix in calculator_prefixes:

        if text.startswith(prefix):

            possible = text[len(prefix):].strip()


            if re.fullmatch(
                r"[0-9+\-*/(). %]+",
                possible
            ):

                expression = possible

                break


    # Direct calculation

    if expression is None:

        if re.fullmatch(
            r"[0-9+\-*/(). %]+",
            text
        ):

            expression = text


    if expression:

        try:

            result = eval(
                expression,
                {"__builtins__": {}},
                {}
            )

            return f"The answer is {result}."

        except Exception:

            return "I couldn't calculate that expression."


    return None


def get_ai_response(user_message):

    global conversation_history

    command = user_message.strip()


    if not command:

        return "Please type a question."


    # Handle local commands first.

    local = local_response(command)


    if local is not None:

        return local


    if client is None:

        return (
            "The Groq API key is not configured on the server. "
            "Please check the GROQ_API_KEY environment variable in Render."
        )


    # Save user message.

    conversation_history.append({
        "role": "user",
        "content": command
    })


    # Keep recent conversation.

    recent_history = conversation_history[-10:]


    current_date = datetime.now().strftime(
        "%d %B %Y"
    )


    system_message = {

        "role": "system",

        "content": (

            "You are SmartAI, a helpful personal AI assistant. "

            "Today's server date is "
            + current_date
            + ". "

            "Answer clearly and simply using student-friendly language. "

            "Remember recent conversation context and understand follow-up questions. "

            "You have access to Groq's browser search tool. "

            "For questions asking about current, latest, recent, today's, live, "
            "real-time, news, current affairs, prices, weather, scores, events, "
            "or other time-sensitive information, use browser search before answering. "

            "For current affairs questions, search specifically for the requested "
            "country or region and the current date. "

            "Do not pretend that older model knowledge is current. "

            "When current web information is used, clearly mention the relevant "
            "dates and sources when available."

        )

    }


    try:

        if needs_fresh_information(command):

            # Browser search is REQUIRED for fresh-information questions.

            response = client.chat.completions.create(

                model=MODEL,

                messages=[
                    system_message
                ] + recent_history,

                max_completion_tokens=2048,

                temperature=1,

                tool_choice="required",

                tools=[
                    {
                        "type": "browser_search"
                    }
                ]

            )

        else:

            # Normal questions use the AI without web search.

            response = client.chat.completions.create(

                model=MODEL,

                messages=[
                    system_message
                ] + recent_history,

                max_completion_tokens=1024,

                temperature=1

            )


        answer = response.choices[0].message.content


        if not answer:

            answer = "Sorry, I couldn't generate an answer."


        # Save AI response.

        conversation_history.append({

            "role": "assistant",

            "content": answer

        })


        return answer


    except Exception as error:

        print(
            "Groq error:",
            repr(error)
        )


        if needs_fresh_information(command):

            return (
                "I couldn't retrieve current web information right now. "
                "Please try the same question again in a moment."
            )


        return (
            "Sorry, I couldn't connect to the assistant right now. "
            "Please try again."
        )


@app.route("/")
def home():

    return render_template_string(HTML)


@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json(
        silent=True
    ) or {}


    message = data.get(
        "message",
        ""
    ).strip()


    if not message:

        return jsonify({

            "answer": "Please type a question."

        })


    answer = get_ai_response(message)


    return jsonify({

        "answer": answer

    })


@app.route("/clear", methods=["POST"])
def clear():

    global conversation_history

    conversation_history.clear()


    return jsonify({

        "status": "cleared"

    })


if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=False

    )
