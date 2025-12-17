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
# 3. デザイン (CSS)
# ==========================================
CUSTOM_CSS = """
<style>
    .stApp { background-color: #121212 !important; font-family: 'Helvetica Neue', Arial, sans-serif; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; max-width: 900px !important; }
    h2 { color: #e0e0e0 !important; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px !important; }

    /* 入力欄 */
    div[data-testid="stNumberInput"] label { color: #aaa !important; }
    div[data-testid="stNumberInput"] input { background-color: #000 !important; color: #fff !important; border: 1px solid #555 !important; border-radius: 4px !important; text-align: right; font-weight: bold; }
    div[data-testid="stNumberInput"] input:focus { border-color: #ffc107 !important; }

    /* ボタン */
    div.stButton > button { width: 100%; border-radius: 4px !important; font-weight: bold !important; border: none !important; padding: 0.6rem !important; margin-top: 5px; }
    div[data-testid="column"]:nth-of-type(1) div.stButton > button { background-color: #0277bd !important; color: white !important; }
    div[data-testid="column"]:nth-of-type(2) div.stButton > button { background-color: #e65100 !important; color: white !important; }

    /* --- レスポンシブグリッド --- */
    .flex-container {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        width: 100%;
        box-sizing: border-box;
    }
    .flex-full { flex: 1 1 100%; width: 100%; }
    .flex-half { flex: 1 1 45%; min-width: 320px; }

    /* カード */
    .custom-card { background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 15px; margin-bottom: 0; box-sizing: border-box; }
    .card-fx { border-left: 4px solid #009688; }
    .card-gold { border-left: 4px solid #ffc107; }
    .card-plat { border-left: 4px solid #b0bec5; }

    .card-label { font-size: 0.85rem; color: #aaa; display: flex; justify-content: space-between; margin-bottom: 5px; }
    .val-main { font-size: 2rem; font-weight: bold; font-family: monospace; text-align: right; color: #fff; line-height: 1.1; }
    .unit { font-size: 1rem; color: #666; margin-left: 5px; }

    .calc-area { border-top: 1px dashed #444; margin-top: 10px; padding-top: 10px; }
    .row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 3px; }
    .row-lbl { font-size: 0.8rem; color: #888; }
    .row-val { font-size: 1.1rem; font-weight: bold; color: #fff; font-family: monospace; }
    .diff-val { font-size: 1.2rem; font-weight: bold; font-family: monospace; }
    .plus { color: #ff5252; }
    .minus { color: #69f0ae; }

    /* 予想エリア */
    .sim-box { background: #261a1a; border: 1px solid #5d4037; padding: 15px; border-radius: 8px; margin-top: 10px; margin-bottom: 20px; }
    .sim-title { font-size: 1rem; font-weight: bold; color: #ffab91; margin-bottom: 10px; }
    .sim-grid { display: flex; flex-wrap: wrap; gap: 15px; }
    .sim-item { flex: 1 1 45%; min-width: 250px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 4px; border-left: 3px solid #555; }
    .sim-val { font-size: 1.5rem; font-weight: bold; color: #fff; text-align: right; font-family: monospace; }

    /* 履歴テーブル */
    .hist-container { margin-top: 20px; }
    .hist-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    .hist-table th { background: #2d2d2d; color: #ccc; padding: 8px; border: 1px solid #444; text-align: center; }
    .hist-table td { border: 1px solid #444; padding: 6px; text-align: center; color: #ddd; font-family: monospace; }
    .hist-row:nth-child(even) { background: #1a1a1a; }
</style>
"""

