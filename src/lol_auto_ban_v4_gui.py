#!/usr/bin/env python3
"""
LOL Auto BAN Tool V4 - GUI Module
完全動作版
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
import time
from character_overlay import CharacterOverlay 

class LOLV4GUI:
    """LOL Auto BAN Tool V4 GUI"""

    def __init__(self, root, v4_system, core_tool):
        """初期化"""
        self.root = root
        self.core_tool = core_tool
        self.v4_system = v4_system
        self.update_thread = None
        self.is_updating = False
        
        self.setup_window()
        self.load_champions_data()
        self.create_widgets()
    #    self.start_updates()
    
    def setup_window(self):
        """ウィンドウ設定"""
        self.root.title("LOL Auto BAN Tool V4 - 完全動作版")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # アイコン設定（オプション）
        try:
            # self.root.iconbitmap('icon.ico')
            pass
        except:
            pass
    
    def create_widgets(self):
        """ウィジェット作成"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
    
        tabV3 = ttk.Frame(self.notebook, padding="10")
        tabV4 = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tabV3, text="V3")
        self.notebook.add(tabV4, text="V4")

###########################################################
        #                                                 #
        #               ▼ V3 設定領域 ▼                 #
        #                                                 #
###########################################################

        # タイトル V3
        tabV3_taitle_label = ttk.Label(tabV3, text="LOL Auto BAN Tool V3", font=("Arial", 16, "bold"))
        tabV3_taitle_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))    

        # V3機能制御　開始・終了等
        self.create_control_buttons(tabV3)

        # Ban指定
        self.create_ban_section(tabV3)

        # ロール別設定
        self.create_role_section(tabV3)

        # その他設定
        self.create_other_settings(tabV3)

        # タイトル V4
        tabV4_taitle_label = ttk.Label(tabV4, text="LOL Auto BAN Tool V4", font=("Arial", 16, "bold"))
        tabV4_taitle_label.grid(row=0, column=0, columnspan=2, pady=(0,20))    
    
        # ステータスフレーム
        tabV4_status_frame = ttk.LabelFrame(tabV4, text="システム状態", padding="10")
        tabV4_status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.tabV4_status_label = ttk.Label(tabV4_status_frame  , text="初期化中...")
        self.tabV4_status_label.grid(row=0, column=0, sticky=tk.W)        

        # 監視制御フレーム
        tabV4_control_frame = ttk.LabelFrame(tabV4, text="監視制御", padding="10")
        tabV4_control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.tabV4_start_button = ttk.Button(tabV4_control_frame, text="監視開始", 
                                      command=self.start_monitoring)
        self.tabV4_start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.tabV4_stop_button = ttk.Button(tabV4_control_frame, text="監視停止", 
                                     command=self.stop_monitoring, state=tk.DISABLED)
        self.tabV4_stop_button.grid(row=0, column=1)

        # 予測結果フレーム
        tabV4_prediction_frame = ttk.LabelFrame(tabV4, text="勝率予測", padding="10")
        tabV4_prediction_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.tabV4_prediction_text = tk.Text(tabV4_prediction_frame, height=8, width=70)
        self.tabV4_prediction_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # スクロールバー
        tabV4_scrollbar = ttk.Scrollbar(tabV4_prediction_frame, orient=tk.VERTICAL, 
                                 command=self.tabV4_prediction_text.yview)
        tabV4_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tabV4_prediction_text.configure(yscrollcommand=tabV4_scrollbar.set)

        #--- ▼▼▼ タブ分割のため削除する ▼▼▼ ---
        ## メインフレーム
        #main_frame = ttk.Frame(self.root, padding="10")
        #main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        #
        ## タイトル
        #title_label = ttk.Label(main_frame, text="LOL Auto BAN Tool V4", 
        #                       font=("Arial", 16, "bold"))
        #title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        #
        ## ステータスフレーム
        #status_frame = ttk.LabelFrame(main_frame, text="システム状態", padding="10")
        #status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        #
        #self.status_label = ttk.Label(status_frame, text="初期化中...")
        #self.status_label.grid(row=0, column=0, sticky=tk.W)
        #
        ## 監視制御フレーム
        #control_frame = ttk.LabelFrame(main_frame, text="監視制御", padding="10")
        #control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        #
        #self.start_button = ttk.Button(control_frame, text="監視開始", 
        #                              command=self.start_monitoring)
        #self.start_button.grid(row=0, column=0, padx=(0, 10))
        #
        #self.stop_button = ttk.Button(control_frame, text="監視停止", 
        #                             command=self.stop_monitoring, state=tk.DISABLED)
        #self.stop_button.grid(row=0, column=1)
        #
        ## 予測結果フレーム
        #prediction_frame = ttk.LabelFrame(main_frame, text="勝率予測", padding="10")
        #prediction_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        #
        #self.prediction_text = tk.Text(prediction_frame, height=8, width=70)
        #self.prediction_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        #
        ## スクロールバー
        #scrollbar = ttk.Scrollbar(prediction_frame, orient=tk.VERTICAL, 
        #                         command=self.prediction_text.yview)
        #scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        #self.prediction_text.configure(yscrollcommand=scrollbar.set)
        #
        ## BAN推奨フレーム
        #ban_frame = ttk.LabelFrame(main_frame, text="BAN推奨", padding="10")
        #ban_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        #
        #self.ban_label = ttk.Label(ban_frame, text="BAN推奨チャンピオン: 分析中...")
        #self.ban_label.grid(row=0, column=0, sticky=tk.W)
        #
        ## ログフレーム
        #log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="10")
        #log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        #
        #self.log_text = tk.Text(log_frame, height=6, width=70)
        #self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        #
        ## ログスクロールバー
        #log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, 
        #                             command=self.log_text.yview)
        #log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        #self.log_text.configure(yscrollcommand=log_scrollbar.set)
        #
        ## グリッド設定
        #self.root.columnconfigure(0, weight=1)
        #self.root.rowconfigure(0, weight=1)
        #main_frame.columnconfigure(1, weight=1)
        #main_frame.rowconfigure(5, weight=1)
        #
        ## 初期ログ
        #print("LOL Auto BAN Tool V4 GUI 初期化完了")
        #--- ▲▲▲ タブ分割のため削除する ▲▲▲ ---
    
    def start_monitoring(self):
        """監視開始"""
        try:
            self.v4_system.start_monitoring()
            print("キャラクタウィンドウを初期化中...")
            # 親ウィンドウを渡してCharacterOverlayを作成
            self.character_overlay = CharacterOverlay(parent=self.root)
            self.character_overlay.run()  # 表示
            # 分析モジュールのインポート
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.NORMAL)
            print("ゲーム監視を開始しました")
            self.update_status("監視中...")
        except Exception as e:
            messagebox.showerror("エラー", f"監視開始に失敗しました: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_monitoring(self):
        """監視停止"""
        try:
            self.v4_system.stop_monitoring()
            self.tabV4_start_button.configure(state=tk.NORMAL)
            self.tabV4_stop_button.configure(state=tk.DISABLED)
            print("ゲーム監視を停止しました")
            self.update_status("停止中")
        except Exception as e:
            messagebox.showerror("エラー", f"監視停止に失敗しました: {e}")
    
    def start_updates(self):
        """更新開始"""
        self.is_updating = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """更新ループ"""
        while self.is_updating:
            try:
                # ゲーム状態更新
                game_status = self.v4_system.get_game_status()
                if game_status['in_game']:
                    self.root.after(0, self.update_status, 
                                   f"ゲーム中 - {game_status.get('game_time', 0):.0f}秒")
                else:
                    self.root.after(0, self.update_status, "ゲーム待機中")
                
                # 予測結果更新
                predictions = self.v4_system.get_current_predictions()
                if predictions:
                    self.root.after(0, self.update_predictions, predictions)
                
                # BAN推奨更新
                ban_recommendations = self.v4_system.get_ban_recommendations()
                self.root.after(0, self.update_ban_recommendations, ban_recommendations)
                
                time.sleep(2)
                
            except Exception as e:
                self.root.after(0, print, f"更新エラー: {e}")
                time.sleep(5)
    
    def update_status(self, status):
        """ステータス更新"""
        self.tabV4_status_label.configure(text=f"状態: {status}")
    
    def update_predictions(self, predictions):
        """予測結果更新"""
        self.prediction_text.delete(1.0, tk.END)
        
        if predictions:
            self.prediction_text.insert(tk.END, "=== 勝率予測結果 ===\n\n")
            
            for team, winrate in predictions.items():
                team_name = "青チーム" if team == "blue_team" else "赤チーム"
                self.prediction_text.insert(tk.END, f"{team_name}: {winrate:.1f}%\n")
            
            self.prediction_text.insert(tk.END, f"\n更新時刻: {time.strftime('%H:%M:%S')}\n")
        else:
            self.prediction_text.insert(tk.END, "予測データなし\n")
    
    def update_ban_recommendations(self, recommendations):
        """BAN推奨更新"""
        if recommendations:
            ban_text = ", ".join(recommendations)
            self.ban_label.configure(text=f"BAN推奨チャンピオン: {ban_text}")
        else:
            self.ban_label.configure(text="BAN推奨チャンピオン: 分析中...")
    
    def add_log(self, message):
        """ログ追加"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # ログ行数制限
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete(1.0, "2.0")
    
    def on_closing(self):
        """ウィンドウ閉じる時の処理"""
        self.is_updating = False
        self.v4_system.stop_monitoring()
        self.root.destroy()

    def create_control_buttons(self, parent):
        """制御ボタンを作成"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
    
        # 監視開始ボタン
        self.start_button = ttk.Button(control_frame, text="監視開始", command=self.start_tool)
        self.start_button.grid(row=0, column=0)
    
        # 監視停止ボタン
        self.stop_button = ttk.Button(control_frame, text="監視停止", command=self.stop_tool, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))

        self.save_button = ttk.Button(control_frame, text="設定保存")
        self.save_button.grid(row=0, column=2)
    
        self.load_button = ttk.Button(control_frame, text="設定読み込み")
        self.load_button.grid(row=0, column=3)

    def stop_tool(self):
        print("F ツールを停止")
        if self.core_tool:
            self.core_tool.running = False
        
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="状態: 停止", foreground="red")
        self.connection_status.config(text="接続: 切断", foreground="red")
        
        print("ツール停止")

    def create_ban_section(self, parent):
        """BAN設定セクションを作成"""
        ban_frame = ttk.LabelFrame(parent, text="BANチャンピオン設定", padding="10")
        ban_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        ban_frame.columnconfigure(1, weight=1)
        
        # 自動BAN有効/無効チェックボックス
        self.auto_ban_var = tk.BooleanVar(value=True)
        auto_ban_check = ttk.Checkbutton(ban_frame, text="自動BAN有効", variable=self.auto_ban_var)
        auto_ban_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(ban_frame, text="BANするチャンピオン:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        
        self.ban_champion_var = tk.StringVar(value="Yasuo")
        self.ban_champion_combo = ttk.Combobox(ban_frame, textvariable=self.ban_champion_var, 
                                              values=self.get_champion_list(), 
                                              state="readonly", width=20)
        self.ban_champion_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(ban_frame, text="選択").grid(row=1, column=2)    

    def get_champion_list(self):
        """チャンピオンリストを取得"""
        champions = self.champions_data.get('champions', [])
    #    if not champions:
    #        # フォールバック用の基本チャンピオンリスト
    #        champions = ["Garen", "Annie", "Ashe", "Yasuo", "Zed", "Lux", "Jinx", "Darius", "Master Yi", "Thresh"]
        return sorted(champions) 

    def load_champions_data(self):
        """チャンピオンデータを読み込み（静的データ + コアツール連携）"""
        print("F チャンピオンデータ読み込み")
        try:
            # 現在のスクリプトと同じディレクトリのchampions_data.jsonを読み込み
            current_dir = os.path.dirname(os.path.abspath(__file__))    
            champions_file = os.path.join(current_dir,'champions_data.json')
            print("存在する？", os.path.exists(champions_file))  
            print(champions_file)
#            self.champions_data = {"champions": ["Garen", "Annie", "Ashe", "Yasuo", "Zed"]}
            with open(champions_file, 'r', encoding='utf-8') as f:
                self.champions_data = json.load(f)
#            print(f"チャンピオンデータ読み込み完了: {champions_file}")
            
            # コアツールが利用可能な場合は追加データを取得
#            if self.core_tool and hasattr(self.core_tool, 'champion_id_map'):
#                if self.core_tool.champion_id_map:
#                    # コアツールからのデータで更新
#                    core_champions = list(self.core_tool.champion_id_map.keys())
#                    if core_champions:
#                        self.champions_data['champions'] = sorted(set(
#                            self.champions_data.get('champions', []) + core_champions
#                        ))
#                        print(f"コアツールからチャンピオンデータを更新: {len(core_champions)}体")
                        
        except Exception as e:
            self.champions_data = {"champions": ["Garen", "Annie", "Ashe", "Yasuo", "Zed"]}
            print(f"チャンピオンデータ読み込みエラー: {e}")
    def log_message(self, message):
        print(message)

    def create_role_section(self, parent):
        """ロール別設定セクションを作成"""
        role_frame = ttk.LabelFrame(parent, text="ロール別チャンピオン設定", padding="10")
        role_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        role_frame.columnconfigure(1, weight=1)
        
        self.role_vars = {}
        roles = [
            ("Top:", "top"),
            ("Jungle:", "jungle"), 
            ("Middle:", "middle"),
            ("ADC:", "bottom"),
            ("Support:", "utility")
        ]
        
        for i, (display_name, role_key) in enumerate(roles):
            ttk.Label(role_frame, text=display_name).grid(row=i, column=0, sticky=tk.W, padx=(0, 10))
            
            # 各ロールに3つのチャンピオン選択
            role_champions_frame = ttk.Frame(role_frame)
            role_champions_frame.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
            role_champions_frame.columnconfigure(0, weight=1)
            role_champions_frame.columnconfigure(1, weight=1)
            role_champions_frame.columnconfigure(2, weight=1)
            
            self.role_vars[role_key] = []
            for j in range(3):
                var = tk.StringVar(value="")
                combo = ttk.Combobox(role_champions_frame, textvariable=var,
                                   values=self.get_champion_list(),
                                   state="readonly", width=15)
                combo.grid(row=0, column=j, padx=(0, 5) if j < 2 else 0, sticky=(tk.W, tk.E))
                self.role_vars[role_key].append(var)
            
            ttk.Button(role_frame, text="設定", 
                      command=lambda r=role_key: self.configure_role(r)).grid(row=i, column=2)

    def create_other_settings(self, parent):
        """その他設定セクションを作成"""
        other_frame = ttk.LabelFrame(parent, text="その他設定", padding="10")
        other_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # チェックボックス設定
        self.auto_accept_var = tk.BooleanVar(value=True)
        self.auto_pick_var = tk.BooleanVar(value=True)
        self.auto_lock_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(other_frame, text="自動キュー受諾", variable=self.auto_accept_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(other_frame, text="自動チャンピオンピック", variable=self.auto_pick_var).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(other_frame, text="自動ロック", variable=self.auto_lock_var).grid(row=0, column=2, sticky=tk.W)
        
        # 遅延設定
        delay_frame = ttk.Frame(other_frame)
        delay_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(delay_frame, text="受諾遅延(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.accept_delay_var = tk.StringVar(value="0.5")
        ttk.Entry(delay_frame, textvariable=self.accept_delay_var, width=8).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(delay_frame, text="ピック遅延(秒):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.pick_delay_var = tk.StringVar(value="1.0")
        ttk.Entry(delay_frame, textvariable=self.pick_delay_var, width=8).grid(row=0, column=3)

    def start_tool(self):
        print("F ツールを開始")
        if self.core_tool:
            # 設定をコアツールに反映
            self.apply_config_to_core()
            
            # コアツールを別スレッドで開始
            self.tool_thread = threading.Thread(target=self.run_core_tool, daemon=True)
            self.tool_thread.start()
            # 追加
            self.tool_thread = threading.Thread(target=self.run_charactor_tool, daemon=True)
            self.tool_thread.start()        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="状態: 実行中", foreground="green")
        self.connection_status.config(text="接続: 確認中...", foreground="orange")
        
        print("ツール開始")

    def apply_config_to_core(self):
        """GUI設定をコアツールに適用"""
        if not self.core_tool:
            return
        
        try:
            # 基本設定
            self.core_tool.ban_champion = self.ban_champion_var.get()
            self.core_tool.auto_ban_enabled = self.auto_ban_var.get()
            self.core_tool.auto_accept_queue = self.auto_accept_var.get()
            self.core_tool.auto_pick_champion = self.auto_pick_var.get()
            self.core_tool.auto_lock = self.auto_lock_var.get()
            
            # 遅延設定
            try:
                self.core_tool.accept_delay_seconds = float(self.accept_delay_var.get())
                self.core_tool.pick_delay_seconds = float(self.pick_delay_var.get())
            except ValueError:
                print("遅延設定が不正です。デフォルト値を使用します。")
            
            # ロール別設定
            champion_preferences = {}
            for role, vars_list in self.role_vars.items():
                champions = [var.get() for var in vars_list if var.get()]
                if champions:
                    champion_preferences[role] = champions
            self.core_tool.champion_preferences = champion_preferences
            
            # フォールバック設定
            fallback_champions = [var.get() for var in self.fallback_vars if var.get()]
            if fallback_champions:
                self.core_tool.fallback_champions = fallback_champions
            
            print("設定をコアツールに適用しました")
            
        except Exception as e:
            print(f"設定適用エラー: {e}")

    def run_core_tool(self):
        """コアツールを実行"""
        try:
            if self.core_tool:
                self.core_tool.run()
        except Exception as e:
            self.log_message(f"ツール実行エラー: {e}")
    def run_charactor_tool(self):
        """コアツールを実行"""
        try:
            if self.core_tool:
                self.core_tool.run()
        except Exception as e:
            self.log_message(f"ツール実行エラー: {e}")