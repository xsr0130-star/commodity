import streamlit as st
import requests
import pandas as pd
import datetime
import os

# ==========================================
# 設定
# ==========================================
OZ = 31.1034768            # 1トロイオンス
HISTORY_FILE = "price_history.csv"

# ヘッダー (Sina Finance等のブロック回避用)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn/",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8"
}

# ==========================================
# データ取得ロジック
# ==========================================

def get_china_data_robust():
    """
    中国市場データを取得
    nf_au0 : 上海金 (主力連続)
    nf_pt0 : 広州白金 (主力連続) -> 自動で最新の主力限月を参照します
    """
    gold = 0.0
    plat = 0.0

    try:
        # nf_au0=上海金, nf_pt0=広州白金(自動)
        url = f"https://hq.sinajs.cn/list=nf_au0,nf_pt0"
        r = requests.get(url, headers=HEADERS, timeout=3)
        r.encoding = 'gbk'
        text = r.text
        
        # --- 金 (SHFE) ---
        if "nf_au0" in text:
            try:
                parts = text.split('var hq_str_nf_au0="')[1].split('";')[0].split(',')
                # Index 8: Latest Transaction, Index 5: Last Close/Price
                p = float(parts[8]) if float(parts[8]) > 0 else float(parts[5])
                if p > 0: gold = p
            except: pass

        # --- 白金 (GFEX) ---
        if "nf_pt0" in text:
            try:
                parts = text.split('var hq_str_nf_pt0="')[1].split('";')[0].split(',')
                # Index 8 or 5
                p = float(parts[8]) if float(parts[8]) > 0 else float(parts[5])
                if p > 0: plat = p
            except: pass
            
    except Exception as e:
        print(f"Sina Error: {e}")

    # 万が一 nf_pt0 (連続足) がまだ配信されていない場合のバックアップ
    # 特定の限月(2606など)を決め打ちで確認するロジックを入れることも可能ですが、
    # 基本的に nf_pt0 が最も安全です。
    
    return gold, plat

def get_market_data():
    data = {
        "usdjpy": 0.0, "cnyjpy": 0.0,
        "us_gold": 0.0, "us_plat": 0.0,
        "cn_gold": 0.0, "cn_plat": 0.0
    }

    # 1. 為替
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
        d = r.json()
        data["usdjpy"] = d["rates"]["JPY"]
        data["cnyjpy"] = data["usdjpy"] / d["rates"]["CNY"]
    except: pass

    # 2. US市場
    try:
        # Gold (CoinGecko)
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", headers=HEADERS, timeout=3)
        data["us_gold"] = r.json()["pax-gold"]["usd"]
    except: pass
    
    try:
        # Plat (Yahoo)
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/PL=F?interval=1d&range=1d", headers=HEADERS, timeout=3)
        data["us_plat"] = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except: pass

    # 3. 中国市場
    data["cn_gold"], data["cn_plat"] = get_china_data_robust()

    return data

# ==========================================
# 履歴管理ロジック
# ==========================================
def update_history(ose_g, ose_p, us_g_jpy, us_p_jpy, cn_g_jpy, cn_p_jpy):
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    today_str = datetime.datetime.now(JST).strftime('%Y-%m-%d')
    time_str = datetime.datetime.now(JST).strftime('%H:%M')

    new_row = {
        "日付": today_str,
        "時刻": time_str,
        "OSE金": round(ose_g),
        "US金(換算)": round(us_g_jpy),
        "中国金(換算)": round(cn_g_jpy),
        "OSE白金": round(ose_p),
        "US白金(換算)": round(us_p_jpy),
        "中国白金(換算)": round(cn_p_jpy)
    }

    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
    else:
        df = pd.DataFrame(columns=new_row.keys())

    # 同日データの更新ロジック
    df = df[df["日付"] != today_str]
    df_new = pd.DataFrame([new_row])
    df = pd.concat([df_new, df], ignore_index=True)
    df = df.head(20)
    df.to_csv(HISTORY_FILE, index=False)
    
    return df

