import time
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from telegram import Bot
from config import API_KEY, API_SECRET, TELEGRAM_API_TOKEN, CHAT_ID, SYMBOL, INTERVAL, LIMIT

# اتصال به بایننس API
client = Client(API_KEY, API_SECRET)

# اتصال به تلگرام API
telegram_bot = Bot(token=TELEGRAM_API_TOKEN)

# تابع برای ارسال پیام به تلگرام
def send_telegram_message(message):
    telegram_bot.send_message(chat_id=CHAT_ID, text=message)

# تابع برای گرفتن کندل‌ها از بایننس
def get_candles(symbol, interval, limit):
    candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    return candles

# تابع برای محاسبه میانگین حجم 200 کندل گذشته
def calculate_avg_volume(candles):
    volumes = [float(candle[5]) for candle in candles]  # حجم کندل‌ها در ایندکس 5 قرار دارد
    return sum(volumes) / len(volumes)

# تابع برای بررسی سیگنال خرید یا فروش
def check_signal(candles, avg_volume):
    current_candle = candles[-1]
    current_volume = float(current_candle[5])  # حجم کندل کنونی
    close_price = float(current_candle[4])  # قیمت بسته شدن کندل
    open_price = float(current_candle[1])  # قیمت باز شدن کندل
    
    # بررسی اینکه حجم کندل کنونی بیشتر از میانگین حجم 200 کندل گذشته است یا نه
    if current_volume > avg_volume:
        if close_price > open_price:  # کندل سبز (سیگنال خرید)
            return 'BUY'
        elif close_price < open_price:  # کندل قرمز (سیگنال فروش)
            return 'SELL'
    return 'NO_SIGNAL'

# تابع برای بررسی 25 معامله متوالی در تب "Trades"
def check_recent_trades(client, action, symbol):
    trades = client.futures_account_trades(symbol=symbol)
    recent_trades = [trade for trade in trades if trade['side'] == action]
    return len(recent_trades) >= 25

# تابع اصلی برای بررسی بازار و ارسال سیگنال
def main():
    candles = get_candles(SYMBOL, INTERVAL, LIMIT)
    avg_volume = calculate_avg_volume(candles)
    signal = check_signal(candles, avg_volume)
    
    if signal == 'BUY' and check_recent_trades(client, 'BUY', SYMBOL):
        send_telegram_message('Signal: BUY\nConditions met: 25 consecutive BUY trades.')
    elif signal == 'SELL' and check_recent_trades(client, 'SELL', SYMBOL):
        send_telegram_message('Signal: SELL\nConditions met: 25 consecutive SELL trades.')
    else:
        print('No signal to send.')
    
    # هر 1 دقیقه یکبار سیگنال‌ها را بررسی می‌کند
    time.sleep(60)

# اجرای ربات به طور مداوم
if __name__ == "__main__":
    while True:
        main()
