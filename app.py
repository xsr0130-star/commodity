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
# 3. CSS (最終調整・超コンパクト版)
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

    /* --- 【重要】入力欄 & ボタンのスタイル (HTML要素を直接指定) --- */
    /* 入力フォームの親コンテナ (CSSでdisplay:flexにする) */
    div[data-testid="stForm"] > div > div {
        display: flex !important;
        flex-wrap: nowrap !important; /* 折り返し禁止 */
        gap: 5px !important; /* 隙間を詰める */
        align-items: flex-end !important; /* 底辺揃え */
        width: 100%;
    }
    
    /* 各入力欄のコンテナ */
    .ose-input-container {
        flex: 1 1 0px !important; /* 均等幅に縮む */
        min-width: 0 !important;
        width: auto !important;
    }

    /* ラベル */
    .ose-label {
        color: #aaa !important; 
        font-size: 0.65rem !important; 
        white-space: nowrap;          
        overflow: hidden;             
        text-overflow: ellipsis;
        margin-bottom: 2px !important;
        display: block; /* labelをブロック要素に */
    }

    /* 入力ボックス本体 */
    .ose-input { 
        background-color: #000 !important; 
        color: #fff !important; 
        border: 1px solid #555 !important; 
        border-radius: 4px !important; 
        text-align: right !important; 
        font-weight: bold; 
        width: 100% !important;       
        min-width: 0 !important;
        font-size: 1rem !important; 
        padding: 0.2rem 0.4rem !important; 
        height: auto !important;
        box-sizing: border-box; /* paddingを幅に含める */
    }
    .ose-input:focus { border-color: #ffc107 !important; outline: none !important; box-shadow: none !important; }

    /* ボタン */
    .stButton {
        flex: 1 1 0px !important; /* 均等幅に縮む */
        min-width: 0 !important;
        width: auto !important;
        margin-top: 0 !important; /* 上の余白を消す */
        padding: 0 !important;
    }
    div.stButton > button { 
        width: 100% !important; 
        min-width: 0 !important;
        border-radius: 4px !important; 
        font-weight: bold !important; 
        border: none !important; 
        padding: 0.5rem 0.1rem !important; /* 余白削除 */
        margin-top: 0px !important; /* 強制 */
        font-size: 0.75rem !important; 
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: clip; 
        line-height: 1.2 !important;
        height: auto !important;
    }
    /* 青ボタン */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) > div:nth-child(1) div.stButton > button { background-color: #0277bd !important; color: white !important; }
    /* オレンジボタン */
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) > div:nth-child(2) div.stButton > button { background-color: #e65100 !important; color: white !important; }


    /* --- HTML表示部分 --- */
    .flex-row {
        display: flex; flex-direction: row; flex-wrap: nowrap; gap: 5px; width: 100%; margin-bottom: 5px;
    }
    .flex-item { flex: 1; min-width: 0; }

    /* カード */
    .custom-card { background-color: #1e1e1e; border: 1px solid #333; border-radius: 4px; padding: 8px; box-sizing: border-box; }
    .card-fx { border-left: 3px solid #009688; }
    .card-gold { border-left: 3px solid #ffc107; }
    .card-plat { border-left: 3px solid #b0bec5; }

    .card-label { font-size: 0.7rem; color: #aaa; display: flex; justify-content: space-between; margin-bottom: 2px; white-space: nowrap; overflow: hidden; }
    .val-main { font-size: 1.2rem; font-weight: bold; font-family: monospace; text-align: right; color: #fff; line-height: 1.1; white-space: nowrap; }
    .unit { font-size: 0.7rem; color: #666; margin-left: 2px; }

    .calc-area { border-top: 1px dashed #444; margin-top: 4px; padding-top: 4px; }
    .row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0px; }
    .row-lbl { font-size: 0.65rem; color: #888; white-space: nowrap; }
    .row-val { font-size: 0.85rem; font-weight: bold; color: #fff; font-family: monospace; white-space: nowrap; }
    .diff-val { font-size: 0.95rem; font-weight: bold; font-family: monospace; white-space: nowrap; }
    .plus { color: #ff5252; }
    .minus { color: #69f0ae; }

    /* 予想ボックス */
    .sim-box { background: #261a1a; border: 1px solid #5d4037; padding: 6px; border-radius: 4px; margin-bottom: 8px; }
    .sim-title { font-size: 0.75rem; font-weight: bold; color: #ffab91; margin-bottom: 4px; white-space: nowrap; }
    .sim-val { font-size: 1.1rem; font-weight: bold; color: #fff; text-align: right; font-family: monospace; white-space: nowrap; }

    /* 履歴テーブル */
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
    st.set_page_config(page_title="US/OSE Monitor", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # セッション状態
    if 'ose_g' not in st.session_state: st.session_state['ose_g'] = 13500.0
    if 'ose_p' not in st.session_state: st.session_state['ose_p'] = 4600.0

    st.markdown("<h2>🇺🇸 US/OSE Monitor & Predictor</h2>", unsafe_allow_html=True)

    # --- 1. OSE入力欄とボタン (HTMLで生成し、Streamlitの値を反映) ---
    # Pythonで現在の値を渡せるように準備
    current_ose_g = st.session_state['ose_g']
    current_ose_p = st.session_state['ose_p']

    # HTML入力フォームのレンダリング
    input_html = f"""
    <div style="display:flex; flex-wrap:nowrap; gap:5px; align-items:flex-end; width:100%; margin-bottom:10px;">
        <div class="ose-input-container">
            <label for="ose-gold-input" class="ose-label">OSE 金</label>
            <input type="number" id="ose-gold-input" class="ose-input" value="{current_ose_g}" onchange="this.value = Math.round(this.value);" />
        </div>
        <div class="ose-input-container">
            <label for="ose-plat-input" class="ose-label">OSE 白金</label>
            <input type="number" id="ose-plat-input" class="ose-input" value="{current_ose_p}" onchange="this.value = Math.round(this.value);" />
        </div>
        <div class="ose-input-container">
            <button id="update-only-btn" class="stButton" style="background-color:#0277bd !important; color:white !important;">更新</button>
        </div>
        <div class="ose-input-container">
            <button id="update-save-btn" class="stButton" style="background-color:#e65100 !important; color:white !important;">保存</button>
        </div>
    </div>
    <script>
        // ボタンクリックイベントを登録
        const updateBtn = document.getElementById('update-only-btn');
        const saveBtn = document.getElementById('update-save-btn');
        const goldInput = document.getElementById('ose-gold-input');
        const platInput = document.getElementById('ose-plat-input');

        if (updateBtn) updateBtn.onclick = function() {{
            Streamlit.setComponentValue("update_action", {{gold: parseFloat(goldInput.value), plat: parseFloat(platInput.value), save: false}});
        }};
        if (saveBtn) saveBtn.onclick = function() {{
            Streamlit.setComponentValue("update_action", {{gold: parseFloat(goldInput.value), plat: parseFloat(platInput.value), save: true}});
        }};
    </script>
    """
    st.components.v1.html(input_html, height=100) # StreamlitにHTMLを埋め込む

    # Streamlitのコンポーネントからのコールバックを受け取る
    update_action = st.experimental_get_query_params().get("update_action")
    if update_action:
        # クエリパラメータはリストで来るので最初の要素を取得し、JSON文字列をパース
        action_data = json.loads(update_action[0])
        ose_gold = action_data["gold"]
        ose_plat = action_data["plat"]
        save_clicked = action_data["save"]
        
        st.session_state['ose_g'] = ose_gold
        st.session_state['ose_p'] = ose_plat

        if save_clicked:
            # データを取得して保存
            d = get_market_data() # 最新データを再度取得
            us_g_jpy = (d["gold"] / OZ) * d["usdjpy"] if d["gold"] > 0 and d["usdjpy"] > 0 else 0
            g_diff = ose_gold - us_g_jpy if us_g_jpy > 0 else 0
            us_p_jpy = (d["plat"] / OZ) * d["usdjpy"] if d["plat"] > 0 and d["usdjpy"] > 0 else 0
            p_diff = ose_plat - us_p_jpy if us_p_jpy > 0 else 0

            if us_g_jpy > 0:
                save_history(d["usdjpy"], ose_gold, g_diff, ose_plat, p_diff)
                st.toast("保存!", icon="💾")
        st.experimental_set_query_params() # クエリパラメータをクリア
        st.rerun() # 画面を再描画して最新状態に


    # --- データ取得 & 計算 (ここはHTML表示に使う値なので常に実行) ---
    d = get_market_data()
    ose_gold = st.session_state['ose_g'] # 最新の入力値を使う
    ose_plat = st.session_state['ose_p'] # 最新の入力値を使う

    us_g_jpy = 0; g_diff = 0
    us_p_jpy = 0; p_diff = 0

    if d["usdjpy"] > 0:
        if d["gold"] > 0:
            us_g_jpy = (d["gold"] / OZ) * d["usdjpy"]
            g_diff = ose_gold - us_g_jpy
        if d["plat"] > 0:
            us_p_jpy = (d["plat"] / OZ) * d["usdjpy"]
            p_diff = ose_plat - us_p_jpy
            
    # 履歴 & 予想
    df_hist = load_history()
    last_g = df_hist.iloc[0]["gDiff"] if not df_hist.empty else 0
    last_p = df_hist.iloc[0]["pDiff"] if not df_hist.empty else 0
    pred_g = us_g_jpy + last_g if us_g_jpy > 0 else 0
    pred_p = us_p_jpy + last_p if us_p_jpy > 0 else 0

    # ==========================================
    # HTMLコンポーネント (Flexbox)
    # ==========================================
    def fmt(val):
        cls = "plus" if val > 0 else "minus"
        sgn = "+" if val > 0 else ""
        return f'<span class="diff-val {cls}">{sgn}{val:,.0f}</span>'

    # 為替
    html_fx = f"""
    <div class="custom-card card-fx" style="display:flex; justify-content:space-between; align-items:center; padding:6px 10px; margin-bottom:5px; margin-top:10px;">
        <span style="font-weight:bold; color:#aaa; font-size:0.8rem;">USD/JPY</span>
        <div><span class="val-main" style="font-size:1.2rem;">{d['usdjpy']:.2f}</span><span class="unit">円</span></div>
    </div>
    """

    # 金・白金 (横並び)
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

    # 予想 (横並び)
    html_pred = f"""
    <div class="sim-box">
        <div class="sim-title">🚀 予想価格 <span style="font-weight:normal; font-size:0.7rem; color:#888;">(現在値+最終差額)</span></div>
        <div class="flex-row" style="margin-bottom:0;">
            <div class="flex-item" style="background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; border-left:3px solid #ffc107;">
                <div style="font-size:0.65rem; color:#aaa;">金</div>
                <div class="sim-val">{pred_g:,.0f}</div>
            </div>
            <div class="flex-item" style="background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; border-left:3px solid #b0bec5;">
                <div style="font-size:0.65rem; color:#aaa;">白金</div>
                <div class="sim-val">{pred_p:,.0f}</div>
            </div>
        </div>
    </div>
    """

    # 履歴
    rows_html = ""
    if not df_hist.empty:
        for _, r in df_hist.iterrows():
            gc = "plus" if r['gDiff'] > 0 else "minus"
            pc = "plus" if r['pDiff'] > 0 else "minus"
            gs = "+" if r['gDiff'] > 0 else ""
            ps = "+" if r['pDiff'] > 0 else ""
            rows_html += f"""
            <tr class="hist-row">
                <td>{r['time']}</td>
                <td>{r['rate']}</td>
                <td>{r['oseG']:,}</td>
                <td class="{gc}" style="font-weight:bold;">{gs}{r['gDiff']:,}</td>
                <td>{r['oseP']:,}</td>
                <td class="{pc}" style="font-weight:bold;">{ps}{r['pDiff']:,}</td>
            </tr>
            """
    else: rows_html = "<tr><td colspan='6'>履歴なし</td></tr>"

    html_hist = f"""
    <div class="hist-container">
        <div style="font-weight:bold; color:#ccc; margin-bottom:5px; font-size:0.8rem;">📊 履歴(20件)</div>
        <table class="hist-table">
            <thead><tr><th>時間</th><th>為替</th><th>金</th><th>差額</th><th>白金</th><th>差額</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """

    st.markdown(html_fx, unsafe_allow_html=True)
    st.markdown(html_main, unsafe_allow_html=True)
    st.markdown(html_pred, unsafe_allow_html=True)
    st.markdown(html_hist, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
