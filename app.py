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
# 3. CSS (Streamlit標準部品の強制整形)
# ==========================================
CUSTOM_CSS = """
<style>
    /* 全体設定 */
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
        padding-bottom: 5px; margin-bottom: 10px !important; 
        font-size: 1rem !important; white-space: nowrap; 
    }

    /* --- 強制横並び設定 --- */
    /* 4つのカラムを含むコンテナ */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; /* 絶対に折り返さない */
        gap: 5px !important;
        align-items: flex-end !important;
        width: 100% !important;
    }
    
    /* 各カラム */
    div[data-testid="column"] {
        flex: 1 1 0px !important; /* 均等幅かつ最小0 */
        min-width: 0 !important;
        width: auto !important;
    }

    /* --- 入力欄 (st.number_input) --- */
    div[data-testid="stNumberInput"] {
        min-width: 0 !important;
    }
    div[data-testid="stNumberInput"] label {
        color: #aaa !important; font-size: 0.6rem !important; 
        white-space: nowrap; margin-bottom: 0px !important;
        line-height: 1 !important;
    }
    div[data-testid="stNumberInput"] input { 
        background-color: #000 !important; color: #fff !important; 
        border: 1px solid #555 !important; border-radius: 4px !important; 
        text-align: right; font-weight: bold; 
        font-size: 0.9rem !important; padding: 0.2rem !important;
        min-width: 0 !important; width: 100% !important;
    }
    /* 増減ボタンを消す */
    div[data-testid="stNumberInput"] button { display: none !important; }
    div[data-testid="stNumberInput"] div[data-baseweb="input"] { padding: 0 !important; }

    /* --- ボタン (st.button) --- */
    div.stButton {
        min-width: 0 !important; width: 100% !important;
        padding-bottom: 2px !important; /* ベースライン調整 */
    }
    div.stButton > button { 
        width: 100% !important; min-width: 0 !important;
        border-radius: 4px !important; font-weight: bold !important; border: none !important; 
        padding: 0.35rem 0 !important; margin-top: 0px !important; 
        font-size: 0.7rem !important; white-space: nowrap; overflow: hidden; line-height: 1.2 !important;
    }
    /* 青ボタン */
    div[data-testid="column"]:nth-of-type(3) div.stButton > button { background-color: #0277bd !important; color: white !important; }
    /* オレンジボタン */
    div[data-testid="column"]:nth-of-type(4) div.stButton > button { background-color: #e65100 !important; color: white !important; }

    /* --- HTML表示部分 --- */
    .flex-row { display: flex; flex-direction: row; flex-wrap: nowrap; gap: 5px; width: 100%; margin-bottom: 5px; }
    .flex-item { flex: 1; min-width: 0; }

    .custom-card { background-color: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 8px; box-sizing: border-box; }
    .card-fx { border-left: 3px solid #009688; }
    .card-gold { border-left: 3px solid #ffc107; }
    .card-plat { border-left: 3px solid #b0bec5; }

    .card-label { font-size: 0.7rem; color: #aaa; display: flex; justify-content: space-between; margin-bottom: 2px; white-space: nowrap; overflow: hidden; }
    .val-main { font-size: 1.3rem; font-weight: bold; font-family: monospace; text-align: right; color: #fff; line-height: 1.1; white-space: nowrap; }
    .unit { font-size: 0.7rem; color: #666; margin-left: 2px; }

    .calc-area { border-top: 1px dashed #444; margin-top: 4px; padding-top: 4px; }
    .row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0px; }
    .row-lbl { font-size: 0.65rem; color: #888; white-space: nowrap; }
    .row-val { font-size: 0.85rem; font-weight: bold; color: #fff; font-family: monospace; white-space: nowrap; }
    .diff-val { font-size: 0.95rem; font-weight: bold; font-family: monospace; white-space: nowrap; }
    .plus { color: #ff5252; }
    .minus { color: #69f0ae; }

    .sim-box { background: #261a1a; border: 1px solid #5d4037; padding: 6px; border-radius: 4px; margin-bottom: 8px; }
    .sim-title { font-size: 0.75rem; font-weight: bold; color: #ffab91; margin-bottom: 4px; white-space: nowrap; }
    .sim-val { font-size: 1.1rem; font-weight: bold; color: #fff; text-align: right; font-family: monospace; white-space: nowrap; }

    .hist-container { margin-top: 10px; overflow-x: auto; }
    .hist-table { width: 100%; border-collapse: collapse; font-size: 0.65rem; }
    .hist-table th { background: #2d2d2d; color: #ccc; padding: 2px; border: 1px solid #444; text-align: center; white-space: nowrap; }
    .hist-table td { border: 1px solid #444; padding: 2px; text-align: center; color: #ddd; font-family: monospace; white-space: nowrap; }
    .hist-row:nth-child(even) { background: #1a1a1a; }
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

    st.markdown("<h2>🇺🇸 US/OSE Monitor</h2>", unsafe_allow_html=True)

    # --- 1. 入力＆ボタンエリア (4カラム) ---
    # Pythonの標準機能だけで構築（JSを使わないので確実に動く）
    # 比率は 入力:入力:ボタン:ボタン = 1.5 : 1.5 : 0.8 : 0.8 くらい
    c1, c2, c3, c4 = st.columns([1.5, 1.5, 0.8, 0.8])
    
    with c1:
        # label_visibility="visible" だが CSSでサイズ調整
        ose_gold = st.number_input("OSE 金", value=st.session_state['ose_g'], step=10.0, format="%.0f", key="in_g")
    
    with c2:
        ose_plat = st.number_input("OSE 白金", value=st.session_state['ose_p'], step=10.0, format="%.0f", key="in_p")
    
    with c3:
        update_clicked = st.button("更新", use_container_width=True)
    
    with c4:
        save_clicked = st.button("保存", use_container_width=True)

    # --- 処理ロジック ---
    if update_clicked or save_clicked:
        # 入力値をStateに保存
        st.session_state['ose_g'] = ose_gold
        st.session_state['ose_p'] = ose_plat
    
    # データ取得
    d = get_market_data()
    us_g_jpy = 0; g_diff = 0
    us_p_jpy = 0; p_diff = 0

    if d["usdjpy"] > 0:
        if d["gold"] > 0:
            us_g_jpy = (d["gold"] / OZ) * d["usdjpy"]
            g_diff = st.session_state['ose_g'] - us_g_jpy
        if d["plat"] > 0:
            us_p_jpy = (d["plat"] / OZ) * d["usdjpy"]
            p_diff = st.session_state['ose_p'] - us_p_jpy

    # 保存処理
    if save_clicked:
        if us_g_jpy > 0:
            save_history(d["usdjpy"], st.session_state['ose_g'], g_diff, st.session_state['ose_p'], p_diff)
            st.toast("保存完了", icon="💾")

    # 履歴 & 予想
    df_hist = load_history()
    last_g = df_hist.iloc[0]["gDiff"] if not df_hist.empty else 0
    last_p = df_hist.iloc[0]["pDiff"] if not df_hist.empty else 0
    pred_g = us_g_jpy + last_g if us_g_jpy > 0 else 0
    pred_p = us_p_jpy + last_p if us_p_jpy > 0 else 0

    # ==========================================
    # HTMLコンポーネント
    # ==========================================
    def fmt(val):
        cls = "plus" if val > 0 else "minus"
        sgn = "+" if val > 0 else ""
        return f'<span class="diff-val {cls}">{sgn}{val:,.0f}</span>'

    html_fx = f"""
    <div class="custom-card card-fx" style="display:flex; justify-content:space-between; align-items:center; padding:6px 10px; margin-bottom:5px; margin-top:10px;">
        <span style="font-weight:bold; color:#aaa; font-size:0.8rem;">USD/JPY</span>
        <div><span class="val-main" style="font-size:1.2rem;">{d['usdjpy']:.2f}</span><span class="unit">円</span></div>
    </div>
    """

    html_main = f"""
    <div class="flex-row">
        <div class="flex-item custom-card card-gold">
            <div class="card-label"><span>NY Gold</span><span>$/oz</span></div>
            <div class="val-main">{d['gold']:,.2f}</div>
            <div class="calc-area">
                <div class="row"><span class="row-lbl">理論</span><span class="row-val">{us_g_jpy:,.0f}</span></div>
                <div class="row" style="margin-top:2px;">
                    <span class="row-lbl">差額</span>
                    <div>{fmt(g_diff)}</div>
                </div>
            </div>
        </div>
        <div class="flex-item custom-card card-plat">
            <div class="card-label"><span>NY Plat</span><span>$/oz</span></div>
            <div class="val-main">{d['plat']:,.2f}</div>
            <div class="calc-area">
                <div class="row"><span class="row-lbl">理論</span><span class="row-val">{us_p_jpy:,.0f}</span></div>
                <div class="row" style="margin-top:2px;">
                    <span class="row-lbl">差額</span>
                    <div>{fmt(p_diff)}</div>
                </div>
            </div>
        </div>
    </div>
    """

    html_pred = f"""
    <div class="sim-box">
        <div class="sim-title">🚀 予想価格</div>
        <div class="flex-row" style="margin-bottom:0;">
            <div class="flex-item" style="background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; border-left:3px solid #ffc107;">
                <div style="font-size:0.6rem; color:#aaa;">金</div>
                <div class="sim-val">{pred_g:,.0f}</div>
            </div>
            <div class="flex-item" style="background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; border-left:3px solid #b0bec5;">
                <div style="font-size:0.6rem; color:#aaa;">白金</div>
                <div class="sim-val">{pred_p:,.0f}</div>
            </div>
        </div>
    </div>
    """

    rows = ""
    if not df_hist.empty:
        for _, r in df_hist.iterrows():
            gc = "plus" if r['gDiff'] > 0 else "minus"
            pc = "plus" if r['pDiff'] > 0 else "minus"
            gs = "+" if r['gDiff'] > 0 else ""
            ps = "+" if r['pDiff'] > 0 else ""
            rows += f"""
            <tr class="hist-row">
                <td>{r['time']}</td>
                <td>{r['rate']}</td>
                <td>{r['oseG']:,}</td>
                <td class="{gc}" style="font-weight:bold;">{gs}{r['gDiff']:,}</td>
                <td>{r['oseP']:,}</td>
                <td class="{pc}" style="font-weight:bold;">{ps}{r['pDiff']:,}</td>
            </tr>
            """
    else: rows = "<tr><td colspan='6'>履歴なし</td></tr>"

    html_hist = f"""
    <div class="hist-container">
        <div style="font-weight:bold; color:#ccc; margin-bottom:5px; font-size:0.7rem;">📊 履歴(20件)</div>
        <table class="hist-table">
            <thead><tr><th>時間</th><th>為替</th><th>金</th><th>差額</th><th>白金</th><th>差額</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """

    st.markdown(html_fx, unsafe_allow_html=True)
    st.markdown(html_main, unsafe_allow_html=True)
    st.markdown(html_pred, unsafe_allow_html=True)
    st.markdown(html_hist, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
