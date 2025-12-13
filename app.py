import streamlit as st
import requests
import time

# ==========================================
# 設定
# ==========================================
# 広州白金の限月コード (必要に応じて変更可能)
GFEX_PLAT_CODE = "pt2606" 
OZ = 31.1034768  # 1トロイオンス

# ヘッダー (APIアクセス用)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# ==========================================
# データ取得ロジック (海外のみリアルタイム取得)
# ==========================================
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
        data["cnyjpy"] = data["usdjpy"] / d["rates"]["CNY"]
    except: pass

    # 2. US市場 (CoinGecko & Yahoo)
    try: # Gold
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", headers=HEADERS, timeout=3)
        data["us_gold"] = r.json()["pax-gold"]["usd"]
    except: pass
    
    try: # Plat
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/PL=F?interval=1d&range=1d", headers=HEADERS, timeout=3)
        data["us_plat"] = r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except: pass

    # 3. 中国市場 (Sina Direct - SHFE/GFEX)
    try:
        url = f"https://hq.sinajs.cn/list=nf_au0,{GFEX_PLAT_CODE}"
        r = requests.get(url, headers=HEADERS, timeout=3)
        text = r.text
        
        # 上海金 (nf_au0)
        if "nf_au0" in text:
            parts = text.split('var hq_str_nf_au0="')[1].split('";')[0].split(',')
            if len(parts) > 5: data["cn_gold"] = float(parts[5])
            
        # 広州白金 (ptXXXX)
        if GFEX_PLAT_CODE in text:
            parts = text.split(f'var hq_str_{GFEX_PLAT_CODE}="')[1].split('";')[0].split(',')
            # GFEX: 最新値が入る場所を探す (Index 8 or 5 or 6)
            p = 0.0
            try: p = float(parts[8]) 
            except: pass
            if p == 0:
                try: p = float(parts[5])
                except: pass
            data["cn_plat"] = p
    except: pass

    return data

# ==========================================
# メイン画面
# ==========================================
def main():
    st.set_page_config(page_title="金・白金 裁定モニター", layout="wide")

    st.title("🌏 リアルタイム裁定モニター")
    
    # -------------------------------------------
    # 1. 日本 OSE (手動入力エリア)
    # -------------------------------------------
    st.markdown("### 🇯🇵 日本 OSE (円建て/手入力)")
    
    # 入力欄を並べる
    input_c1, input_c2, input_c3 = st.columns([1.5, 1.5, 1])
    
    with input_c1:
        ose_gold = st.number_input("OSE 金標準 (円/g)", value=13500.0, step=10.0, format="%.0f")
    with input_c2:
        ose_plat = st.number_input("OSE 白金標準 (円/g)", value=4700.0, step=10.0, format="%.0f")
    with input_c3:
        st.write("") # スペース調整
        st.write("") 
        if st.button("データ更新 (Refresh)", type="primary"):
            st.rerun()

    st.markdown("---")

    # データを取得
    d = get_market_data()

    # -------------------------------------------
    # 2. 左右カラム (左:ドル建て / 右:元建て)
    # -------------------------------------------
    col_us, col_cn = st.columns(2)

    # === 左：ドル建て (US Market) ===
    with col_us:
        st.header("🇺🇸 米国市場 (ドル建て)")

        # (1) 為替
        st.subheader("1. ドル円 (USD/JPY)")
        if d["usdjpy"]:
            st.metric(label="現在のレート", value=f"{d['usdjpy']:.2f} 円")
        else:
            st.error("取得失敗")
        
        st.markdown("---")

        # (2) 金
        st.subheader("2. 金 (NY Gold)")
        if d["us_gold"] and d["usdjpy"]:
            # 理論値計算: ($/oz ÷ 31.1035) × ドル円
            theory = (d["us_gold"] / OZ) * d["usdjpy"]
            diff = ose_gold - theory
            
            # 表示
            st.metric(label="NY価格 ($/oz)", value=f"${d['us_gold']:,.2f}")
            st.info(f"理論価格 (税抜): {theory:,.0f} 円/g")
            
            # 差額判定
            st.markdown(" **OSEとの差額:**")
            if diff > 0:
                st.error(f"OSEが {diff:,.0f} 円 高い (Premium)")
            else:
                st.success(f"OSEが {abs(diff):,.0f} 円 安い (Discount)")
        else:
            st.warning("データ取得中...")

        st.markdown("---")

        # (3) 白金
        st.subheader("3. 白金 (NY Platinum)")
        if d["us_plat"] and d["usdjpy"]:
            theory = (d["us_plat"] / OZ) * d["usdjpy"]
            diff = ose_plat - theory
            
            st.metric(label="NY価格 ($/oz)", value=f"${d['us_plat']:,.2f}")
            st.info(f"理論価格 (税抜): {theory:,.0f} 円/g")
            
            # 差額判定
            st.markdown(" **OSEとの差額:**")
            if diff > 0:
                st.error(f"OSEが {diff:,.0f} 円 高い (Premium)")
            else:
                st.success(f"OSEが {abs(diff):,.0f} 円 安い (Discount)")
        else:
            st.warning("データ取得中...")


    # === 右：元建て (China Market) ===
    with col_cn:
        st.header("🇨🇳 中国市場 (元建て)")

        # (1) 為替
        st.subheader("1. 元円 (CNY/JPY)")
        if d["cnyjpy"]:
            st.metric(label="現在のレート", value=f"{d['cnyjpy']:.2f} 円")
        else:
            st.error("取得失敗")

        st.markdown("---")

        # (2) 金
        st.subheader("2. 金 (SHFE Shanghai)")
        if d["cn_gold"] and d["cnyjpy"]:
            # 理論値計算: 元/g × 元円
            theory = d["cn_gold"] * d["cnyjpy"]
            diff = ose_gold - theory
            
            st.metric(label="上海価格 (元/g)", value=f"{d['cn_gold']:,.2f}")
            st.info(f"換算価格: {theory:,.0f} 円/g")
            
            # 差額判定
            st.markdown(" **OSEとの差額:**")
            if diff > 0:
                st.error(f"OSEが {diff:,.0f} 円 高い (Premium)")
            else:
                st.success(f"OSEが {abs(diff):,.0f} 円 安い (Discount)")
        else:
            st.warning("データ取得中...")

        st.markdown("---")

        # (3) 白金
        st.subheader(f"3. 白金 (GFEX {GFEX_PLAT_CODE})")
        if d["cn_plat"] and d["cnyjpy"]:
            theory = d["cn_plat"] * d["cnyjpy"]
            diff = ose_plat - theory
            
            st.metric(label="広州価格 (元/g)", value=f"{d['cn_plat']:,.2f}")
            st.info(f"換算価格: {theory:,.0f} 円/g")
            
            # 差額判定
            st.markdown(" **OSEとの差額:**")
            if diff > 0:
                st.error(f"OSEが {diff:,.0f} 円 高い (Premium)")
            else:
                st.success(f"OSEが {abs(diff):,.0f} 円 安い (Discount)")
        else:
            st.warning("データ取得中 (広州接続...)")

if __name__ == "__main__":
    main()