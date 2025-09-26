import requests

# APIキーをセット
API_KEY = "RGAPI-c253c9e4-04f0-41ad-83a7-2a8980f0b625"

# グローバルリージョン（match-v5はjp1じゃなくasia, americas, europeなどを使う）
region = "asia"

# テスト用のPUUID（実際にはsummoner-v4 APIなどで取得します）
puuid = "6T6j1sWxXpSLAIqz4LC0jxSBAMf3OS0UPBdxF6saYw8X91Tquq46L2SorwIbQ9KVh_nlHkgYJ0jwvw"

# 試合ID取得APIのURL
url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"

headers = {
    "X-Riot-Token": API_KEY
}

# パラメータ（直近10試合だけ取得）
params = {
    "count": 10
}

response = requests.get(url, headers=headers, params=params)

print(f"ステータスコード: {response.status_code}")

if response.status_code == 200:
    match_ids = response.json()
    print("✅ 取得成功！直近10試合のMatch IDs:")
    for match_id in match_ids:
        print(match_id)
else:
    print("❌ エラー発生:")
    print(response.text)
