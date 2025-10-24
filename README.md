Here’s a complete **`README.md`** for your repo, written in a clear and professional developer-focused style:

---

# Real-Time Trading Transcription Service

A Python-based real-time speech-to-text system designed for trading floors.
This project leverages **Deepgram’s Nova-3** model for accurate, low-latency transcription and **OpenAI’s GPT-4.1-mini** model to detect and log trade intents as they happen.

---

## 🚀 Overview

Trading floors are loud, fast-paced, and chaotic. Capturing accurate voice logs in real time is a major challenge, yet essential for **auditing and compliance**.

This project demonstrates how to:

* Stream live audio from a trader’s microphone
* Transcribe it in real time using **Deepgram Nova-3**
* Detect trading instructions such as *"Buy 100 AAPL at market"* using **OpenAI’s LLM**
* Log valid trades automatically into a JSONL file for record keeping

---

## 🧠 Architecture

The system is made up of three main components:

1. **Audio Input:** Captures live microphone input using `PyAudio`.
2. **WebSocket Communication:** Streams audio in chunks to Deepgram’s API for transcription.
3. **Transcription & Logging:** Processes transcripts with OpenAI to detect trading intents and logs detected trades in real time.

```
🎙️ Microphone → WebSocket → Deepgram (Nova-3) → OpenAI LLM → Trade Log
```

---

## 🧩 Features

* Real-time voice transcription
* Speaker-aware diarization
* Trading intent detection (Buy, Sell, Cancel)
* Automatic trade logging to `trades_log.jsonl`
* Configurable and extensible for other downstream tasks

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Neurl-LLC/deepgram-60.git
cd deepgram-60
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root with your API keys:

```
OPENAI_API_KEY=sk-your-openai-key
DEEPGRAM_API_KEY=your-deepgram-key
```

---

## 🧑‍💻 Running the Application

Start the trading transcription service:

```bash
python main.py
```

You’ll see output like:

```
🎙️  Microphone live. Press Ctrl+C to stop.
🗣️  Speaker 0: Buy 100 AAPL at market
💹 TRADE DETECTED:
{
  "trade_detected": true,
  "action": "BUY",
  "symbol": "AAPL",
  "quantity": 100,
  "price_type": "MARKET",
  "price": null
}
```

All detected trades are stored in `trades_log.jsonl` with timestamps.

---

## 🧾 Example Trade Log

Each trade is stored as a structured JSON object:

```json
{
  "timestamp": "2025-10-21 15:42:03",
  "trade_detected": true,
  "action": "BUY",
  "symbol": "TSLA",
  "quantity": 200,
  "price_type": "LIMIT",
  "price": 250.00,
  "raw_text": "Buy 200 Tesla at limit 250"
}
```

---

## 🛠️ Customization

You can modify the `TRADING_INSTRUCTION` system prompt in `main.py` to adapt the detection logic for different trading formats, markets, or internal compliance requirements.

---

## 🧩 Future Improvements

* Integrate **Deepgram Flux** CSR model for conversational trade execution
* Add a web dashboard for visual trade tracking
* Include keyword-based risk detection and trade validation


