import pyaudio
import asyncio
import json
import os
import sys
import websockets
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# --- CONFIG ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 8000
audio_queue = asyncio.Queue()
all_mic_data = []
all_transcripts = []

# --- SYSTEM PROMPT FOR TRADING ---
TRADING_INSTRUCTION = """
You are a real-time trading intent detection assistant.
Your job is to analyze voice transcripts from a trading floor in real time.

When a transcript contains a trading instruction (e.g. "Buy 200 shares of AAPL at market", 
"Sell 100 Tesla at limit 250", "Cancel order 309"), you must extract the intent and return a structured JSON object.

Return ONLY JSON, no explanations. 
If no trade intent is detected, return: {"trade_detected": false}

If a trade intent is detected, return:
{
  "trade_detected": true,
  "action": "BUY" or "SELL" or "CANCEL",
  "symbol": "<STOCK_SYMBOL>",
  "quantity": <number if available>,
  "price_type": "MARKET" or "LIMIT" or "UNKNOWN",
  "price": <float if mentioned else null>,
  "raw_text": "<original user text>"
}
"""

# --- MIC CALLBACK ---
def mic_callback(input_data, frame_count, time_info, status_flag):
    audio_queue.put_nowait(input_data)
    return (input_data, pyaudio.paContinue)

# --- HELPER: GET TRANSCRIPT TEXT ---
def get_speaker_transcripts(json_data):
    speaker_transcripts = {}
    channel = json_data.get("channel", {})
    alternatives = channel.get("alternatives", [])

    for alt in alternatives:
        for word_info in alt.get("words", []):
            speaker_id = word_info.get("speaker", "Unknown")
            word = word_info.get("punctuated_word", word_info.get("word", ""))
            if speaker_id not in speaker_transcripts:
                speaker_transcripts[speaker_id] = []
            speaker_transcripts[speaker_id].append(word)

    formatted_transcripts = []
    for speaker_id, words in speaker_transcripts.items():
        formatted_transcripts.append(f"Speaker {speaker_id}: {' '.join(words)}")

    return "\n".join(formatted_transcripts)

# --- STREAM AUDIO TO DEEPGRAM ---
async def sender(ws, audio_queue):
    print("🟢 Streaming audio to Deepgram...")
    try:
        while True:
            mic_data = await audio_queue.get()
            all_mic_data.append(mic_data)
            await ws.send(mic_data)
    except asyncio.CancelledError:
        return
    except Exception as e:
        print(f"❌ Sender error: {e}")

# --- DETECT TRADING INTENT IN REAL TIME ---
async def detect_trading_intent(transcript: str):
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": TRADING_INSTRUCTION},
                {"role": "user", "content": transcript},
            ],
            temperature=0
        )

        output = response.output_text.strip()
        if not output:
            return

        data = json.loads(output)
        if data.get("trade_detected"):
            print(f"💹 TRADE DETECTED: {json.dumps(data, indent=2)}")
            log_trade(data)
    except Exception as e:
        print(f"⚠️ Error processing trade intent: {e}")

# --- LOG TRADES ---
def log_trade(data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("trades_log.jsonl", "a") as f:
        f.write(json.dumps({"timestamp": timestamp, **data}) + "\n")

# --- RECEIVE FROM DEEPGRAM ---
async def receiver(ws):
    print("🟢 Listening for Deepgram transcripts...")
    first_message = True
    async for msg in ws:
        res = json.loads(msg)
        if first_message:
            print("🟢 Receiving Deepgram messages...")
            first_message = False
        try:
            if res.get("is_final"):
                transcript = get_speaker_transcripts(res)
                if transcript:
                    print(f"🗣️  {transcript}")
                    all_transcripts.append(transcript)
                    # Process trading detection concurrently
                    asyncio.create_task(detect_trading_intent(transcript))
        except KeyError:
            print(f"🔴 Unexpected response: {msg}")

# --- MICROPHONE CAPTURE ---
async def microphone(audio_queue):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        stream_callback=mic_callback,
    )

    stream.start_stream()
    print("🎙️  Microphone live. Press Ctrl+C to stop.")
    try:
        while stream.is_active():
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

# --- MAIN EVENT LOOP ---
async def run(key, model='nova-3'):
    deepgram_url = f"wss://api.deepgram.com/v1/listen?punctuate=true&diarize=true&model={model}&encoding=linear16&sample_rate=16000"
    async with websockets.connect(deepgram_url, additional_headers={"Authorization": f"Token {key}"}) as ws:
        print("✅ Connected to Deepgram.")
        tasks = [
            asyncio.create_task(sender(ws, audio_queue)),
            asyncio.create_task(receiver(ws)),
            asyncio.create_task(microphone(audio_queue)),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("🛑 Stopped gracefully.")

def main():
    key = os.getenv("DEEPGRAM_API_KEY")
    if not key:
        print("❌ Missing DEEPGRAM_API_KEY in environment.")
        sys.exit(1)
    asyncio.run(run(key))

if __name__ == "__main__":
    main()

