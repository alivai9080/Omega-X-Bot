import os
import asyncio
import threading
import ccxt.pro as ccxt
import telebot
from telebot import types
import numpy as np
import pandas as pd
from flask import Flask, render_template_string
import time
from collections import deque
from scipy.fft import fft
import logging

# ==========================================
# ১. গ্লোবাল সুপার কনফিগারেশন
# ==========================================
class OmegaConfig:
    # সার্ভার এনভায়রনমেন্ট থেকে ডাটা নিবে
    API_KEY = os.getenv('BINANCE_KEY', '')
    API_SECRET = os.getenv('BINANCE_SECRET', '')
    TG_TOKEN = os.getenv('TG_TOKEN', '')
    CHAT_ID = os.getenv('CHAT_ID', '')
    
    # স্ক্যানিং লিস্ট (কয়েন সংখ্যা বাড়ানো হয়েছে)
    SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT']
    IS_RUNNING = True
    BUFFER_SIZE = 1200  # ডাটা গভীরতা বৃদ্ধি
    SCAN_INTERVAL = 0.2  # মিলিসেকেন্ড স্পিড

# সিস্টেম লগিং
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OMEGA-X")

bot_tg = telebot.TeleBot(OmegaConfig.TG_TOKEN)
app = Flask(__name__)

# ==========================================
# ২. কোয়ান্টাম নিউরাল এনালাইসিস ইঞ্জিন
# ==========================================
class QuantumBrain:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': OmegaConfig.API_KEY,
            'secret': OmegaConfig.API_SECRET,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True
        })
        self.price_stream = {s: deque(maxlen=OmegaConfig.BUFFER_SIZE) for s in OmegaConfig.SYMBOLS}
        self.market_intel = {s: {
            'price': 0, 'signal': 'CALIBRATING', 'conf': 0, 'color': '#ffffff',
            'rsi': 50, 'whale_pressure': 0, 'wave_energy': 0
        } for s in OmegaConfig.SYMBOLS}

    # আরএসআই (RSI) ক্যালকুলেটর লজিক
    def get_rsi(self, series, period=14):
        if len(series) < period: return 50
        df = pd.Series(series)
        delta = df.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return round(100 - (100 / (1 + rs.iloc[-1])), 2)

    # ফুরিয়ার ট্রান্সফর্ম (FFT) এনালাইসিস
    def analyze_waves(self, symbol):
        data = list(self.price_stream[symbol])
        if len(data) < 100: return 0
        transformed = fft(np.array(data))
        return np.abs(transformed[1])

    async def core_scanner(self, symbol):
        logger.info(f"NODE LINKED: {symbol}")
        while True:
            if OmegaConfig.IS_RUNNING:
                try:
                    # রিয়েল টাইম ডাটা ফেচিং
                    ticker = await self.exchange.watch_ticker(symbol)
                    ob = await self.exchange.watch_order_book(symbol)
                    
                    curr_price = ticker['last']
                    self.price_stream[symbol].append(curr_price)

                    # লিকুইডিটি ক্লাস্টার এনালাইসিস
                    bids = sum([b[1] for b in ob['bids'][:30]])
                    asks = sum([a[1] for a in ob['asks'][:30]])
                    imbalance = (bids - asks) / (bids + asks)

                    # টেকনিক্যাল ম্যাট্রিক্স
                    rsi = self.get_rsi(list(self.price_stream[symbol]))
                    energy = self.analyze_waves(symbol)
                    
                    # ওমেগা ডিসিশন প্রোটোকল
                    status = "STABLE"
                    conf = abs(imbalance * 100)
                    color = "#ffffff"

                    if imbalance > 0.70 and rsi < 65:
                        status = "🚀 STRONG PUMP (1M)"
                        color = "#00ff88"
                        if conf > 88: self.alert_tg(symbol, "BUY", curr_price, conf)
                    
                    elif imbalance < -0.70 and rsi > 35:
                        status = "📉 SHARP DUMP (1M)"
                        color = "#ff0055"
                        if conf > 88: self.alert_tg(symbol, "SELL", curr_price, conf)

                    self.market_intel[symbol].update({
                        'price': curr_price, 'signal': status, 'conf': round(conf, 1),
                        'color': color, 'rsi': rsi, 'whale_pressure': round(imbalance, 3)
                    })

                except Exception as e:
                    await asyncio.sleep(5)
            await asyncio.sleep(OmegaConfig.SCAN_INTERVAL)

    def alert_tg(self, sym, side, price, conf):
        try:
            msg = f"🔱 **OMEGA-X PREDICTION**\n\nAsset: `{sym}`\nAction: `{side}`\nPrice: `{price}`\nConfidence: `{round(conf, 2)}%`"
            bot_tg.send_message(OmegaConfig.CHAT_ID, msg, parse_mode='Markdown')
        except: pass

brain = QuantumBrain()

# ==========================================
# ৩. সুপার-নিওন ড্যাশবোর্ড ইউআই
# ==========================================
@app.route('/')
@app.route('/health')
def terminal():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="2">
        <title>OMEGA-X TERMINAL</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
            body { background: #000; color: #fff; font-family: 'Orbitron', sans-serif; margin: 0; }
            .header { background: rgba(0,243,255,0.1); padding: 25px; text-align: center; border-bottom: 2px solid #00f3ff; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; padding: 30px; }
            .card { background: #080808; border: 1px solid #222; border-radius: 15px; padding: 25px; transition: 0.3s; }
            .card:hover { border-color: #00f3ff; transform: scale(1.02); }
            .price { font-size: 35px; color: #00f3ff; margin: 10px 0; }
            .signal { padding: 10px; border-radius: 8px; font-weight: bold; border: 1px solid; margin-top: 15px; }
            .glow { animation: blink 1.5s infinite; }
            @keyframes blink { from { opacity: 1; } to { opacity: 0.4; } }
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="glow">☢️ OMEGA-X : SENTIENT NODE ☢️</h1>
            <p>HFT SCANNING ACTIVE | CLOUD MODE</p>
        </div>
        <div class="grid">
            {% for s, d in data.items() %}
            <div class="card" style="border-bottom: 4px solid {{ d.color }};">
                <div style="font-size: 12px; color: #555;">{{ s }} / FUTURES</div>
                <div class="price">${{ d.price }}</div>
                <div style="font-size: 11px; margin-bottom: 10px;">RSI: {{ d.rsi }} | Whale Imbalance: {{ d.whale_pressure }}</div>
                <div class="signal" style="color: {{ d.color }}; border-color: {{ d.color }}; background: {{ d.color }}11;">
                    {{ d.signal }}
                </div>
                <p style="font-size: 10px; margin-top: 10px;">Confidence: {{ d.conf }}%</p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """, data=brain.market_intel)

# ==========================================
# ৪. ইগনিশন লঞ্চার
# ==========================================
if __name__ == "__main__":
    threading.Thread(target=lambda: bot_tg.infinity_polling(), daemon=True).start()
    
    def start_nodes():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [brain.core_scanner(s) for s in OmegaConfig.SYMBOLS]
        loop.run_until_complete(asyncio.gather(*tasks))

    threading.Thread(target=start_nodes, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
