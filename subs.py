import pandas as pd

def set_tickers(user, tickers, sma):
    print(user)
    df = pd.read_csv('database.csv', header=0, sep=';')
    print(df)
    for ticker in list(zip(tickers.split(","), sma.split(" "))):
        if ticker[0] not in df[df['user_id'] == user].tickers.values:
            df = df.append({'user_id': user, 'tickers': ticker[0], "sma": ticker[1]}, ignore_index=True)
    df.to_csv('database.csv', sep=';', index=False)


def del_tic(user_id, tickers):
    tickers = tickers.lower()
    df = pd.read_csv('database.csv', header=0, sep=';')
    if tickers == "отписка":
        df = df.drop(df[df["user_id"] == user_id].index)
    else:
        for ticker in tickers.split(","):
            df = df.drop(df[(df["user_id"] == user_id) & (df["tickers"] == ticker)].index)
    df.to_csv('database.csv', sep=';', index=False)


def sub_ticker_list(user_id):
    df = pd.read_csv('database.csv', header=0, sep=';')
    user_tickers = df[df['user_id'] == user_id].tickers.values
    msg = "\n".join(user_tickers)
    return msg
