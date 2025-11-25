oiceBot — AI Health Assistant (Hindi + Twilio + Gemini)

VoiceBot is a Hindi-speaking AI Health Assistant powered by Google Gemini, integrated with Twilio Voice, and deployed locally using FastAPI and Cloudflare Tunnel.
It allows real phone conversations with an AI that remembers context during the call and responds naturally using Polly Kajal Neural Voice.

✨ Features

✅ Real-time phone conversations via Twilio
✅ Natural Hindi Neural voice (Polly.Kajal-Neural)
✅ Context-aware responses (AI remembers the conversation flow)
✅ Powered by Gemini 2.5 Flash
✅ Secure local hosting via Cloudflare Tunnel
✅ Runs fully on FastAPI

🧩 Tech Stack
Component	Technology Used
Backend	FastAPI (Python)
AI Engine	Google Gemini 2.5 Flash
Voice	Twilio Voice + Polly Kajal Neural
Hosting Tunnel	Cloudflare Tunnel
Environment	Python v3.10+
Language	Hindi (hi-IN)
⚙️ Installation
1️⃣ Clone the repository
git clone https://github.com/rohitsinghnegi/voicebot.git
cd voicebot

2️⃣ Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

3️⃣ Install dependencies
pip install -r requirements.txt


Example of requirements.txt

fastapi
uvicorn
twilio
google-generativeai
python-dotenv
cloudflare

🔑 Environment Setup

Create a file named .env in your project root:

GEMINI_API_KEY=your_gemini_api_key_here
PUBLIC_URL=https://<your-cloudflare-tunnel-url>


You can get your Gemini API key from:
👉 https://aistudio.google.com/app/apikey

☁️ Cloudflare Tunnel Setup

Install Cloudflare Tunnel (cloudflared) if not installed:

winget install Cloudflare.cloudflared


Then start a tunnel to expose your local FastAPI app:

cloudflared tunnel --url http://localhost:8000


You’ll see a public URL like:

https://dude-examine-producers-pin.trycloudflare.com


Copy this URL and update your .env file:

PUBLIC_URL=https://dude-examine-producers-pin.trycloudflare.com

☎️ Twilio Setup

Go to your Twilio Console → Phone Numbers
.

Select your Twilio phone number.

Under Voice & Fax → A Call Comes In, set:

Webhook URL:

https://<your-cloudflare-tunnel-url>/voice


HTTP Method: POST

Save your settings.

🚀 Run the Project
Step 1: Start FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Step 2: Start Cloudflare tunnel
cloudflared tunnel --url http://localhost:8000


Now your app is publicly accessible via Cloudflare, and Twilio can reach it.

🔍 Testing via cURL
1️⃣ Check Greeting
curl -X POST "https://<your-cloudflare-url>/voice" -d "CallSid=TEST1"

2️⃣ Simulate User Input
curl -X POST "https://<your-cloudflare-url>/gather" -d "CallSid=TEST1" -d "SpeechResult=मुझे सर दर्द हो रहा है"

3️⃣ Context Test
curl -X POST "https://<your-cloudflare-url>/gather" -d "CallSid=TEST1" -d "SpeechResult=यह लगातार दो दिन से हो रहा है"

🧠 How It Works

Twilio calls your /voice endpoint → returns a greeting TwiML.

User speaks → Twilio sends the text transcript (SpeechResult) to /gather.

The server sends the user query + previous context to Gemini 2.5 Flash.

The AI generates a short Hindi medical response.

The text is converted into speech using Polly Kajal Neural, and Twilio plays it live.

Context is maintained until the call ends.

🧹 Optional Cleanup

After the call ends, Twilio calls /status →
your app deletes the conversation context for that CallSid.

📁 Folder Structure