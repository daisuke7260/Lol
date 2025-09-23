#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高度なキャラクターオーバーレイアプリケーション
メッセージ表示、アニメーション、設定保存機能付き
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sys
import os
import json
import threading
import time


class AdvancedCharacterOverlay(tk.Tk):
    """
    高度なキャラクター付きオーバーレイウィンドウ
    アニメーション、設定保存、メッセージ履歴機能付き
    """
    
    def __init__(self, width=400, height=280, x=100, y=100):
        super().__init__()
        
        # ウィンドウサイズと位置
        self.window_width = width
        self.window_height = height
        self.window_x = x
        self.window_y = y
        
        # ドラッグ移動用の変数
        self.offset_x = None
        self.offset_y = None
        
        # メッセージ関連
        self.current_message = "こんにちは！\nメッセージを表示します"
        self.message_history = []
        self.message_queue = []
        self.auto_message_enabled = False
        self.message_display_time = 3000  # ミリ秒
        
        # 設定
        self.settings = {
            'transparency': 0.95,
            'topmost': True,
            'bubble_color': '#FFFFFF',
            'text_color': '#000000',
            'font_size': 12,
            'auto_hide': False,
            'animation_enabled': True
        }
        
        # アニメーション関連
        self.animation_running = False
        self.bounce_direction = 1
        self.original_y = y
        
        # 画像リソース
        self.character_image = None
        self.speech_bubble_image = None
        
        # 設定ファイルパス
        self.config_file = '/home/ubuntu/overlay_settings.json'
        
        # 初期化
        self._load_settings()
        self._setup_window()
        self._load_images()
        self._create_widgets()
        self._setup_events()
        self._start_animation()
    
    def _load_settings(self):
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                print("設定を読み込みました")
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
    
    def _save_settings(self):
        """設定ファイルに保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            print("設定を保存しました")
        except Exception as e:
            print(f"設定保存エラー: {e}")
    
    def _setup_window(self):
        """ウィンドウの基本設定を行う"""
        self.title("Advanced Character Overlay")
        
        # ウィンドウサイズと位置を設定
        geometry = f"{self.window_width}x{self.window_height}+{self.window_x}+{self.window_y}"
        self.geometry(geometry)
        
        # 設定に基づいてウィンドウ属性を設定
        self.wm_attributes("-topmost", self.settings['topmost'])
        self.wm_attributes("-alpha", self.settings['transparency'])
        
        # ウィンドウボーダーを削除
        self.overrideredirect(True)
        
        # フォーカスを強制取得
        self.focus_force()
        
        # 背景を透明に設定
        self._setup_transparency()
    
    def _setup_transparency(self):
        """透明化設定"""
        try:
            if sys.platform.startswith('win'):
                self.configure(bg='white')
                self.wm_attributes("-transparentcolor", "white")
            else:
                self.configure(bg='#f0f0f0')
        except tk.TclError:
            self.configure(bg='lightblue')
    
    def _load_images(self):
        """画像リソースを読み込む"""
        try:
            if os.path.exists('/home/ubuntu/character.png'):
                char_img = Image.open('/home/ubuntu/character.png')
                char_img = char_img.resize((100, 100), Image.Resampling.LANCZOS)
                self.character_image = ImageTk.PhotoImage(char_img)
            else:
                self.character_image = self._create_default_character()
        except Exception as e:
            print(f"画像読み込みエラー: {e}")
            self.character_image = self._create_default_character()
    
    def _create_default_character(self):
        """デフォルトキャラクター画像を作成"""
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 顔の輪郭
        draw.ellipse([15, 15, 85, 85], fill='#FFE4B5', outline='#DEB887', width=3)
        
        # 目
        draw.ellipse([30, 35, 40, 45], fill='black')
        draw.ellipse([60, 35, 70, 45], fill='black')
        
        # 目のハイライト
        draw.ellipse([32, 37, 36, 41], fill='white')
        draw.ellipse([62, 37, 66, 41], fill='white')
        
        # 口
        draw.arc([40, 55, 60, 70], start=0, end=180, fill='black', width=3)
        
        # ほっぺ
        draw.ellipse([20, 50, 30, 60], fill='#FFB6C1', outline='#FF69B4', width=1)
        draw.ellipse([70, 50, 80, 60], fill='#FFB6C1', outline='#FF69B4', width=1)
        
        return ImageTk.PhotoImage(img)
    
    def _create_speech_bubble(self, text, width=250, height=120):
        """吹き出し画像を動的に作成"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 設定から色を取得
        bubble_color = self.settings['bubble_color']
        text_color = self.settings['text_color']
        
        # 吹き出しの本体（角丸四角形）
        bubble_rect = [10, 10, width-10, height-35]
        draw.rounded_rectangle(bubble_rect, radius=20, fill=bubble_color, outline='#333333', width=2)
        
        # 影効果
        shadow_rect = [12, 12, width-8, height-33]
        draw.rounded_rectangle(shadow_rect, radius=20, fill='#00000020')
        draw.rounded_rectangle(bubble_rect, radius=20, fill=bubble_color, outline='#333333', width=2)
        
        # 吹き出しの尻尾
        tail_points = [(40, height-35), (25, height-5), (65, height-35)]
        draw.polygon(tail_points, fill=bubble_color, outline='#333333')
        
        # テキストを描画
        try:
            font_size = self.settings['font_size']
            font = ImageFont.load_default()
        except:
            font = None
        
        # テキストを複数行に分割して描画
        lines = self._wrap_text(text, 25)
        line_height = font_size + 4
        start_y = 25
        
        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            if y_pos < height - 45:  # 吹き出し内に収まる範囲で描画
                draw.text((25, y_pos), line, fill=text_color, font=font)
        
        return ImageTk.PhotoImage(img)
    
    def _wrap_text(self, text, max_chars_per_line):
        """テキストを指定文字数で改行"""
        lines = []
        for paragraph in text.split('\\n'):
            if len(paragraph) <= max_chars_per_line:
                lines.append(paragraph)
            else:
                words = paragraph.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) <= max_chars_per_line:
                        current_line += word + " "
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())
        return lines
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        self.main_frame = tk.Frame(self, bg=self.cget('bg'))
        self.main_frame.pack(fill='both', expand=True)
        
        # キャラクター表示エリア
        self.character_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.character_frame.pack(side='left', padx=15, pady=15)
        
        # キャラクター画像ラベル
        self.character_label = tk.Label(
            self.character_frame,
            image=self.character_image,
            bg=self.cget('bg')
        )
        self.character_label.pack()
        
        # 吹き出し表示エリア
        self.bubble_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.bubble_frame.pack(side='right', padx=15, pady=15, fill='both', expand=True)
        
        # 吹き出し画像を作成して表示
        self.speech_bubble_image = self._create_speech_bubble(self.current_message)
        self.bubble_label = tk.Label(
            self.bubble_frame,
            image=self.speech_bubble_image,
            bg=self.cget('bg')
        )
        self.bubble_label.pack()
        
        # ステータス表示（小さなインジケーター）
        self.status_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.status_frame.pack(side='bottom', fill='x')
        
        self.status_indicator = tk.Label(
            self.status_frame,
            text="●",
            fg='green',
            bg=self.cget('bg'),
            font=('Arial', 8)
        )
        self.status_indicator.pack(side='right', padx=5)
    
    def _setup_events(self):
        """イベントハンドラーを設定"""
        # マウスイベントをバインド
        widgets = [self, self.main_frame, self.character_frame, self.character_label, 
                  self.bubble_frame, self.bubble_label, self.status_frame]
        
        for widget in widgets:
            widget.bind("<Button-1>", self._on_mouse_click)
            widget.bind("<B1-Motion>", self._on_mouse_drag)
            widget.bind("<ButtonRelease-1>", self._on_mouse_release)
            widget.bind("<Button-3>", self._on_right_click)
            widget.bind("<Double-Button-1>", self._on_double_click)
        
        # キーボードイベント
        self.bind("<Escape>", self._on_escape)
        self.bind("<Return>", self._on_enter)
        self.bind("<Control-s>", self._on_save_settings)
        self.focus_set()
        
        # ウィンドウクローズイベント
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_mouse_click(self, event):
        """マウスクリック時の処理"""
        self.offset_x = self.winfo_pointerx() - self.winfo_rootx()
        self.offset_y = self.winfo_pointery() - self.winfo_rooty()
    
    def _on_mouse_drag(self, event):
        """マウスドラッグ時の処理"""
        if self.offset_x is not None and self.offset_y is not None:
            new_x = self.winfo_pointerx() - self.offset_x
            new_y = self.winfo_pointery() - self.offset_y
            self.geometry(f"+{new_x}+{new_y}")
            self.original_y = new_y  # アニメーション用の基準位置を更新
    
    def _on_mouse_release(self, event):
        """マウスリリース時の処理"""
        self.offset_x = None
        self.offset_y = None
    
    def _on_double_click(self, event):
        """ダブルクリック時の処理"""
        self._change_message()
    
    def _on_right_click(self, event):
        """右クリック時の処理"""
        self._show_context_menu(event)
    
    def _on_escape(self, event):
        """Escapeキー押下時の処理"""
        self._on_closing()
    
    def _on_enter(self, event):
        """Enterキー押下時の処理"""
        self._change_message()
    
    def _on_save_settings(self, event):
        """Ctrl+S押下時の処理"""
        self._save_settings()
        self.show_temporary_message("設定を保存しました", 2000)
    
    def _on_closing(self):
        """アプリケーション終了時の処理"""
        self._save_settings()
        self.animation_running = False
        self.quit()
        self.destroy()
    
    def _show_context_menu(self, event):
        """コンテキストメニューを表示"""
        context_menu = tk.Menu(self, tearoff=0)
        
        # メッセージ関連
        message_menu = tk.Menu(context_menu, tearoff=0)
        message_menu.add_command(label="メッセージ変更", command=self._change_message)
        message_menu.add_command(label="定型メッセージ", command=self._show_preset_messages)
        message_menu.add_command(label="メッセージ履歴", command=self._show_message_history)
        message_menu.add_separator()
        message_menu.add_command(label="自動メッセージ開始", command=self._start_auto_messages)
        message_menu.add_command(label="自動メッセージ停止", command=self._stop_auto_messages)
        
        context_menu.add_cascade(label="メッセージ", menu=message_menu)
        
        # 設定関連
        settings_menu = tk.Menu(context_menu, tearoff=0)
        settings_menu.add_command(label="外観設定", command=self._show_appearance_settings)
        settings_menu.add_command(label="動作設定", command=self._show_behavior_settings)
        settings_menu.add_command(label="設定リセット", command=self._reset_settings)
        
        context_menu.add_cascade(label="設定", menu=settings_menu)
        
        context_menu.add_separator()
        context_menu.add_command(label="情報", command=self._show_about)
        context_menu.add_command(label="終了", command=self._on_closing)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _change_message(self):
        """メッセージを変更"""
        new_message = simpledialog.askstring(
            "メッセージ変更",
            "新しいメッセージを入力してください:",
            initialvalue=self.current_message
        )
        
        if new_message is not None:
            self.set_message(new_message)
    
    def _show_preset_messages(self):
        """定型メッセージ選択ダイアログ"""
        preset_window = tk.Toplevel(self)
        preset_window.title("定型メッセージ")
        preset_window.geometry("350x450")
        preset_window.wm_attributes("-topmost", True)
        
        presets = [
            "こんにちは！",
            "お疲れ様です",
            "作業中です...",
            "休憩中",
            "会議中",
            "集中モード",
            "質問があります",
            "確認お願いします",
            "完了しました！",
            "ありがとうございます",
            "少々お待ちください",
            "対応中です",
            "確認中...",
            "準備中",
            "もうすぐ完了"
        ]
        
        tk.Label(preset_window, text="定型メッセージを選択:", font=('Arial', 12)).pack(pady=10)
        
        listbox = tk.Listbox(preset_window, height=12)
        listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        for preset in presets:
            listbox.insert(tk.END, preset)
        
        button_frame = tk.Frame(preset_window)
        button_frame.pack(pady=10)
        
        def select_preset():
            selection = listbox.curselection()
            if selection:
                selected_message = presets[selection[0]]
                self.set_message(selected_message)
                preset_window.destroy()
        
        tk.Button(button_frame, text="選択", command=select_preset).pack(side='left', padx=5)
        tk.Button(button_frame, text="キャンセル", command=preset_window.destroy).pack(side='left', padx=5)
    
    def _show_message_history(self):
        """メッセージ履歴を表示"""
        history_window = tk.Toplevel(self)
        history_window.title("メッセージ履歴")
        history_window.geometry("400x300")
        history_window.wm_attributes("-topmost", True)
        
        tk.Label(history_window, text="メッセージ履歴:", font=('Arial', 12)).pack(pady=10)
        
        listbox = tk.Listbox(history_window)
        listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        for msg in self.message_history[-20:]:  # 最新20件
            listbox.insert(tk.END, msg)
        
        def reuse_message():
            selection = listbox.curselection()
            if selection:
                selected_message = self.message_history[-(20-selection[0])]
                self.set_message(selected_message)
                history_window.destroy()
        
        button_frame = tk.Frame(history_window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="再利用", command=reuse_message).pack(side='left', padx=5)
        tk.Button(button_frame, text="閉じる", command=history_window.destroy).pack(side='left', padx=5)
    
    def _show_appearance_settings(self):
        """外観設定ダイアログ"""
        settings_window = tk.Toplevel(self)
        settings_window.title("外観設定")
        settings_window.geometry("400x500")
        settings_window.wm_attributes("-topmost", True)
        
        # 透明度設定
        tk.Label(settings_window, text="透明度:", font=('Arial', 10)).pack(pady=5)
        transparency_var = tk.DoubleVar(value=self.settings['transparency'])
        transparency_scale = tk.Scale(
            settings_window, from_=0.1, to=1.0, resolution=0.1,
            orient='horizontal', variable=transparency_var
        )
        transparency_scale.pack(fill='x', padx=20)
        
        # 吹き出し色設定
        tk.Label(settings_window, text="吹き出し色:", font=('Arial', 10)).pack(pady=5)
        bubble_color_var = tk.StringVar(value=self.settings['bubble_color'])
        
        def choose_bubble_color():
            color = colorchooser.askcolor(initialcolor=bubble_color_var.get())
            if color[1]:
                bubble_color_var.set(color[1])
        
        bubble_color_frame = tk.Frame(settings_window)
        bubble_color_frame.pack(pady=5)
        tk.Button(bubble_color_frame, text="色選択", command=choose_bubble_color).pack(side='left')
        tk.Label(bubble_color_frame, textvariable=bubble_color_var).pack(side='left', padx=10)
        
        # テキスト色設定
        tk.Label(settings_window, text="テキスト色:", font=('Arial', 10)).pack(pady=5)
        text_color_var = tk.StringVar(value=self.settings['text_color'])
        
        def choose_text_color():
            color = colorchooser.askcolor(initialcolor=text_color_var.get())
            if color[1]:
                text_color_var.set(color[1])
        
        text_color_frame = tk.Frame(settings_window)
        text_color_frame.pack(pady=5)
        tk.Button(text_color_frame, text="色選択", command=choose_text_color).pack(side='left')
        tk.Label(text_color_frame, textvariable=text_color_var).pack(side='left', padx=10)
        
        # フォントサイズ設定
        tk.Label(settings_window, text="フォントサイズ:", font=('Arial', 10)).pack(pady=5)
        font_size_var = tk.IntVar(value=self.settings['font_size'])
        font_size_scale = tk.Scale(
            settings_window, from_=8, to=20, orient='horizontal', variable=font_size_var
        )
        font_size_scale.pack(fill='x', padx=20)
        
        # 適用ボタン
        def apply_settings():
            self.settings['transparency'] = transparency_var.get()
            self.settings['bubble_color'] = bubble_color_var.get()
            self.settings['text_color'] = text_color_var.get()
            self.settings['font_size'] = font_size_var.get()
            
            # 設定を即座に反映
            self.wm_attributes("-alpha", self.settings['transparency'])
            self.speech_bubble_image = self._create_speech_bubble(self.current_message)
            self.bubble_label.configure(image=self.speech_bubble_image)
            
            settings_window.destroy()
        
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="適用", command=apply_settings).pack(side='left', padx=5)
        tk.Button(button_frame, text="キャンセル", command=settings_window.destroy).pack(side='left', padx=5)
    
    def _show_behavior_settings(self):
        """動作設定ダイアログ"""
        settings_window = tk.Toplevel(self)
        settings_window.title("動作設定")
        settings_window.geometry("350x300")
        settings_window.wm_attributes("-topmost", True)
        
        # 常に最前面
        topmost_var = tk.BooleanVar(value=self.settings['topmost'])
        tk.Checkbutton(settings_window, text="常に最前面に表示", variable=topmost_var).pack(pady=10)
        
        # アニメーション
        animation_var = tk.BooleanVar(value=self.settings['animation_enabled'])
        tk.Checkbutton(settings_window, text="アニメーション有効", variable=animation_var).pack(pady=5)
        
        # 自動非表示
        auto_hide_var = tk.BooleanVar(value=self.settings['auto_hide'])
        tk.Checkbutton(settings_window, text="一定時間後に自動非表示", variable=auto_hide_var).pack(pady=5)
        
        def apply_settings():
            self.settings['topmost'] = topmost_var.get()
            self.settings['animation_enabled'] = animation_var.get()
            self.settings['auto_hide'] = auto_hide_var.get()
            
            # 設定を即座に反映
            self.wm_attributes("-topmost", self.settings['topmost'])
            
            if not self.settings['animation_enabled']:
                self.animation_running = False
            else:
                self._start_animation()
            
            settings_window.destroy()
        
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="適用", command=apply_settings).pack(side='left', padx=5)
        tk.Button(button_frame, text="キャンセル", command=settings_window.destroy).pack(side='left', padx=5)
    
    def _reset_settings(self):
        """設定をリセット"""
        if messagebox.askyesno("設定リセット", "設定を初期値にリセットしますか？"):
            self.settings = {
                'transparency': 0.95,
                'topmost': True,
                'bubble_color': '#FFFFFF',
                'text_color': '#000000',
                'font_size': 12,
                'auto_hide': False,
                'animation_enabled': True
            }
            self._save_settings()
            messagebox.showinfo("完了", "設定をリセットしました。再起動してください。")
    
    def _show_about(self):
        """アプリケーション情報を表示"""
        about_text = """
Advanced Character Overlay v1.0

キャラクター付きオーバーレイアプリケーション

機能:
• 他のアプリの上に常に表示
• ドラッグで移動可能
• カスタマイズ可能な吹き出し
• メッセージ履歴
• 設定保存
• アニメーション効果

操作方法:
• ドラッグ: 移動
• ダブルクリック: メッセージ変更
• 右クリック: メニュー
• Enter: メッセージ変更
• Escape: 終了
• Ctrl+S: 設定保存
        """
        messagebox.showinfo("アプリケーション情報", about_text)
    
    def _start_auto_messages(self):
        """自動メッセージ表示を開始"""
        self.auto_message_enabled = True
        self.status_indicator.configure(fg='orange')
        
        auto_messages = [
            "作業中...",
            "進行中",
            "確認中",
            "処理中",
            "待機中"
        ]
        
        def auto_message_loop():
            import random
            while self.auto_message_enabled:
                if auto_messages:
                    message = random.choice(auto_messages)
                    self.set_message(message)
                time.sleep(5)  # 5秒間隔
        
        threading.Thread(target=auto_message_loop, daemon=True).start()
    
    def _stop_auto_messages(self):
        """自動メッセージ表示を停止"""
        self.auto_message_enabled = False
        self.status_indicator.configure(fg='green')
    
    def _start_animation(self):
        """アニメーションを開始"""
        if self.settings['animation_enabled'] and not self.animation_running:
            self.animation_running = True
            self._animate_bounce()
    
    def _animate_bounce(self):
        """バウンスアニメーション"""
        if not self.animation_running or not self.settings['animation_enabled']:
            return
        
        try:
            current_y = self.winfo_y()
            new_y = current_y + self.bounce_direction
            
            # バウンス範囲を制限
            if abs(new_y - self.original_y) > 3:
                self.bounce_direction *= -1
                new_y = current_y + self.bounce_direction
            
            self.geometry(f"+{self.winfo_x()}+{new_y}")
            
            # 次のアニメーションフレームをスケジュール
            self.after(100, self._animate_bounce)
        except tk.TclError:
            # ウィンドウが破棄された場合
            self.animation_running = False
    
    def set_message(self, message):
        """メッセージを設定"""
        self.current_message = message
        self.message_history.append(message)
        
        # 履歴の長さを制限
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-50:]
        
        # 吹き出し画像を更新
        self.speech_bubble_image = self._create_speech_bubble(message)
        self.bubble_label.configure(image=self.speech_bubble_image)
        
        print(f"メッセージを更新: {message}")
    
    def show_temporary_message(self, message, duration=3000):
        """一時的なメッセージを表示"""
        original_message = self.current_message
        self.set_message(message)
        
        def restore_message():
            self.set_message(original_message)
        
        self.after(duration, restore_message)
    
    def get_message(self):
        """現在のメッセージを取得"""
        return self.current_message
    
    def run(self):
        """アプリケーションを実行"""
        try:
            self.mainloop()
        except KeyboardInterrupt:
            print("\nアプリケーションを終了します...")
            self._on_closing()


def main():
    """メイン関数"""
    print("高度なキャラクターオーバーレイアプリケーションを起動中...")
    
    # 依存関係チェック
    try:
        from PIL import Image, ImageTk, ImageDraw, ImageFont
    except ImportError:
        print("PILライブラリが必要です。インストールしてください:")
        print("pip install Pillow")
        return
    
    # アプリケーションを作成
    app = AdvancedCharacterOverlay(width=400, height=280, x=200, y=150)
    
    print("アプリケーションが起動しました")
    print("\n=== 操作方法 ===")
    print("• ドラッグ: ウィンドウを移動")
    print("• ダブルクリック: メッセージ変更")
    print("• 右クリック: コンテキストメニュー")
    print("• Enter: メッセージ変更")
    print("• Ctrl+S: 設定保存")
    print("• Escape: 終了")
    print("\n=== 機能 ===")
    print("• カスタマイズ可能な外観")
    print("• メッセージ履歴")
    print("• 自動メッセージ表示")
    print("• アニメーション効果")
    print("• 設定の保存/復元")
    
    # アプリケーションを実行
    app.run()


if __name__ == "__main__":
    main()
