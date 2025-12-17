import streamlit as st
import requests
import pandas as pd
import datetime
import os

# ==========================================
# 設定 & 定数
# ==========================================
OZ = 31.1034768  # 1トロイオンス
HISTORY_FILE = "arb_history.csv"

# APIヘッダー (ブロック回避用)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ==========================================
# 1. データ取得ロジック
# ==========================================
def get_market_data():
    data = {"usdjpy": 0.0, "gold": 0.0, "plat": 0.0}

    # 1. 為替 (ExchangeRate-API)
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
        data["usdjpy"] = r.json()["rates"]["JPY"]
    except: pass

    # 2. 金 (CoinGecko - PAXG)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", headers=HEADERS, timeout=3)
        data["gold"] = r.json()["pax-gold"]["usd"]
    except: pass

    # 3. 白金 (Yahoo Finance US - 先物 PL=F)
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/PL=F?interval=1d&range=1d"
        r = requests.get(url, headers=HEADERS, timeout=3)
        data["plat"] = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except: pass

    return data

# ==========================================
# 2. 履歴管理ロジック (CSV)
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

    # 同日上書き
    df = df[df["date"] != date_str]
    # 先頭に追加
    df_new = pd.DataFrame([new_row])
    df = pd.concat([df_new, df], ignore_index=True)
    # 20件制限
    df = df.head(20)
    
    df.to_csv(HISTORY_FILE, index=False)
    return df

# ==========================================
# 3. UI (CSSスタイル定義)
# ==========================================
# HTML版と同じデザインにするためのCSS
CUSTOM_CSS = """
<style>
    /* 全体の背景とフォント */
    .stApp { background-color: #121212; color: #e0e0e0; font-family: 'Helvetica Neue', Arial, sans-serif; }
    
    /* カードデザイン */
    .custom-card {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        position: relative;
    }
    .card-fx { border-left: 5px solid #009688; }
    .card-gold { border-left: 5px solid #ffc107; }
    .card-plat { border-left: 5px solid #b0bec5; }
    
    /* テキストスタイル */
    .card-label { font-size: 0.8rem; color: #aaa; display: flex; justify-content: space-between; margin-bottom: 5px; }
    .val-main { font-size: 1.8rem; font-weight: bold; font-family: monospace; text-align: right; color: #fff; margin: 0; line-height: 1.2; }
    .unit { font-size: 0.9rem; color: #666; margin-left: 5px; }
    
    /* 計算エリア */
    .calc-area { border-top: 1px dashed #444; margin-top: 8px; padding-top: 8px; }
    .row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 2px; }
    .row-lbl { font-size: 0.75rem; color: #888; }
    .row-val { font-size: 1rem; font-weight: bold; color: #fff; font-family: monospace; }
    .diff-val { font-size: 1.1rem; font-weight: bold; font-family: monospace; }
    .plus { color: #ff5252; }
    .minus { color: #69f0ae; }

    /* 予想エリア */
    .sim-box { background: #261a1a; border: 1px solid #5d4037; padding: 10px; border-radius: 6px; margin-bottom: 20px; }
    .sim-title { font-size: 0.9rem; font-weight: bold; color: #ffab91; margin-bottom: 5px; }
    .sim-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .sim-item { background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; border-left: 3px solid #555; }
    .sim-val { font-size: 1.4rem; font-weight: bold; color: #fff; text-align: right; }
    
    /* 履歴テーブル */
    .hist-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
    .hist-table th { background: #2d2d2d; color: #ccc; padding: 6px; border: 1px solid #444; text-align: center; }
    .hist-table td { border: 1px solid #444; padding: 6px; text-align: center; color: #ddd; }
    .hist-row:nth-child(even) { background: #1a1a1a; }
    
    /* Streamlit標準の余白を消す */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 900px; }
    div[data-testid="stNumberInput"] label { font-size: 0.8rem; color: #aaa; }
</style>
"""

