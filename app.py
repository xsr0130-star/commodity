import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from datetime import datetime
import requests
import websocket

# ==========================================
# 設定
# ==========================================
OZ = 31.1034768
LOG_FILE = "us_monitor_log.csv"
CONFIG_FILE = "us_monitor_config.json"

# データ保持用 (スレッド間で共有)
market_data = {
    "usdjpy": 0.0,
    "gold": 0.0,
    "plat": 0.0
}

# ==========================================
# 通信スレッド群
# ==========================================

# 1. 金 (Binance WebSocket: 最強)
def run_gold_ws():
    def on_message(ws, message):
        try:
            data = json.loads(message)
            price = float(data['p'])
            market_data['gold'] = price
        except: pass

    def on_error(ws, error):
        time.sleep(5) # 再接続待機

    def on_close(ws, close_status_code, close_msg):
        time.sleep(5)
        start_ws() # 再帰的に再接続

    def start_ws():
        # PAXG/USDT (Gold Token)
        ws = websocket.WebSocketApp(
            "wss://stream.binance.com:9443/ws/paxgusdt@trade",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever()

    threading.Thread(target=start_ws, daemon=True).start()

# 2. 為替 & 白金 (ポーリング)
def run_polling():
    while True:
        try:
            # 為替 (ExchangeRate-API)
            r_fx = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            market_data['usdjpy'] = r_fx.json()['rates']['JPY']
        except: pass

        try:
            # 白金 (Yahoo Finance JSON - 先物 PL=F)
            # Pythonならヘッダー偽装で直接Yahooを取れるのでプロキシ不要！
            headers = {"User-Agent": "Mozilla/5.0"}
            url_p = "https://query1.finance.yahoo.com/v8/finance/chart/PL=F?interval=1d&range=1d"
            r_p = requests.get(url_p, headers=headers, timeout=5)
            market_data['plat'] = r_p.json()['chart']['result'][0]['meta']['regularMarketPrice']
        except: pass

        time.sleep(5) # 5秒間隔

threading.Thread(target=run_polling, daemon=True).start()


# ==========================================
# GUI アプリケーション
# ==========================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🇺🇸 US/OSE Monitor (Python Native)")
        self.geometry("600x550")
        self.configure(bg="#1e1e1e")
        
        # スタイル設定
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#1e1e1e", foreground="#e0e0e0", font=("Meiryo", 10))
        style.configure("Header.TLabel", font=("Meiryo", 14, "bold"), foreground="#ffffff")
        style.configure("Val.TLabel", font=("Consolas", 20, "bold"), foreground="#ffffff")
        style.configure("DiffPlus.TLabel", font=("Consolas", 14, "bold"), foreground="#ff5252")
        style.configure("DiffMinus.TLabel", font=("Consolas", 14, "bold"), foreground="#69f0ae")
        style.configure("TButton", font=("Meiryo", 10, "bold"), background="#0277bd", foreground="white")
        style.map("TButton", background=[("active", "#01579b")])

        # 保存されたOSE入力値をロード
        self.load_config()

        # --- UI構築 ---
        
        # 1. 入力エリア
        input_frame = tk.Frame(self, bg="#2d2d2d", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(input_frame, text="OSE 金 (円):", bg="#2d2d2d", fg="#ffc107").grid(row=0, column=0, padx=5)
        self.entry_gold = tk.Entry(input_frame, font=("Consolas", 12), width=10, justify="right", bg="#000", fg="#fff", insertbackground="white")
        self.entry_gold.grid(row=0, column=1, padx=5)
        self.entry_gold.insert(0, str(self.config.get("ose_gold", "")))

        tk.Label(input_frame, text="OSE 白金 (円):", bg="#2d2d2d", fg="#b0bec5").grid(row=0, column=2, padx=5)
        self.entry_plat = tk.Entry(input_frame, font=("Consolas", 12), width=10, justify="right", bg="#000", fg="#fff", insertbackground="white")
        self.entry_plat.grid(row=0, column=3, padx=5)
        self.entry_plat.insert(0, str(self.config.get("ose_plat", "")))

        save_btn = tk.Button(input_frame, text="記録", bg="#e65100", fg="white", font=("Meiryo", 9, "bold"), command=self.save_log)
        save_btn.grid(row=0, column=4, padx=20)

        # 2. 為替表示
        fx_frame = tk.Frame(self, bg="#004d40", padx=10, pady=5)
        fx_frame.pack(fill="x", padx=10, pady=0)
        tk.Label(fx_frame, text="USD/JPY", bg="#004d40", fg="#aaa").pack(side="left")
        self.lbl_fx = tk.Label(fx_frame, text="---", font=("Consolas", 16, "bold"), bg="#004d40", fg="#fff")
        self.lbl_fx.pack(side="right")

        # 3. メイングリッド (金・白金)
        grid_frame = tk.Frame(self, bg="#1e1e1e")
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 金パネル
        g_panel = tk.Frame(grid_frame, bg="#252525", bd=1, relief="solid")
        g_panel.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(g_panel, text="Gold (US Future)", bg="#252525", fg="#ffc107", font=("Meiryo", 10, "bold")).pack(pady=5)
        self.lbl_g_usd = ttk.Label(g_panel, text="---", style="Val.TLabel", background="#252525")
        self.lbl_g_usd.pack()
        tk.Label(g_panel, text="理論価格 (円/g)", bg="#252525", fg="#888", font=("Meiryo", 8)).pack(pady=(10,0))
        self.lbl_g_jpy = tk.Label(g_panel, text="---", font=("Consolas", 12, "bold"), bg="#252525", fg="#fff")
        self.lbl_g_jpy.pack()
        tk.Label(g_panel, text="OSE差額", bg="#252525", fg="#888", font=("Meiryo", 8)).pack(pady=(5,0))
        self.lbl_g_diff = ttk.Label(g_panel, text="---", style="DiffPlus.TLabel", background="#252525")
        self.lbl_g_diff.pack(pady=5)

        # 白金パネル
        p_panel = tk.Frame(grid_frame, bg="#252525", bd=1, relief="solid")
        p_panel.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(p_panel, text="Platinum (US Future)", bg="#252525", fg="#b0bec5", font=("Meiryo", 10, "bold")).pack(pady=5)
        self.lbl_p_usd = ttk.Label(p_panel, text="---", style="Val.TLabel", background="#252525")
        self.lbl_p_usd.pack()
        tk.Label(p_panel, text="理論価格 (円/g)", bg="#252525", fg="#888", font=("Meiryo", 8)).pack(pady=(10,0))
        self.lbl_p_jpy = tk.Label(p_panel, text="---", font=("Consolas", 12, "bold"), bg="#252525", fg="#fff")
        self.lbl_p_jpy.pack()
        tk.Label(p_panel, text="OSE差額", bg="#252525", fg="#888", font=("Meiryo", 8)).pack(pady=(5,0))
        self.lbl_p_diff = ttk.Label(p_panel, text="---", style="DiffPlus.TLabel", background="#252525")
        self.lbl_p_diff.pack(pady=5)

        # 4. 履歴テーブル
        hist_frame = tk.Frame(self, bg="#1e1e1e")
        hist_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("Time", "OSE_G", "Diff_G", "OSE_P", "Diff_P")
        self.tree = ttk.Treeview(hist_frame, columns=cols, show="headings", height=5)
        
        # カラム設定
        self.tree.heading("Time", text="時刻")
        self.tree.heading("OSE_G", text="OSE金")
        self.tree.heading("Diff_G", text="金差額")
        self.tree.heading("OSE_P", text="OSE白金")
        self.tree.heading("Diff_P", text="白金差額")
        
        self.tree.column("Time", width=80, anchor="center")
        self.tree.column("OSE_G", width=80, anchor="e")
        self.tree.column("Diff_G", width=80, anchor="e")
        self.tree.column("OSE_P", width=80, anchor="e")
        self.tree.column("Diff_P", width=80, anchor="e")
        
        self.tree.pack(fill="both", expand=True)
        
        # 履歴読み込み
        self.load_history_view()

        # GUI更新ループ開始
        self.update_ui_loop()

    def load_config(self):
        self.config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
            except: pass

    def save_config(self):
        try:
            self.config["ose_gold"] = self.entry_gold.get()
            self.config["ose_plat"] = self.entry_plat.get()
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except: pass

    def update_ui_loop(self):
        # 画面更新 (100msごと)
        try:
            fx = market_data['usdjpy']
            g = market_data['gold']
            p = market_data['plat']

            if fx > 0: self.lbl_fx.config(text=f"{fx:.2f} 円")
            if g > 0: self.lbl_g_usd.config(text=f"${g:,.1f}")
            if p > 0: self.lbl_p_usd.config(text=f"${p:,.1f}")

            # 計算
            try:
                ose_g = float(self.entry_gold.get())
                ose_p = float(self.entry_plat.get())
                
                # 計算結果の一時保存（記録用）
                self.calc_res = {"og": ose_g, "op": ose_p, "gd": 0, "pd": 0}

                if fx > 0 and g > 0:
                    g_jpy = (g / OZ) * fx
                    g_diff = ose_g - g_jpy
                    self.lbl_g_jpy.config(text=f"{g_jpy:,.0f}")
                    
                    sign = "+" if g_diff > 0 else ""
                    self.lbl_g_diff.config(text=f"{sign}{g_diff:,.0f}", style="DiffPlus.TLabel" if g_diff > 0 else "DiffMinus.TLabel")
                    self.calc_res["gd"] = int(g_diff)

                if fx > 0 and p > 0:
                    p_jpy = (p / OZ) * fx
                    p_diff = ose_p - p_jpy
                    self.lbl_p_jpy.config(text=f"{p_jpy:,.0f}")
                    
                    sign = "+" if p_diff > 0 else ""
                    self.lbl_p_diff.config(text=f"{sign}{p_diff:,.0f}", style="DiffPlus.TLabel" if p_diff > 0 else "DiffMinus.TLabel")
                    self.calc_res["pd"] = int(p_diff)

            except ValueError:
                pass # 入力中などで数値でない場合

        except Exception as e:
            print(e)

        self.after(100, self.update_ui_loop)

    def save_log(self):
        self.save_config() # 入力値保存
        
        if not hasattr(self, 'calc_res'): return

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        
        # CSV読み込み
        rows = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                rows = f.readlines()
        
        # ヘッダーがなければ作成
        if not rows:
            rows.append("Date,Time,OSE_G,Diff_G,OSE_P,Diff_P\n")

        # 同日行があれば削除
        new_rows = [r for r in rows if not r.startswith(date_str)]
        
        # 新しい行を作成
        new_line = f"{date_str},{time_str},{self.calc_res['og']},{self.calc_res['gd']},{self.calc_res['op']},{self.calc_res['pd']}\n"
        
        # ヘッダーの直後に挿入 (最新を上に)
        if len(new_rows) > 0:
            new_rows.insert(1, new_line)
        else:
            new_rows.append(new_line)

        # 20件制限 (ヘッダー1行 + データ20行)
        if len(new_rows) > 21:
            new_rows = new_rows[:21]

        # 保存
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_rows)
            
        self.load_history_view()

    def load_history_view(self):
        # ツリービューをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:] # ヘッダー飛ばす
                for line in lines:
                    cols = line.strip().split(",")
                    if len(cols) >= 6:
                        # Time, OSE_G, Diff_G, OSE_P, Diff_P
                        display_row = (cols[1], cols[2], cols[3], cols[4], cols[5])
                        self.tree.insert("", "end", values=display_row)

if __name__ == "__main__":
    app = App()
    app.mainloop()
