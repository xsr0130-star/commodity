import streamlit as st
import requests
import pandas as pd
import datetime
import os

# ==========================================
# 設定
# ==========================================
OZ = 31.1034768  # 1トロイオンス
HISTORY_FILE = "price_history.csv"

# 偽装ヘッダー (ブラウザからのアクセスに見せる)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/"
}

# ==========================================
# データ取得ロジック (Eastmoney API)
# ==========================================
def get_china_data_eastmoney():
    """
    東方財富 (Eastmoney) のAPIを使用して中国先物を取得
    secid: 市場ID.コード
    - 113.au00 : 上海金 (主力連続)
    - 142.pt00 : 広州白金 (主力連続)
    """
    gold = 0.0
    plat = 0.0
    
    # --- 1. 上海金 (SHFE Gold Main) ---
    try:
        # secid=113.au00 (上海期貨交易所)
        url_g = "https://push2.eastmoney.com/api/qt/stock/get?secid=113.au00&fields=f43"
        r = requests.get(url_g, headers=HEADERS, timeout=5)
        data = r.json()
        
        # f43が現在価格 (データがない場合は "-" が返る)
        val = data.get("data", {}).get("f43", 0)
        if val != "-":
            gold = float(val)
    except Exception as e:
        print(f"China Gold Error: {e}")

    # --- 2. 広州白金 (GFEX Platinum Main) ---
    try:
        # secid=142.pt00 (広州期貨交易所)
        # pt00 (主力連続) が取れない場合は pt2606 (特定限月) を試すロジック
        codes_to_try = ["142.pt00", "142.pt2606"]
        
        for code in codes_to_try:
            url_p = f"https://push2.eastmoney.com/api/qt/stock/get?secid={code}&fields=f43"
            r = requests.get(url_p, headers=HEADERS, timeout=5)
            data = r.json()
            val = data.get("data", {}).get("f43", 0)
            
            if val != "-" and float(val) > 0:
                plat = float(val)
                break # 取得できたらループ終了
                
    except Exception as e:
        print(f"China Plat Error: {e}")

    return gold, plat

def get_market_data():
    data = {
        "usdjpy": 0.0, "cnyjpy": 0.0,
        "us_gold": 0.0, "us_plat": 0.0,
        "cn_gold": 0.0, "cn_plat": 0.0
    }

    # 1. 為替 (ExchangeRate-API)
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
        d = r.json()
        data["usdjpy"] = d["rates"]["JPY"]
        # CNYレート
        if "CNY" in d["rates"]:
            data["cnyjpy"] = data["usdjpy"] / d["rates"]["CNY"]
        else:
            # 万が一CNYがない場合の予備 (手動計算に近い値 1ドル=7.25元想定)
            data["cnyjpy"] = data["usdjpy"] / 7.25
    except:
        pass

    # 2. US市場
    # Gold (CoinGecko is most stable)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", headers=HEADERS, timeout=5)
        data["us_gold"] = r.json()["pax-gold"]["usd"]
    except:
        pass
    
    # Platinum (Yahoo Finance)
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/PL=F?interval=1d&range=1d", headers=HEADERS, timeout=5)
        data["us_plat"] = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except:
        pass

    # 3. 中国市場 (Eastmoney APIへ変更)
    data["cn_gold"], data["cn_plat"] = get_china_data_eastmoney()

    return data

# ==========================================
# 履歴保存
# ==========================================
def update_history(ose_g, ose_p, us_g_jpy, us_p_jpy, cn_g_jpy, cn_p_jpy):
    # 日本時間
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    dt_now = datetime.datetime.now(JST)
    today_str = dt_now.strftime('%Y-%m-%d')
    time_str = dt_now.strftime('%H:%M')

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

    # 同日上書きロジック
    df = df[df["日付"] != today_str]
    df_new = pd.DataFrame([new_row])
    df = pd.concat([df_new, df], ignore_index=True)
    df = df.head(20)
    df.to_csv(HISTORY_FILE, index=False)
    
    return df