# ==========================================
# 4. メインアプリ
# ==========================================
def main():
    st.set_page_config(page_title="US/OSE Monitor", layout="centered")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # セッション状態（入力値保持）
    if 'ose_g' not in st.session_state: st.session_state['ose_g'] = 13500.0
    if 'ose_p' not in st.session_state: st.session_state['ose_p'] = 4600.0

    st.markdown("<h2 style='margin:0 0 15px 0; font-size:1.4rem;'>🇺🇸 US/OSE Monitor & Predictor</h2>", unsafe_allow_html=True)

    # --- 入力 & ボタン ---
    col1, col2, col3 = st.columns([1.5, 1.5, 2])
    with col1:
        ose_gold = st.number_input("OSE 金 (円)", value=st.session_state['ose_g'], step=10.0, format="%.0f")
    with col2:
        ose_plat = st.number_input("OSE 白金 (円)", value=st.session_state['ose_p'], step=10.0, format="%.0f")
    with col3:
        st.write("") # スペーサー
        st.write("")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("更新のみ", use_container_width=True):
                st.session_state['ose_g'] = ose_gold
                st.session_state['ose_p'] = ose_plat
                st.rerun()
        with c_b2:
            save_clicked = st.button("更新＆保存", type="primary", use_container_width=True)

    # --- データ取得 ---
    d = get_market_data()

    # 計算
    us_g_jpy = 0; g_diff = 0
    us_p_jpy = 0; p_diff = 0

    if d["usdjpy"] > 0:
        if d["gold"] > 0:
            us_g_jpy = (d["gold"] / OZ) * d["usdjpy"]
            g_diff = ose_gold - us_g_jpy
        if d["plat"] > 0:
            us_p_jpy = (d["plat"] / OZ) * d["usdjpy"]
            p_diff = ose_plat - us_p_jpy

    # 保存処理
    if save_clicked:
        st.session_state['ose_g'] = ose_gold
        st.session_state['ose_p'] = ose_plat
        if us_g_jpy > 0:
            save_history(d["usdjpy"], ose_gold, g_diff, ose_plat, p_diff)
            st.toast("履歴を保存しました", icon="💾")

    # --- 履歴読み込み (予想用) ---
    df_hist = load_history()
    last_g_spread = df_hist.iloc[0]["gDiff"] if not df_hist.empty else 0
    last_p_spread = df_hist.iloc[0]["pDiff"] if not df_hist.empty else 0

    # 予想価格計算
    pred_g = us_g_jpy + last_g_spread if us_g_jpy > 0 else 0
    pred_p = us_p_jpy + last_p_spread if us_p_jpy > 0 else 0

    # ==========================================
    # 5. HTMLコンポーネントの構築 (コンパクト表示)
    # ==========================================
    
    # フォーマット関数
    def fmt_diff(val):
        sign = "+" if val > 0 else ""
        cls = "plus" if val > 0 else "minus"
        return f'<span class="diff-val {cls}">{sign}{val:,.0f}</span> <span style="font-size:0.8rem">円</span>'

    # 為替カードHTML
    html_fx = f"""
    <div class="custom-card card-fx" style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:bold; color:#aaa;">USD/JPY</span>
        <div><span class="val-main">{d['usdjpy']:.2f}</span><span class="unit">円</span></div>
    </div>
    """

    # 金カードHTML
    html_gold = f"""
    <div class="custom-card card-gold">
        <div class="card-label"><span>NY Gold</span><span>$/oz</span></div>
        <div class="val-main">{d['gold']:,.2f}</div>
        <div class="calc-area">
            <div class="row"><span class="row-lbl">理論価格</span><span class="row-val">{us_g_jpy:,.0f} 円</span></div>
            <div class="row" style="margin-top:5px; align-items:center;">
                <span class="row-lbl">OSE差額</span>
                <div>{fmt_diff(g_diff)}</div>
            </div>
        </div>
    </div>
    """

    # 白金カードHTML
    html_plat = f"""
    <div class="custom-card card-plat">
        <div class="card-label"><span>NY Platinum</span><span>$/oz</span></div>
        <div class="val-main">{d['plat']:,.2f}</div>
        <div class="calc-area">
            <div class="row"><span class="row-lbl">理論価格</span><span class="row-val">{us_p_jpy:,.0f} 円</span></div>
            <div class="row" style="margin-top:5px; align-items:center;">
                <span class="row-lbl">OSE差額</span>
                <div>{fmt_diff(p_diff)}</div>
            </div>
        </div>
    </div>
    """

    # 予想セクションHTML
    html_pred = f"""
    <div class="sim-box">
        <div class="sim-title">🚀 OSE再開時 予想価格 <span style="font-weight:normal; font-size:0.8rem; color:#aaa;">(理論値 + 最終記録スプレッド)</span></div>
        <div class="sim-grid">
            <div class="sim-item" style="border-color:#ffc107;">
                <div style="font-size:0.7rem; color:#aaa;">金 (Gold)</div>
                <div class="sim-val">{pred_g:,.0f} <span style="font-size:0.9rem">円</span></div>
                <div style="text-align:right; font-size:0.7rem; color:#888;">Spread: {last_g_spread:+}</div>
            </div>
            <div class="sim-item" style="border-color:#b0bec5;">
                <div style="font-size:0.7rem; color:#aaa;">白金 (Plat)</div>
                <div class="sim-val">{pred_p:,.0f} <span style="font-size:0.9rem">円</span></div>
                <div style="text-align:right; font-size:0.7rem; color:#888;">Spread: {last_p_spread:+}</div>
            </div>
        </div>
    </div>
    """

    # 履歴テーブルHTML構築
    rows_html = ""
    if not df_hist.empty:
        for _, row in df_hist.iterrows():
            g_cls = "plus" if row['gDiff'] > 0 else "minus"
            p_cls = "plus" if row['pDiff'] > 0 else "minus"
            g_sign = "+" if row['gDiff'] > 0 else ""
            p_sign = "+" if row['pDiff'] > 0 else ""
            
            rows_html += f"""
            <tr class="hist-row">
                <td>{row['date']}<br>{row['time']}</td>
                <td>{row['rate']}</td>
                <td>{row['oseG']:,}</td>
                <td class="{g_cls}" style="font-weight:bold;">{g_sign}{row['gDiff']:,}</td>
                <td>{row['oseP']:,}</td>
                <td class="{p_cls}" style="font-weight:bold;">{p_sign}{row['pDiff']:,}</td>
            </tr>
            """
    else:
        rows_html = "<tr><td colspan='6' style='padding:10px;'>履歴なし</td></tr>"

    html_hist = f"""
    <div style="margin-top:20px;">
        <div style="font-weight:bold; color:#ccc; margin-bottom:5px;">📊 過去20日間の記録</div>
        <table class="hist-table">
            <thead>
                <tr><th>日時</th><th>為替</th><th>OSE金</th><th>差額</th><th>OSE白金</th><th>差額</th></tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """

    # --- 描画実行 ---
    st.markdown(html_fx, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1: st.markdown(html_gold, unsafe_allow_html=True)
    with c2: st.markdown(html_plat, unsafe_allow_html=True)
    
    st.markdown(html_pred, unsafe_allow_html=True)
    st.markdown(html_hist, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