# ==========================================
# 4. メイン処理
# ==========================================
def main():
    st.set_page_config(page_title="US/OSE Monitor", layout="centered", initial_sidebar_state="collapsed")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if 'ose_g' not in st.session_state: st.session_state['ose_g'] = 13500.0
    if 'ose_p' not in st.session_state: st.session_state['ose_p'] = 4600.0

    st.markdown("<h2>🇺🇸 US/OSE Monitor & Predictor</h2>", unsafe_allow_html=True)

    # 入力エリア
    col1, col2 = st.columns(2)
    with col1:
        ose_gold = st.number_input("OSE 金 (円)", value=st.session_state['ose_g'], step=10.0, format="%.0f")
    with col2:
        ose_plat = st.number_input("OSE 白金 (円)", value=st.session_state['ose_p'], step=10.0, format="%.0f")

    # ボタンエリア
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("更新のみ", use_container_width=True):
            st.session_state['ose_g'] = ose_gold
            st.session_state['ose_p'] = ose_plat
            st.rerun()
    with c_btn2:
        save_clicked = st.button("更新＆保存", type="primary", use_container_width=True)

    # データ処理
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
            st.toast("履歴を保存しました", icon="💾")

    # 履歴ロード
    df_hist = load_history()
    last_g_spread = df_hist.iloc[0]["gDiff"] if not df_hist.empty else 0
    last_p_spread = df_hist.iloc[0]["pDiff"] if not df_hist.empty else 0
    pred_g = us_g_jpy + last_g_spread if us_g_jpy > 0 else 0
    pred_p = us_p_jpy + last_p_spread if us_p_jpy > 0 else 0

    # === HTML生成 (コメント削除済・構造修正済) ===
    
    def fmt_diff(val):
        sign = "+" if val > 0 else ""
        cls = "plus" if val > 0 else "minus"
        return f'<span class="diff-val {cls}">{sign}{val:,.0f}</span> <span style="font-size:0.9rem">円</span>'

    # 1. 為替
    html_fx = f"""
    <div class="custom-card card-fx" style="display:flex; justify-content:space-between; align-items:center; margin-top:15px;">
        <span style="font-weight:bold; color:#aaa; font-size:1rem;">USD/JPY</span>
        <div><span class="val-main" style="font-size:1.8rem;">{d['usdjpy']:.2f}</span><span class="unit">円</span></div>
    </div>
    """

    # 2. 金カード
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

    # 3. 白金カード
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

    # 4. 予想セクション
    html_pred = f"""
    <div class="sim-box">
        <div class="sim-title">🚀 OSE再開時 予想価格</div>
        <div class="sim-grid">
            <div class="sim-item" style="border-color:#ffc107;">
                <div style="font-size:0.75rem; color:#aaa;">金 (Gold)</div>
                <div class="sim-val">{pred_g:,.0f} <span style="font-size:0.9rem">円</span></div>
                <div style="text-align:right; font-size:0.75rem; color:#888;">Spread: {last_g_spread:+}</div>
            </div>
            <div class="sim-item" style="border-color:#b0bec5;">
                <div style="font-size:0.75rem; color:#aaa;">白金 (Plat)</div>
                <div class="sim-val">{pred_p:,.0f} <span style="font-size:0.9rem">円</span></div>
                <div style="text-align:right; font-size:0.75rem; color:#888;">Spread: {last_p_spread:+}</div>
            </div>
        </div>
    </div>
    """

    # 5. 履歴テーブル
    rows = ""
    if not df_hist.empty:
        for _, r in df_hist.iterrows():
            g_cls = "plus" if r['gDiff'] > 0 else "minus"
            p_cls = "plus" if r['pDiff'] > 0 else "minus"
            g_sgn = "+" if r['gDiff'] > 0 else ""
            p_sgn = "+" if r['pDiff'] > 0 else ""
            rows += f"""
            <tr class="hist-row">
                <td>{r['date']}<br>{r['time']}</td>
                <td>{r['rate']}</td>
                <td>{r['oseG']:,}</td>
                <td class="{g_cls}" style="font-weight:bold;">{g_sgn}{r['gDiff']:,}</td>
                <td>{r['oseP']:,}</td>
                <td class="{p_cls}" style="font-weight:bold;">{p_sgn}{r['pDiff']:,}</td>
            </tr>
            """
    else:
        rows = "<tr><td colspan='6' style='padding:15px;'>履歴なし</td></tr>"

    html_hist = f"""
    <div class="hist-container">
        <div style="font-weight:bold; color:#ccc; margin-bottom:8px; font-size:0.9rem;">📊 過去20日間の記録</div>
        <table class="hist-table">
            <thead>
                <tr><th>日時</th><th>為替</th><th>OSE金</th><th>差額</th><th>OSE白金</th><th>差額</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """

    # レイアウト結合
    # flex-container内に全てを収め、幅に応じて折り返させる
    html_combined = f"""
    <div class="flex-container">
        <div class="flex-full">{html_fx}</div>
        <div class="flex-half">{html_gold}</div>
        <div class="flex-half">{html_plat}</div>
        <div class="flex-full">{html_pred}</div>
        <div class="flex-full">{html_hist}</div>
    </div>
    """

    st.markdown(html_combined, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
