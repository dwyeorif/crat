import ccxt
import datetime
import FinanceDataReader as fdr
import pyupbit
import time
import requests

p_exchange = 1188.72  # Exchange rate initial value
u_mount = 2000000  # Upbit order amount
p_standard = 0.9153  # Premium standard
p_gap = 0.75  # Premium gap
binance = ccxt.binance({
'apiKey': '',
'secret': '',
})  # Binance API
upbit = pyupbit.Upbit('', '')  # Upbit API
myToken = ''  # Slack token
ticker = 'EOS'  # Ticker
u_count = 350  # Upbit order quantity
b_count = round(u_count*0.997, 1)  # Binance order quantity
p_cnt = 299  # Initial count


def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
    headers={"Authorization": "Bearer "+token},
    data={"channel": channel,"text": text}
        )


def get_exchange():
    try:
        today = str(datetime.date.today())
        today = int(today.replace('-', ''))
        today = str(today)
        exchange = fdr.DataReader('USD/KRW', today).iloc[-1, 0]
    except:
        today = 211026
        exchange = fdr.DataReader('USD/KRW', today).iloc[-1, 0]
    post_message(myToken, "#stock", 'Exchange: ' + str(exchange))
    return exchange


def binance_balance(tk):
    balance = binance.fetch_balance()  # Binance balance
    b_balance = balance[tk]['free']
    return b_balance


def binance_price(tk, p_exchange):
    b_ticker = binance.fetch_ticker(tk+'/USDT')  # Binance current KRW price
    price = b_ticker['close']
    price2 = price * p_exchange
    return price2


def binance_usd_price(tk):
    b_ticker = binance.fetch_ticker(tk+'/USDT')  # Binance current USD price
    price = b_ticker['close']
    return price


def binance_buy(tk, cnt):
    order = binance.create_market_buy_order(tk + '/USDT', cnt)  # Binance market buy by count
    print(order)


def binance_sell(tk, cnt):
    order = binance.create_market_sell_order(tk + '/USDT', cnt)  # Binance market sell by count
    print(order)


def upbit_price(tk):
    u_price = pyupbit.get_current_price('KRW-' + tk)  # Upbit current KRW price
    return u_price


def upbit_buy(tk, mnt):  # Upbit market buy by amount
    u_ticker = 'KRW-' + tk
    market_price_buy = upbit.buy_market_order(u_ticker, mnt)
    print(market_price_buy)


def upbit_sell(tk, cnt):  # Upbit market sell by count
    u_ticker = 'KRW-' + tk
    market_price_sell = upbit.sell_market_order(u_ticker, cnt)
    print(market_price_sell)


def get_premium(b_price, u_price, tk):  # Current premium
    premium = 100*(u_price-b_price)/u_price
    return premium


while True:
    try:
        if binance_balance('USDT') > round(u_count*binance_usd_price(ticker)*1.03) and upbit.get_balance('KRW-' + ticker) > u_count:  # Premium trading
            if get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) > (p_standard+2*p_gap):  # Above standard
                binance_buy(ticker, u_count)
                upbit_sell(ticker, u_count)
                post_message(myToken, "#stock", 'Premium trading: ' + str(round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)) + ' / ' + str(u_count) + 'ea')
                p_standard = round((p_standard * 0.999) + (get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker) * 0.001), 9)
                if binance_balance('USDT') < round(u_count * binance_usd_price(ticker) * 1.05):  # Reset
                    p_exchange = get_exchange()
                    p_standard = round(get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker), 9) - 2.2*p_gap
                    post_message(myToken, "#stock", 'Standard reset: ' + str(p_standard))

        if upbit.get_balance('KRW') > round(u_mount*1.03) and binance_balance(ticker) > b_count:  # Reverse premium trading
            if get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker) < (p_standard-p_gap):  # Below standard
                binance_sell(ticker, b_count)
                upbit_buy(ticker, u_mount)
                post_message(myToken, "#stock", 'R-premium trading: ' + str(round(get_premium((binance_usd_price(ticker)*p_exchange), upbit_price(ticker), ticker), 2)) + ' / ' + str(b_count) + 'ea')
                p_standard = round((p_standard * 0.999) + (get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker) * 0.001), 9)

        p_standard = round((p_standard * 0.99998) + (get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker) * 0.00002), 9)
        p_cnt = p_cnt + 1
        time.sleep(7)

        if p_cnt % 300 == 0:
            p_cnt = 0
            now_premium = round(get_premium((binance_usd_price(ticker) * p_exchange), upbit_price(ticker), ticker), 2)
            b_krw = float(p_exchange * (1.0 + now_premium / 100))
            krw_balance = round(upbit.get_balance('KRW') + binance_balance('USDT') * b_krw)
            ticker_balance = round(upbit.get_balance('KRW-' + ticker) + binance_balance(ticker))
            u_count = round(u_mount / (upbit_price(ticker) + 5))
            b_count = round(u_count*0.997, 1)
            post_message(myToken, "#stock", 'Now: ' + str(now_premium) + ' / Std: ' + str(round(p_standard, 2)) + ' / Exc: ' + str(p_exchange) + '\nCrypto: ' + str(ticker_balance) + ' / KRW:  ' + str(krw_balance))

    except Exception as e:
        post_message(myToken, "#stock", e)
        time.sleep(30)