# ==========================================
# メイン画面
# ==========================================
def main():
    st.set_page_config(page_title="Gold/Plat Monitor", layout="wide")
    st.title("🌏 リアルタイム裁定モニター")
    
    # --- 入力エリア ---
    st.markdown("### 🇯🇵 日本 OSE (円建て/手入力)")
    input_c1, input_c2, input_c3 = st.columns([1.5, 1.5, 1])
    
    with input_c1:
        ose_gold = st.number_input("OSE 金標準 (円/g)", value=13500.0, step=10.0, format="%.0f")
    with input_c2:
        ose_plat = st.number_input("OSE 白金標準 (円/g)", value=4600.0, step=10.0, format="%.0f")
    with input_c3:
        st.write("") 
        st.write("") 
        if st.button("データ更新 & 記録", type="primary"):
            st.rerun()

    st.markdown("---")

    # データ取得
    d = get_market_data()

    # 計算
    us_gold_jpy = (d["us_gold"] / OZ) * d["usdjpy"] if d["us_gold"] and d["usdjpy"] else 0
    us_plat_jpy = (d["us_plat"] / OZ) * d["usdjpy"] if d["us_plat"] and d["usdjpy"] else 0
    cn_gold_jpy = d["cn_gold"] * d["cnyjpy"] if d["cn_gold"] and d["cnyjpy"] else 0
    cn_plat_jpy = d["cn_plat"] * d["cnyjpy"] if d["cn_plat"] and d["cnyjpy"] else 0

    # 履歴保存
    if us_gold_jpy > 0 or cn_gold_jpy > 0:
        df_history = update_history(ose_gold, ose_plat, us_gold_jpy, us_plat_jpy, cn_gold_jpy, cn_plat_jpy)
    else:
        if os.path.exists(HISTORY_FILE):
            df_history = pd.read_csv(HISTORY_FILE)
        else:
            df_history = pd.DataFrame()

    # --- カラム表示 ---
    col_us, col_cn = st.columns(2)

    # === 左：ドル建て ===
    with col_us:
        st.header("🇺🇸 米国市場 (ドル建て)")
        if d["usdjpy"]: st.metric("ドル円", f"{d['usdjpy']:.2f} 円")
        else: st.error("為替取得中...")
        
        st.markdown("---")
        
        # 金
        st.subheader("金 (NY Gold)")
        if d["us_gold"]:
            st.metric("NY価格", f"${d['us_gold']:,.2f}")
            st.info(f"理論価格: {us_gold_jpy:,.0f} 円/g")
            diff = ose_gold - us_gold_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗")

        st.markdown("---")

        # 白金
        st.subheader("白金 (NY Plat)")
        if d["us_plat"]:
            st.metric("NY価格", f"${d['us_plat']:,.2f}")
            st.info(f"理論価格: {us_plat_jpy:,.0f} 円/g")
            diff = ose_plat - us_plat_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗")

    # === 右：元建て ===
    with col_cn:
        st.header("🇨🇳 中国市場 (元建て)")
        if d["cnyjpy"]: st.metric("元円", f"{d['cnyjpy']:.2f} 円")
        else: st.error("為替取得中...")
        
        st.markdown("---")

        # 金
        st.subheader("金 (上海 Au)")
        if d["cn_gold"] > 0:
            st.metric("上海価格", f"{d['cn_gold']:,.2f} 元/g")
            st.info(f"換算価格: {cn_gold_jpy:,.0f} 円/g")
            diff = ose_gold - cn_gold_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗 (Sina)")

        st.markdown("---")

        # 白金 (ここが自動更新版)
        st.subheader(f"白金 (広州 主力限月)")
        if d["cn_plat"] > 0:
            st.metric("広州価格", f"{d['cn_plat']:,.2f} 元/g")
            st.info(f"換算価格: {cn_plat_jpy:,.0f} 円/g")
            diff = ose_plat - cn_plat_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else:
            st.warning("取得失敗 (Sina/GFEX)")

    # --- 履歴 ---
    st.markdown("---")
    st.markdown("### 📊 過去20日間の記録 (最終更新)")
    if not df_history.empty:
        st.dataframe(
            df_history,
            use_container_width=True,
            hide_index=True,
            column_config={
                "日付": "Date",
                "時刻": "Time",
                "OSE金": st.column_config.NumberColumn(format="%d"),
                "US金(換算)": st.column_config.NumberColumn(format="%d"),
                "中国金(換算)": st.column_config.NumberColumn(format="%d"),
                "OSE白金": st.column_config.NumberColumn(format="%d"),
                "US白金(換算)": st.column_config.NumberColumn(format="%d"),
                "中国白金(換算)": st.column_config.NumberColumn(format="%d"),
            }
        )

if __name__ == "__main__":
    main()
