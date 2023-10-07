# NIRA Net Backend
おいここまで来たらもう戻れないだろこれ

# What is this?
これは、NIRA Netのバックエンド的なものを提供するごくごく一般的なAPIサーバーです。  
一般的すぎて吐き気を催すほどです。

# ちゃんとした説明
Pythonの`Sanic`を使用して作成されたAPIサーバーです。  
Discord APIやMongoDBと連携を行い、NIRA Netの(主にダッシュボードでの)通信を行うためのものです。

# Install/Setup
1. このリポジトリを任意の場所にCloneする
2. `pip install -r requirements.txt`で必要なライブラリをインストールする
3. `temp.config.json`を`config.json`にリネーム(コピー)する
4. `config.json`を編集する
5. `python main.py`で起動する

# `config.json`

```json
{
    "client_id": Discord Client ID,
    "client_secret": Discord Client Secret,
    "bot_token": Discord BOT Token,
    "mongo_uri": MongoDB URI,
    "mongo_db": Mongo Database Name,
    "cors_origins": CORS Origin,
    "host": Web Host,
    "port": Web Port Number
}
```

## `client_id`
Discord Developer Portalで取得したClient ID

## `client_secret`
Discord Developer Portalで取得したClient Secret

## `bot_token`
Discord Developer Portalで取得したBOT Token

## `mongo_uri`
MongoDBのURI

## `mongo_db`
MongoDBのDatabase名

## `cors_origins`
CORSで許可するOrigin

## `host`
Webサーバーのホスト名

## `port`
Webサーバーのポート番号
