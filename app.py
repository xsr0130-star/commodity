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
# 3. CSS (入力欄をウィンドウ幅に100%同期させる)
# ==========================================
CUSTOM_CSS = """
<style>
    /* 全体背景 */
    .stApp { background-color: #121212 !important; color: #e0e0e0 !important; }
    
    /* 余白を極限までカット */
    .block-container { 
        padding: 0.5rem !important; 
        max-width: 100% !important; 
    }

    /* カラムの親コンテナ：絶対改行禁止 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
        align-items: flex-end !important;
        width: 100% !important;
    }
    
    /* 各カラム：幅を可変(％)にし、中身に合わせて縮む許可を出す */
    div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }

    /* --- 【最重要】入力フォームの伸縮設定 --- */
    div[data-testid="stNumberInput"] {
        width: 100% !important;
    }
    
    /* 1. ラベルを小さく固定 */
    div[data-testid="stNumberInput"] label {
        font-size: 0.65rem !important; 
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* 2. 入力欄の「+ -」ボタンを物理的に削除してスペースを確保 */
    div[data-testid="stNumberInput"] button {
        display: none !important;
    }

    /* 3. 入力欄のコンテナを伸縮自在にする */
    div[data-baseweb="input"] {
        width: 100% !important;
        min-width: 0 !important;
        padding-right: 0 !important;
    }

    /* 4. 入力エリア本体の幅を100%にし、フォントも自動縮小に対応させる */
    div[data-testid="stNumberInput"] input { 
        background-color: #000 !important; 
        color: #fff !important; 
        border: 1px solid #555 !important; 
        text-align: right !important;
        width: 100% !important;
        min-width: 0 !important;
        font-size: clamp(0.7rem, 2vw, 1rem) !important; /* 画面幅に応じてフォントも縮む */
        padding: 4px !important;
        height: 32px !important;
    }

    /* --- ボタンの伸縮設定 --- */
    div.stButton > button { 
        width: 100% !important;
        min-width: 0 !important;
        padding: 0px !important;
        height: 32px !important;
        font-size: clamp(0.6rem, 1.5vw, 0.8rem) !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
    }
    div[data-testid="column"]:nth-of-type(3) div.stButton > button { background-color: #0277bd !important; color: white !important; }
    div[data-testid="column"]:nth-of-type(4) div.stButton > button { background-color: #e65100 !important; color: white !important; }

    /* --- HTML表示部分 --- */
    .flex-row { display: flex; flex-direction: row; flex-wrap: nowrap; gap: 5px; width: 100%; margin-top: 10px;}
    .flex-item { flex: 1; min-width: 0; }
    .custom-card { background-color: #1e1e1e; border: 1px solid #333; border-radius: 6px; padding: 10px; box-sizing: border-box; }
    .card-fx { border-left: 4px solid #009688; display: flex; justify-content: space-between; align-items: center; margin-top: 10px;}
    .card-gold { border-left: 4px solid #ffc107; }
    .card-plat { border-left: 4px solid #b0bec5; }
    .val-main { font-size: clamp(1rem, 4vw, 1.6rem); font-weight: bold; font-family: monospace; text-align: right; color: #fff; line-height: 1.1; }
    .unit { font-size: 0.7rem; color: #666; }
    .calc-area { border-top: 1px dashed #444; margin-top: 5px; padding-top: 5px; }
    .row { display: flex; justify-content: space-between; align-items: baseline; }
    .row-lbl { font-size: 0.65rem; color: #888; }
    .row-val { font-size: 0.8rem; font-weight: bold; font-family: monospace; }
    .diff-val { font-size: 0.9rem; font-weight: bold; font-family: monospace; }
    .plus { color: #ff5252; }
    .minus { color: #69f0ae; }
    .sim-box { background: #261a1a; border: 1px solid #5d4037; padding: 10px; border-radius: 6px; margin-top: 10px; }
    .sim-val { font-size: 1.2rem; font-weight: bold; color: #fff; text-align: right; font-family: monospace; }
    .hist-container { margin-top: 10px; overflow-x: auto; }
    .hist-table { width: 100%; border-collapse: collapse; font-size: 0.7rem; }
    .hist-table th { background: #2d2d2d; color: #ccc; padding: 4px; border: 1px solid #444; }
    .hist-table td { border: 1px solid #444; padding: 4px; text-align: center; color: #ddd; font-family: monospace; }
</style>
"""

