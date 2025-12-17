import streamlit as st
import requests
import pandas as pd
import datetime
import os

# ==========================================
# 設定 & 定数
# ==========================================
OZ = 31.1034768
HISTORY_FILE = "arb_history.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ==========================================
# 1. データ取得
# ==========================================
def get_market_data():
    data = {"usdjpy": 0.0, "gold": 0.0, "plat": 0.0}
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
        data["usdjpy"] = r.json()["rates"]["JPY"]
    except: pass
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", headers=HEADERS, timeout=3)
        data["gold"] = r.json()["pax-gold"]["usd"]
    except: pass
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/PL=F?interval=1d&range=1d"
        r = requests.get(url, headers=HEADERS, timeout=3)
        data["plat"] = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except: pass
    return data

# ==========================================
# 2. 履歴管理
# ==========================================
def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame()

def save_history(usdjpy, ose_g, g_diff, ose_p, p_diff):
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
    else:
        df = pd.DataFrame(columns=["date", "time", "rate", "oseG", "gDiff", "oseP", "pDiff"])

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')

    new_row = {
        "date": date_str, "time": time_str, "rate": f"{usdjpy:.2f}",
        "oseG": int(ose_g), "gDiff": int(g_diff),
        "oseP": int(ose_p), "pDiff": int(p_diff)
    }

    df = df[df["date"] != date_str]
    df_new = pd.DataFrame([new_row])
    df = pd.concat([df_new, df], ignore_index=True)
    df = df.head(20)
    df.to_csv(HISTORY_FILE, index=False)
    return df

# ==========================================
# 3. CSS (超コンパクト・強制横並び版)
# ==========================================
CUSTOM_CSS = """
<style>
    /* 全体設定: 余白を極限まで削る */
    .stApp { background-color: #121212 !important; font-family: 'Helvetica Neue', Arial, sans-serif; }
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 1rem !important; 
        padding-left: 0.2rem !important;
        padding-right: 0.2rem !important;
        max-width: 100% !important; 
    }
    
    h2 { 
        color: #e0e0e0 !important; 
        border-bottom: 1px solid #333; 
        padding-bottom: 5px; 
        margin-bottom: 10px !important; 
        font-size: 1rem !important; 
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* =========================================
       超強力・強制横並びレイアウト
       ========================================= */
    
    /* カラムの親コンテナ: 折り返し禁止 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 4px !important; /* 隙間も最小限 */
        align-items: flex-end !important;
        width: 100% !important;
        overflow: hidden !important; /* スクロールバーを出さない */
    }
    
    /* 各カラム: 最小幅0、縮小許可 */
    div[data-testid="column"] {
        flex: 1 1 0px !important;
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }

    /* --- 入力フォームの超小型化 --- */
    div[data-testid="stNumberInput"] {
        min-width: 0 !important;
    }
    
    /* ラベル */
    div[data-testid="stNumberInput"] label {
        color: #aaa !important; 
        font-size: 0.6rem !important; 
        white-space: nowrap;          
        margin-bottom: 0px !important;
        width: 100%;
        overflow: hidden;
    }

    /* 入力ボックス */
    div[data-testid="stNumberInput"] input { 
        background-color: #000 !important; 
        color: #fff !important; 
        border: 1px solid #555 !important; 
        border-radius: 4px !important; 
        text-
