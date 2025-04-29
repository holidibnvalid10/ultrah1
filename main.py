
import ccxt
import requests
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY
})

# 118 ta coin
PAIRS = [
    "ACH/USDT", "ADA/USDT", "AGLD/USDT", "ALGO/USDT", "AMP/USDT", "APE/USDT", "API3/USDT", "APT/USDT", "ARB/USDT", "ARKM/USDT",
    "ARPA/USDT", "ASTR/USDT", "ATA/USDT", "ATOM/USDT", "AVA/USDT", "AVAX/USDT", "AXL/USDT", "BANANA/USDT", "BCH/USDT", "BICO/USDT",
    "BTC/USDT", "CHZ/USDT", "CVC/USDT", "CYBER/USDT", "DATA/USDT", "DCR/USDT", "DENT/USDT", "DGB/USDT", "DIA/USDT", "DOT/USDT",
    "DUSK/USDT", "EGLD/USDT", "ENA/USDT", "ENS/USDT", "ETC/USDT", "ETH/USDT", "FIDA/USDT", "FIL/USDT", "FIO/USDT", "FLUX/USDT",
    "GLMR/USDT", "GMT/USDT", "GNO/USDT", "GTC/USDT", "HBAR/USDT", "HIVE/USDT", "ICP/USDT", "IOTA/USDT", "IO/USDT", "KDA/USDT",
    "KMD/USDT", "KSM/USDT", "LINK/USDT", "LPT/USDT", "LTC/USDT", "MANA/USDT", "MANTA/USDT", "MASK/USDT", "MDT/USDT", "ME/USDT",
    "MINA/USDT", "MOVE/USDT", "MOVR/USDT", "MTL/USDT", "OGN/USDT", "ONE/USDT", "ONG/USDT", "OP/USDT", "ORDI/USDT", "OXT/USDT",
    "PHA/USDT", "PHB/USDT", "PIVX/USDT", "POLYX/USDT", "QTUM/USDT", "RAD/USDT", "RARE/USDT", "REQ/USDT", "RSR/USDT", "SCRT/USDT",
    "SCR/USDT", "SC/USDT", "SEI/USDT", "SFP/USDT", "SKL/USDT", "SOL/USDT", "STORJ/USDT", "STX/USDT", "SUI/USDT", "SXP/USDT",
    "SYS/USDT", "TAO/USDT", "TFUEL/USDT", "THETA/USDT", "TIA/USDT", "TNSR/USDT", "TRB/USDT", "TWT/USDT", "VANA/USDT", "VET/USDT",
    "VIC/USDT", "VTHO/USDT", "WAXP/USDT", "WLD/USDT", "XEC/USDT", "XLM/USDT", "XNO/USDT", "XRP/USDT", "XTZ/USDT", "XVG/USDT",
    "ZEN/USDT", "ZIL/USDT", "ZRO/USDT", "AIXBT/USDT", "ALT/USDT", "BIO/USDT", "C98/USDT", "CELO/USDT", "CELR/USDT", "CFX/USDT",
    "CKB/USDT", "COS/USDT", "DASH/USDT", "D/USDT", "EOS/USDT", "GAS/USDT", "HIGH/USDT", "HOOK/USDT", "ID/USDT", "IOTX/USDT",
    "KAITO/USDT", "OMNI/USDT", "SAGA/USDT", "STEEM/USDT", "STRAX/USDT", "S/USDT", "VANRY/USDT", "WCT/USDT", "HYPER/USDT", "SHELL/USDT"
]

# Telegram xabar
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegramga yuborishda xato:", e)

# POC hisoblash (real trade volume asosida)
def calculate_real_poc(symbol, since):
    try:
        market = exchange.market(symbol)
        base = market['base'].lower()
        quote = market['quote'].lower()
        symbol_binance = f"{base}{quote}"
        trades = exchange.fetch_trades(symbol, since=since)
        volume_price_map = {}
        for t in trades:
            price = round(t['price'], 4)
            volume = t['amount']
            if price not in volume_price_map:
                volume_price_map[price] = 0
            volume_price_map[price] += volume
        poc_price = max(volume_price_map, key=volume_price_map.get)
        return poc_price
    except Exception as e:
        print(f"POC xatolik: {symbol} - {e}")
        return None

# Candle sinxronlash
def wait_until_next_valid_time():
    now = datetime.utcnow()
    next_time = now.replace(minute=0, second=5, microsecond=0) + timedelta(hours=1)
    wait_seconds = (next_time - now).total_seconds()
    print(f"⌛ Kutilyapti: {int(wait_seconds)}s ({next_time.strftime('%H:%M')} UTC)")
    time.sleep(wait_seconds)

# So‘nggi 2 ta yopilgan H1 candle
def get_last_closed_candles(pair):
    try:
        candles = exchange.fetch_ohlcv(pair, '1h', limit=3)
        return candles[-3:-1]
    except Exception as e:
        print(f"Candle xato: {pair} - {e}")
        return []

# Bullish engulfing + real POC sharti
def check_bullish_engulfing_with_real_poc(pair, candles):
    if len(candles) < 2:
        return False

    prev = candles[0]
    curr = candles[1]

    open1, high1, low1, close1 = prev[1:5]
    open2, high2, low2, close2 = curr[1:5]

    # Bullish engulfing sharti
    if close1 >= open1 or close2 <= open2 or close2 <= high1:
        return False

    # Real POClarni hisoblash (eng so‘nggi sham uchun)
    since_prev = prev[0]
    since_curr = curr[0]
    poc_prev = calculate_real_poc(pair, since_prev)
    poc_curr = calculate_real_poc(pair, since_curr)

    if poc_prev is None or poc_curr is None:
        return False

    # POC sharti: yashil sham POC > qizil sham POC
    return poc_curr > poc_prev

# Asosiy sikl
while True:
    wait_until_next_valid_time()
    for pair in PAIRS:
        candles = get_last_closed_candles(pair)
        if check_bullish_engulfing_with_real_poc(pair, candles):
            msg = f"✅ Bullish Engulfing + Real POC (H1)🪙 Pair: {pair}"
            send_telegram_message(msg)
            time.sleep(1)
    print(f"⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC tekshirildi.")