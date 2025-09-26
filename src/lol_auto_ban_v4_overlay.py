#!/usr/bin/env python3
"""
LOL Auto BAN Tool V4 - Overlay Module
"""

import tkinter as tk
from tkinter import ttk

class GameOverlay:
    """ゲームオーバーレイクラス"""
    
    def __init__(self, config):
        self.config = config
        self.overlay_window = None
        self.is_visible = False
    
    def create_overlay(self):
        """オーバーレイ作成"""
        try:
            self.overlay_window = tk.Toplevel()
            self.overlay_window.title("V4 Overlay")
            self.overlay_window.geometry("300x200+100+100")
            self.overlay_window.attributes('-topmost', True)
            self.overlay_window.attributes('-alpha', 0.8)
            
            # コンテンツ
            self.winrate_label = ttk.Label(self.overlay_window, 
                                          text="勝率: 計算中...", 
                                          font=("Arial", 12, "bold"))
            self.winrate_label.pack(pady=10)
            
            self.advice_label = ttk.Label(self.overlay_window, 
                                         text="アドバイス: 分析中...", 
                                         font=("Arial", 10))
            self.advice_label.pack(pady=5)
            
            self.is_visible = True
            
        except Exception as e:
            print(f"オーバーレイ作成エラー: {e}")
    
    def update_overlay(self, predictions, advice):
        """オーバーレイ更新"""
        if not self.is_visible or not self.overlay_window:
            return
        
        try:
            if predictions:
                blue_rate = predictions.get('blue_team', 50)
                red_rate = predictions.get('red_team', 50)
                self.winrate_label.configure(text=f"青: {blue_rate:.1f}% | 赤: {red_rate:.1f}%")
            
            if advice:
                self.advice_label.configure(text=f"アドバイス: {advice}")
                
        except Exception as e:
            print(f"オーバーレイ更新エラー: {e}")
    
    def hide_overlay(self):
        """オーバーレイ非表示"""
        if self.overlay_window:
            self.overlay_window.withdraw()
            self.is_visible = False
    
    def show_overlay(self):
        """オーバーレイ表示"""
        if self.overlay_window:
            self.overlay_window.deiconify()
            self.is_visible = True
