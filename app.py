import os
import asyncio
import threading
import ccxt.pro as ccxt
import telebot
import pandas as pd
import numpy as np
from flask import Flask, render_template_string
from sklearn.linear_model import LinearRegression

# কনফিগারেশন
TG_TOKEN = "7976957443:AAHO1JWhVHM3u7nmm-qsayHqTKtwHHH6IrE"
CHAT_ID = "6662252932"

bot = telebot.TeleBot(TG_TOKEN)
app = Flask(__name__)

# এক্সচেঞ্জ সেটিংস
exchange = ccxt.binance({'options': {'defaultType': 'future'}})
symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
data_store = {s: pd.DataFrame(columns=['price', 'volume']) for s in symbols}
market_intel = {s: {'price': 0, 'forecast': 'STABLE', 'confidence': 0, 'target_1m': 0} for s in symbols}

# ১ মিনিট ফোরকাস্টিং ইঞ্জিন (Chronos V12)
def chronos_predict(prices):
    if len(prices) < 40: return "CALIBRATING", 0, 0
    
    # Linear Regression for 60s prediction
    y = np.array(prices[-30:])
    x = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    
    # পরবর্তী ১ মিনিটের (৬০ ধাপ) প্রেডিকশন
    future_index = len(y) + 1
    predicted_price = model.predict([[future_index]])[0]
    change_pct = ((predicted_price - prices[-1]) / prices[-1]) * 100
    
    confidence = min(abs(change_pct) * 500, 99) # Confidence Score logic
    
    if change_pct > 0.03: return "🚀 BULLISH (Next 1m)", round(confidence, 1), round(predicted_price, 2)
    if change_pct < -0.03: return "📉 BEARISH (Next 1m)", round(confidence, 1), round(predicted_price, 2)
    
    return "⚖️ SIDEWAYS", round(confidence, 1), round(predicted_price, 2)

async def omega_v12_chronos_engine():
    print("V12.0 Chronos Engine Active...")
    bot.send_message(CHAT_ID, "🔮 **OMEGA-X V12.0 CHRONOS ONLINE**\nStatus: 1-Minute Future Forecasting ACTIVE")

    while True:
        try:
            for symbol in symbols:
                ticker = await exchange.watch_ticker(symbol)
                price = ticker['last']
                
                # ডাটা আপডেট
                new_row = pd.DataFrame([[price, ticker['quoteVolume']]], columns=['price', 'volume'])
                data_store[symbol] = pd.concat([data_store[symbol], new_row]).tail(300)
                
                # প্রেডিকশন রান
                forecast, confidence, target = chronos_predict(data_store[symbol]['price'].tolist())
                
                # হাই-কনফিডেন্স ১ মিনিটের এলার্ট
                if confidence > 80:
                    msg = (f"🔮 **1-MIN FUTURE FORECAST**\n\n"
                           f"Asset: `{symbol}`\n"
                           f"Prediction: `{forecast}`\n"
                           f"Confidence: `{confidence}%` \n"
                           f"Current Price: `{price}`\n"
                           f"Expected Target: `{target}`")
                    bot.send_message(CHAT_ID, msg, parse_mode='Markdown')

                market_intel[symbol] = {
                    'price': price,
                    'forecast': forecast,
                    'confidence': confidence,
                    'target': target
                }
                
            await asyncio.sleep(0.1)
        except Exception as e:
            await asyncio.sleep(5)

# অ্যাডভান্সড প্রেডিক্টিভ ড্যাশবোর্ড
@app.route('/')
def dashboard():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OMEGA-X CHRONOS V12</title>
        <meta http-equiv="refresh" content="1">
        <style>
            body { background: #000; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }
            .card { border: 1px solid #00ff00; padding: 20px; border-radius: 10px; background: rgba(0,255,0,0.02); box-shadow: 0 0 15px rgba(0,255,0,0.1); }
            .bullish { color: #00ff00; text-shadow: 0 0 10px #00ff00; }
            .bearish { color: #ff0000; text-shadow: 0 0 10px #ff0000; }
            .price { font-size: 32px; color: #fff; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1 style="text-align:center;">🔮 OMEGA-X CHRONOS V12.0 // PREDICTIVE CORE</h1>
        <div class="grid">
            {% for s, d in info.items() %}
            <div class="card">
                <div style="font-size:12px; color:#888;">{{ s }} / PERPETUAL</div>
                <div class="price">${{ d.price }}</div>
                <div class="{{ 'bullish' if 'BULLISH' in d.forecast else 'bearish' if 'BEARISH' in d.forecast else '' }}">
                    FORECAST: {{ d.forecast }}
                </div>
                <p>Confidence: {{ d.confidence }}%</p>
                <p style="font-size:11px; color:#555;">Target (60s): ${{ d.target }}</p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """, info=market_intel)

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(omega_v12_chronos_engine())

if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
