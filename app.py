import streamlit as st
import requests
import pandas as pd
import datetime
import os
import time

# ==========================================
# 設定 & 定数
# ==========================================
OZ = 31.1034768  # 1トロイオンス
HISTORY_FILE = "arb_history.csv" # 履歴保存ファイル

# ブラウザのふりをするヘッダー (ブロック回避用)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ==========================================
# データ取得関数
# ==========================================
def get_market_data():
    data = {"usdjpy": 0.0, "gold": 0.0, "plat": 0.0}

    # 1. 為替 (ExchangeRate-API)
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
        data["usdjpy"] = r.json()["rates"]["JPY"]
    except: pass

    # 2. 金 (CoinGecko - PAXG) - 最も安定
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
# 履歴管理関数
# ==========================================
def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    else:
        return pd.DataFrame(columns=["日付", "時刻", "為替", "OSE金", "金差額", "OSE白金", "白金差額", "最終金スプレッド", "最終白金スプレッド"])

def save_history_log(usdjpy, ose_g, g_diff, ose_p, p_diff):
    df = load_history()
    
    # 日本時間取得
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    today_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M')

    new_row = {
        "日付": today_str,
        "時刻": time_str,
        "為替": f"{usdjpy:.2f}",
        "OSE金": int(ose_g),
        "金差額": int(g_diff),
        "OSE白金": int(ose_p),
        "白金差額": int(p_diff),
        "最終金スプレッド": int(g_diff),   # 予想計算用に数値として保持
        "最終白金スプレッド": int(p_diff) # 予想計算用に数値として保持
    }

    # 同じ日付のデータがあれば削除（上書き用）
    df = df[df["日付"] != today_str]
    
    # 新しい行を先頭に追加
    df_new = pd.DataFrame([new_row])
    df = pd.concat([df_new, df], ignore_index=True)
    
    # 20件制限
    df = df.head(20)
    
    df.to_csv(HISTORY_FILE, index=False)
    return df

