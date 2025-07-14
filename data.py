import os
import json

# プロジェクト内の data ディレクトリを使用（Render無料プラン対応）
BASE_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(BASE_DIR, exist_ok=True)

# 各ファイルのパス
COINS_PATH = os.path.join(BASE_DIR, "coins.json")
QUOTES_PATH = os.path.join(BASE_DIR, "quotes.json")
VOICE_SETTINGS_PATH = os.path.join(BASE_DIR, "voice_settings.json")

# グローバル変数
coins = {}
quotes = {}
voice_settings = {}

# --------- 共通ロード関数 ---------
def load_all_data():
    global coins, quotes, voice_settings

    # coins.json 読み込み
    try:
        with open(COINS_PATH, "r", encoding="utf-8") as f:
            coins = json.load(f)
    except Exception:
        coins = {}

    # quotes.json 読み込み
    try:
        with open(QUOTES_PATH, "r", encoding="utf-8") as f:
            quotes = json.load(f)
    except Exception:
        quotes = {}

    # voice_settings.json 読み込み
    try:
        with open(VOICE_SETTINGS_PATH, "r", encoding="utf-8") as f:
            voice_settings = json.load(f)
    except Exception:
        voice_settings = {}

def save_all_data():
    # coins.json 保存
    with open(COINS_PATH, "w", encoding="utf-8") as f:
        json.dump(coins, f, ensure_ascii=False, indent=2)

    # quotes.json 保存
    with open(QUOTES_PATH, "w", encoding="utf-8") as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)

    # voice_settings.json 保存
    with open(VOICE_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(voice_settings, f, ensure_ascii=False, indent=2)

# --------- コイン操作 ---------
def get_coin(user_id: int) -> int:
    return coins.get(str(user_id), 0)

def update_coin(user_id: int, amount: int):
    user_id_str = str(user_id)
    coins[user_id_str] = coins.get(user_id_str, 0) + amount
    save_all_data()

def get_all_coins():
    return coins

# --------- 名言データ操作 ---------
def get_quotes(user_id: int):
    return quotes.get(str(user_id), [])

def add_quote(user_id: int, quote: dict):
    uid = str(user_id)
    quotes.setdefault(uid, []).append(quote)
    quotes[uid] = quotes[uid][-10:]  # 最大10件に制限
    save_all_data()

# --------- VoiceVox設定操作 ---------
def get_voice_settings(user_id: int):
    return voice_settings.get(str(user_id), {})

def set_voice_settings(user_id: int, settings: dict):
    voice_settings[str(user_id)] = settings
    save_all_data()