# ==========================================
# メインアプリ
# ==========================================
def main():
    st.set_page_config(page_title="Gold/Plat Monitor", layout="wide")
    st.title("🌏 リアルタイム裁定モニター (Eastmoney版)")

    # --- OSE入力 ---
    st.markdown("### 🇯🇵 日本 OSE (円建て/手入力)")
    c1, c2, c3 = st.columns([1.5, 1.5, 1])
    with c1:
        ose_gold = st.number_input("OSE 金標準 (円/g)", value=13500.0, step=10.0, format="%.0f")
    with c2:
        ose_plat = st.number_input("OSE 白金標準 (円/g)", value=4600.0, step=10.0, format="%.0f")
    with c3:
        st.write("")
        st.write("")
        if st.button("データ更新 & 記録", type="primary"):
            st.rerun()

    st.markdown("---")

    # データ取得
    d = get_market_data()

    # 計算
    us_g_jpy = (d["us_gold"]/OZ)*d["usdjpy"] if d["us_gold"] and d["usdjpy"] else 0
    us_p_jpy = (d["us_plat"]/OZ)*d["usdjpy"] if d["us_plat"] and d["usdjpy"] else 0
    cn_g_jpy = d["cn_gold"]*d["cnyjpy"] if d["cn_gold"] and d["cnyjpy"] else 0
    cn_p_jpy = d["cn_plat"]*d["cnyjpy"] if d["cn_plat"] and d["cnyjpy"] else 0

    # 履歴保存 (データが取れた場合のみ)
    if us_g_jpy > 0 or cn_g_jpy > 0:
        df_hist = update_history(ose_gold, ose_plat, us_g_jpy, us_p_jpy, cn_g_jpy, cn_p_jpy)
    else:
        if os.path.exists(HISTORY_FILE):
            df_hist = pd.read_csv(HISTORY_FILE)
        else:
            df_hist = pd.DataFrame()

    # --- 表示 ---
    col_us, col_cn = st.columns(2)

    # US
    with col_us:
        st.header("🇺🇸 米国市場 (ドル建て)")
        if d["usdjpy"]: st.metric("ドル円", f"{d['usdjpy']:.2f} 円")
        else: st.error("為替エラー")
        st.markdown("---")
        
        # Gold
        st.subheader("金 (NY Gold)")
        if d["us_gold"]:
            st.metric("NY価格", f"${d['us_gold']:,.2f}")
            st.info(f"理論価格: {us_g_jpy:,.0f} 円/g")
            diff = ose_gold - us_g_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗")
        
        st.markdown("---")
        
        # Plat
        st.subheader("白金 (NY Plat)")
        if d["us_plat"]:
            st.metric("NY価格", f"${d['us_plat']:,.2f}")
            st.info(f"理論価格: {us_p_jpy:,.0f} 円/g")
            diff = ose_plat - us_p_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗")

    # China
    with col_cn:
        st.header("🇨🇳 中国市場 (元建て)")
        if d["cnyjpy"]: st.metric("元円", f"{d['cnyjpy']:.2f} 円")
        else: st.error("為替エラー")
        st.markdown("---")

        # Gold
        st.subheader("金 (上海 Au 主力)")
        if d["cn_gold"]:
            st.metric("上海価格", f"{d['cn_gold']:,.2f} 元/g")
            st.info(f"換算価格: {cn_g_jpy:,.0f} 円/g")
            diff = ose_gold - cn_g_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗 (Eastmoney)")

        st.markdown("---")

        # Plat
        st.subheader("白金 (広州 Pt 主力)")
        if d["cn_plat"]:
            st.metric("広州価格", f"{d['cn_plat']:,.2f} 元/g")
            st.info(f"換算価格: {cn_p_jpy:,.0f} 円/g")
            diff = ose_plat - cn_p_jpy
            if diff > 0: st.error(f"OSE割高: +{diff:,.0f} 円")
            else: st.success(f"OSE割安: {diff:,.0f} 円")
        else: st.warning("取得失敗 (Eastmoney)")

    # 履歴
    st.markdown("---")
    st.markdown("### 📊 過去20日間の記録")
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