# ==========================================
# メインアプリ
# ==========================================
def main():
    st.set_page_config(page_title="US/OSE Monitor", layout="wide")
    
    st.title("🇺🇸 US/OSE リアルタイム裁定モニター")

    # --- Session State 初期化 (入力値保持のため) ---
    if 'ose_g' not in st.session_state: st.session_state['ose_g'] = 13500.0
    if 'ose_p' not in st.session_state: st.session_state['ose_p'] = 4600.0

    # ==========================================
    # 1. OSE入力 & アクションボタン
    # ==========================================
    with st.container():
        st.subheader("🇯🇵 日本 OSE (手入力)")
        col_in1, col_in2, col_btn = st.columns([2, 2, 3])
        
        with col_in1:
            ose_gold = st.number_input("OSE 金 (円/g)", value=st.session_state['ose_g'], step=10.0, format="%.0f", key="input_g")
        
        with col_in2:
            ose_plat = st.number_input("OSE 白金 (円/g)", value=st.session_state['ose_p'], step=10.0, format="%.0f", key="input_p")
        
        with col_btn:
            st.write("") # 余白調整
            st.write("")
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                # 更新のみ（保存しない）
                if st.button("🔄 データ更新のみ", type="secondary", use_container_width=True):
                    st.session_state['ose_g'] = ose_gold
                    st.session_state['ose_p'] = ose_plat
                    st.rerun()
            with c_btn2:
                # 更新＆保存
                save_clicked = st.button("💾 更新 & 履歴保存", type="primary", use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 2. データ取得 & 計算
    # ==========================================
    with st.spinner('US市場データを取得中...'):
        d = get_market_data()

    # 計算
    us_gold_jpy = 0
    us_plat_jpy = 0
    g_diff = 0
    p_diff = 0

    if d["usdjpy"] > 0:
        if d["gold"] > 0:
            us_gold_jpy = (d["gold"] / OZ) * d["usdjpy"]
            g_diff = ose_gold - us_gold_jpy
        if d["plat"] > 0:
            us_plat_jpy = (d["plat"] / OZ) * d["usdjpy"]
            p_diff = ose_plat - us_plat_jpy

    # 保存ボタンが押された場合の処理
    if save_clicked:
        st.session_state['ose_g'] = ose_gold
        st.session_state['ose_p'] = ose_plat
        if us_gold_jpy > 0 and us_plat_jpy > 0:
            save_history_log(d["usdjpy"], ose_gold, g_diff, ose_plat, p_diff)
            st.success("履歴を保存しました")

    # ==========================================
    # 3. メイン表示 (左: US情報 / 右: 差額・予想)
    # ==========================================
    col_main_l, col_main_r = st.columns(2)

    # --- 左側：US市場価格 ---
    with col_main_l:
        st.header("🇺🇸 US市場 (Realtime)")
        
        # 為替
        st.metric(label="1. ドル円 (USD/JPY)", value=f"{d['usdjpy']:.2f} 円")
        
        st.markdown("---")
        
        # 金
        st.subheader("2. 金 (NY Gold)")
        st.metric(label="ドル建て価格", value=f"${d['gold']:,.2f}")
        st.info(f"理論価格 (税抜): {us_gold_jpy:,.0f} 円/g")

        st.markdown("---")

        # 白金
        st.subheader("3. 白金 (NY Platinum)")
        st.metric(label="ドル建て価格", value=f"${d['plat']:,.2f}")
        st.info(f"理論価格 (税抜): {us_plat_jpy:,.0f} 円/g")

    # --- 右側：OSE差額 & 予想 ---
    with col_main_r:
        st.header("📊 OSE差額 & 夜間予想")

        # 履歴読み込み (予想計算用)
        df_hist = load_history()
        last_g_spread = 0
        last_p_spread = 0
        if not df_hist.empty:
            last_g_spread = df_hist.iloc[0]["最終金スプレッド"]
            last_p_spread = df_hist.iloc[0]["最終白金スプレッド"]

        # 空白調整
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        # 金 差額 & 予想
        st.markdown("#### 金 (Gold) 状況")
        if g_diff > 0:
            st.error(f"現在、OSEが {g_diff:,.0f} 円 割高 (Premium)")
        else:
            st.success(f"現在、OSEが {abs(g_diff):,.0f} 円 割安 (Discount)")
        
        # 予想表示
        pred_g = us_gold_jpy + last_g_spread
        st.markdown(f"""
        <div style="background-color:#333; padding:10px; border-radius:5px; border-left:5px solid #ffc107;">
            <small>🚀 OSE再開時 予想価格 (理論値 + 最終記録スプレッド)</small><br>
            <span style="font-size:1.5em; font-weight:bold; color:#fff;">{pred_g:,.0f} 円</span>
            <br><small style="color:#aaa;">(最終記録スプレッド: {last_g_spread:+} 円)</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 白金 差額 & 予想
        st.markdown("#### 白金 (Platinum) 状況")
        if p_diff > 0:
            st.error(f"現在、OSEが {p_diff:,.0f} 円 割高 (Premium)")
        else:
            st.success(f"現在、OSEが {abs(p_diff):,.0f} 円 割安 (Discount)")

        # 予想表示
        pred_p = us_plat_jpy + last_p_spread
        st.markdown(f"""
        <div style="background-color:#333; padding:10px; border-radius:5px; border-left:5px solid #b0bec5;">
            <small>🚀 OSE再開時 予想価格 (理論値 + 最終記録スプレッド)</small><br>
            <span style="font-size:1.5em; font-weight:bold; color:#fff;">{pred_p:,.0f} 円</span>
            <br><small style="color:#aaa;">(最終記録スプレッド: {last_p_spread:+} 円)</small>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # 4. 履歴ログテーブル
    # ==========================================
    st.markdown("---")
    st.subheader("📝 過去20日間の記録 (最終更新値)")
    
    if not df_hist.empty:
        # 表示用にカラムを整理
        display_df = df_hist[["日付", "時刻", "為替", "OSE金", "金差額", "OSE白金", "白金差額"]]
        
        # 色付けロジック (Pandas Styler)
        def color_diff(val):
            color = '#ff5252' if val > 0 else '#69f0ae' # 赤:割高, 緑:割安
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            display_df.style.map(color_diff, subset=["金差額", "白金差額"]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("履歴はまだありません。「更新 & 履歴保存」ボタンを押すと記録されます。")

if __name__ == "__main__":
    main()
