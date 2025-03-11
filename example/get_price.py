def get_price(currency):
    URL = "https://api.coinbase.com/v2/exchange-rates?currency=" + currency
    r = requests.get(url = URL)
    data = r.json()
    print(json.dumps(data, indent=4))
    eur_price = data['data']['rates']['EUR']
    print(currency + ": " + eur_price + " EUR")
    return int(decimal.Decimal(eur_price) * 1000)