# ==========================================
# 4. メイン処理
# ==========================================
def main():
    st.set_page_config(page_title="US/OSE", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if 'ose_g' not in st.session_state: st.session_state['ose_g'] = 13500.0
    if 'ose_p' not in st.session_state: st.session_state['ose_p'] = 4600.0

    # 一行に「金入力」「白金入力」「更新」「保存」を無理やり並べる
    c1, c2, c3, c4 = st.columns([1, 1, 0.6, 0.6])
    with c1:
        ose_gold = st.number_input("OSE 金", value=st.session_state['ose_g'], step=10.0, format="%.0f")
    with c2:
        ose_plat = st.number_input("OSE 白金", value=st.session_state['ose_p'], step=10.0, format="%.0f")
    with c3:
        if st.button("更新"):
            st.session_state['ose_g'] = ose_gold
            st.session_state['ose_p'] = ose_plat
            st.rerun()
    with c4:
        save_clicked = st.button("保存")

    # データ取得 & 計算
    d = get_market_data()
    us_g_jpy = 0; g_diff = 0
    us_p_jpy = 0; p_diff = 0

    if d["usdjpy"] > 0:
        if d["gold"] > 0:
            us_g_jpy = (d["gold"] / OZ) * d["usdjpy"]
            g_diff = ose_gold - us_g_jpy
        if d["plat"] > 0:
            us_p_jpy = (d["plat"] / OZ) * d["usdjpy"]
            p_diff = ose_plat - us_p_jpy

    if save_clicked:
        st.session_state['ose_g'] = ose_gold
        st.session_state['ose_p'] = ose_plat
        if us_g_jpy > 0:
            save_history(d["usdjpy"], ose_gold, g_diff, ose_plat, p_diff)
            st.toast("記録済")

    # 履歴 & 予想
    df_hist = load_history()
    last_g = df_hist.iloc[0]["gDiff"] if not df_hist.empty else 0
    last_p = df_hist.iloc[0]["pDiff"] if not df_hist.empty else 0
    pred_g = us_g_jpy + last_g if us_g_jpy > 0 else 0
    pred_p = us_p_jpy + last_p if us_p_jpy > 0 else 0

    # HTML描画
    def fmt(val):
        cls = "plus" if val > 0 else "minus"
        sgn = "+" if val > 0 else ""
        return f'<span class="diff-val {cls}">{sgn}{val:,.0f}</span>'

    st.markdown(f"""
    <div class="custom-card card-fx">
        <span style="font-weight:bold; color:#aaa; font-size:0.8rem;">USD/JPY</span>
        <div class="val-main">{d['usdjpy']:.2f} <span class="unit">円</span></div>
    </div>
    
    <div class="flex-row">
        <div class="flex-item custom-card card-gold">
            <div class="card-label"><span>NY Gold</span><span>$/oz</span></div>
            <div class="val-main">{d['gold']:,.1f}</div>
            <div class="calc-area">
                <div class="row"><span class="row-lbl">理論</span><span class="row-val">{us_g_jpy:,.0f}</span></div>
                <div class="row">
                    <span class="row-lbl">差額</span>
                    <div>{fmt(g_diff)}</div>
                </div>
            </div>
        </div>
        <div class="flex-item custom-card card-plat">
            <div class="card-label"><span>NY Plat</span><span>$/oz</span></div>
            <div class="val-main">{d['plat']:,.1f}</div>
            <div class="calc-area">
                <div class="row"><span class="row-lbl">理論</span><span class="row-val">{us_p_jpy:,.0f}</span></div>
                <div class="row">
                    <span class="row-lbl">差額</span>
                    <div>{fmt(p_diff)}</div>
                </div>
            </div>
        </div>
    </div>

    <div class="sim-box">
        <div style="font-size:0.8rem; font-weight:bold; color:#ffab91; margin-bottom:5px;">🚀 予想価格</div>
        <div class="flex-row" style="margin-bottom:0;">
            <div class="flex-item" style="border-left:3px solid #ffc107; padding-left:5px;">
                <div style="font-size:0.6rem; color:#aaa;">金</div>
                <div class="sim-val">{pred_g:,.0f}</div>
            </div>
            <div class="flex-item" style="border-left:3px solid #b0bec5; padding-left:5px;">
                <div style="font-size:0.6rem; color:#aaa;">白金</div>
                <div class="sim-val">{pred_p:,.0f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 履歴
    rows = ""
    if not df_hist.empty:
        for _, r in df_hist.iterrows():
            gc = "plus" if r['gDiff'] > 0 else "minus"; pc = "plus" if r['pDiff'] > 0 else "minus"
            gs = "+" if r['gDiff'] > 0 else ""; ps = "+" if r['pDiff'] > 0 else ""
            rows += f"<tr><td>{r['time']}</td><td>{r['rate']}</td><td>{r['oseG']:,}</td><td class='{gc}'>{gs}{r['gDiff']:,}</td><td>{r['oseP']:,}</td><td class='{pc}'>{ps}{r['pDiff']:,}</td></tr>"
    
    st.markdown(f"""
    <div class="hist-container">
        <table class="hist-table">
            <thead><tr><th>時間</th><th>為替</th><th>金</th><th>差額</th><th>白金</th><th>差額</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='6'>履歴なし</td></tr>"}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
