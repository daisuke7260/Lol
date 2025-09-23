#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャラクター付きオーバーレイアプリケーション
キャラクターと吹き出しでメッセージを表示する
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sys
import os
import logging


class CharacterOverlay(tk.Tk):
    """
    キャラクター付きオーバーレイウィンドウ
    キャラクターと吹き出しでメッセージを表示
    """
    
    def __init__(self, width=350, height=250, x=100, y=100):
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
        
        # 画像リソース
        self.character_image = None
        self.speech_bubble_image = None
        
        # ウィンドウの初期設定
        self._setup_window()
        self._load_images()
        self._create_widgets()
        self._setup_events()
    
    def _setup_window(self):
        """ウィンドウの基本設定を行う"""
        self.title("Character Overlay")
        
        # ウィンドウサイズと位置を設定
        geometry = f"{self.window_width}x{self.window_height}+{self.window_x}+{self.window_y}"
        self.geometry(geometry)
        
        # 常に最前面に表示
        self.wm_attributes("-topmost", True)
        
        # ウィンドウボーダーを削除
        self.overrideredirect(True)
        
        # フォーカスを強制取得
        self.focus_force()
        
        # 背景を透明に設定（プラットフォーム依存）
        self._setup_transparency()
    
    def _setup_transparency(self):
        """透明化設定"""
        try:
            # 透明度を設定
            self.wm_attributes("-alpha", 0.95)
            
            # プラットフォーム固有の透明化
            if sys.platform.startswith('win'):
                # Windowsの場合、特定色を透明化
                self.configure(bg='white')
                self.wm_attributes("-transparentcolor", "white")
            else:
                # その他のプラットフォーム
                self.configure(bg='#f0f0f0')
        except tk.TclError:
            # 透明化がサポートされていない場合
            self.configure(bg='lightblue')
    
    def _load_images(self):
        """画像リソースを読み込む"""
        try:
            # キャラクター画像を読み込み: スクリプトのあるディレクトリ -> カレントワーキングディレクトリ
            script_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(script_dir, 'character.png'),
                os.path.join(os.getcwd(), 'character.png')
            ]

            found = False
            for path in candidates:
                if os.path.exists(path):
                    char_img = Image.open(path)
                    # サイズを調整
                    char_img = char_img.resize((80, 80), Image.Resampling.LANCZOS)
                    self.character_image = ImageTk.PhotoImage(char_img)
                    found = True
                    break

            if not found:
                # デフォルトキャラクターを作成
                self.character_image = self._create_default_character()
                
        except Exception as e:
            try:
                logger = logging.getLogger(__name__)
                logger.exception(f"画像読み込みエラー: {e}")
            except Exception:
                # ログに失敗しても続行
                pass
            # デフォルト画像を作成
            self.character_image = self._create_default_character()
    
    def _create_default_character(self):
        """デフォルトキャラクター画像を作成"""
        # 80x80のデフォルトキャラクター画像を作成
        img = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 顔の輪郭
        draw.ellipse([10, 10, 70, 70], fill='#FFE4B5', outline='#DEB887', width=2)
        
        # 目
        draw.ellipse([25, 30, 35, 40], fill='black')
        draw.ellipse([45, 30, 55, 40], fill='black')
        
        # 口
        draw.arc([30, 45, 50, 55], start=0, end=180, fill='black', width=2)
        
        return ImageTk.PhotoImage(img)
    
    def _create_speech_bubble(self, text, width=200, height=100):
        """吹き出し画像を動的に作成"""
        # 吹き出しの背景画像を作成
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 吹き出しの本体（角丸四角形）
        bubble_rect = [10, 10, width-10, height-30]
        draw.rounded_rectangle(bubble_rect, radius=15, fill='white', outline='#333333', width=2)
        
        # 吹き出しの尻尾
        tail_points = [(30, height-30), (20, height-5), (50, height-30)]
        draw.polygon(tail_points, fill='white', outline='#333333')
        
        # テキストを描画
        try:
            # フォントを設定（システムフォントを使用）
            font_size = 12
            font = ImageFont.load_default()
        except:
            font = None
        
        # テキストを複数行に分割
        lines = text.split('\n')
        line_height = 16
        start_y = 20
        
        for i, line in enumerate(lines):
            if len(line) > 20:  # 長い行は自動改行
                words = line.split(' ')
                current_line = ""
                y_offset = start_y + i * line_height
                
                for word in words:
                    test_line = current_line + word + " "
                    if len(test_line) > 20:
                        if current_line:
                            draw.text((20, y_offset), current_line.strip(), fill='black', font=font)
                            y_offset += line_height
                        current_line = word + " "
                    else:
                        current_line = test_line
                
                if current_line:
                    draw.text((20, y_offset), current_line.strip(), fill='black', font=font)
            else:
                draw.text((20, start_y + i * line_height), line, fill='black', font=font)
        
        return ImageTk.PhotoImage(img)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインフレーム
        self.main_frame = tk.Frame(self, bg=self.cget('bg'))
        self.main_frame.pack(fill='both', expand=True)
        
        # キャラクター表示エリア
        self.character_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.character_frame.pack(side='left', padx=10, pady=10)
        
        # キャラクター画像ラベル
        self.character_label = tk.Label(
            self.character_frame,
            image=self.character_image,
            bg=self.cget('bg')
        )
        self.character_label.pack()
        
        # 吹き出し表示エリア
        self.bubble_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.bubble_frame.pack(side='right', padx=10, pady=10, fill='both', expand=True)
        
        # 吹き出し画像を作成して表示
        self.speech_bubble_image = self._create_speech_bubble(self.current_message)
        self.bubble_label = tk.Label(
            self.bubble_frame,
            image=self.speech_bubble_image,
            bg=self.cget('bg')
        )
        self.bubble_label.pack()
    
    def _setup_events(self):
        """イベントハンドラーを設定"""
        # マウスイベントをバインド（全てのウィジェットに）
        widgets = [self, self.main_frame, self.character_frame, self.character_label, 
                  self.bubble_frame, self.bubble_label]
        
        for widget in widgets:
            widget.bind("<Button-1>", self._on_mouse_click)
            widget.bind("<B1-Motion>", self._on_mouse_drag)
            widget.bind("<ButtonRelease-1>", self._on_mouse_release)
            widget.bind("<Button-3>", self._on_right_click)
        
        # キーボードイベント
        self.bind("<Escape>", self._on_escape)
        self.bind("<Return>", self._on_enter)
        self.focus_set()
    
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
    
    def _on_mouse_release(self, event):
        """マウスリリース時の処理"""
        self.offset_x = None
        self.offset_y = None
    
    def _on_right_click(self, event):
        """右クリック時の処理"""
        self._show_context_menu(event)
    
    def _on_escape(self, event):
        """Escapeキー押下時の処理"""
        self.quit()
    
    def _on_enter(self, event):
        """Enterキー押下時の処理"""
        self._change_message()
    
    def _show_context_menu(self, event):
        """コンテキストメニューを表示"""
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="メッセージ変更", command=self._change_message)
        context_menu.add_command(label="定型メッセージ", command=self._show_preset_messages)
        context_menu.add_separator()
        context_menu.add_command(label="透明度設定", command=self._change_transparency)
        context_menu.add_command(label="常に最前面", command=self._toggle_topmost)
        context_menu.add_separator()
        context_menu.add_command(label="終了", command=self.quit)
        
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
        preset_window.geometry("300x400")
        preset_window.wm_attributes("-topmost", True)
        
        # 定型メッセージリスト
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
            "ありがとうございます"
        ]
        
        tk.Label(preset_window, text="定型メッセージを選択:", font=('Arial', 12)).pack(pady=10)
        
        listbox = tk.Listbox(preset_window, height=10)
        listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        for preset in presets:
            listbox.insert(tk.END, preset)
        
        def select_preset():
            selection = listbox.curselection()
            if selection:
                selected_message = presets[selection[0]]
                self.set_message(selected_message)
                preset_window.destroy()
        
        tk.Button(preset_window, text="選択", command=select_preset).pack(pady=5)
        tk.Button(preset_window, text="キャンセル", command=preset_window.destroy).pack(pady=5)
    
    def _change_transparency(self):
        """透明度を変更"""
        try:
            current_alpha = self.wm_attributes("-alpha")
            new_alpha = simpledialog.askfloat(
                "透明度設定",
                "透明度を入力してください (0.1-1.0):",
                initialvalue=current_alpha,
                minvalue=0.1,
                maxvalue=1.0
            )
            
            if new_alpha is not None:
                self.wm_attributes("-alpha", new_alpha)
        except tk.TclError:
            messagebox.showwarning("警告", "透明度設定はサポートされていません")
    
    def _toggle_topmost(self):
        """常に最前面表示の切り替え"""
        current_topmost = self.wm_attributes("-topmost")
        self.wm_attributes("-topmost", not current_topmost)
        
        status = "有効" if not current_topmost else "無効"
        messagebox.showinfo("設定変更", f"常に最前面表示を{status}にしました")
    
    def set_message(self, message):
        """メッセージを設定"""
        self.current_message = message
        self.message_history.append(message)
        
        # 吹き出し画像を更新
        self.speech_bubble_image = self._create_speech_bubble(message)
        self.bubble_label.configure(image=self.speech_bubble_image)
        
        print(f"メッセージを更新: {message}")
    
    def get_message(self):
        """現在のメッセージを取得"""
        return self.current_message
    
    def run(self):
        """アプリケーションを実行"""
        try:
            self.mainloop()
        except KeyboardInterrupt:
            print("\nアプリケーションを終了します...")
            self.quit()


def main():
    """メイン関数"""
    print("キャラクターオーバーレイアプリケーションを起動中...")
    
    # PILが利用可能かチェック
    try:
        from PIL import Image, ImageTk, ImageDraw, ImageFont
    except ImportError:
        print("PILライブラリが必要です。インストールしてください:")
        print("pip install Pillow")
        return
    
    # アプリケーションを作成
    app = CharacterOverlay(width=350, height=250, x=200, y=150)
    
    print("アプリケーションが起動しました")
    print("操作方法:")
    print("- ドラッグで移動")
    print("- 右クリックでメニュー")
    print("- Enterキーでメッセージ変更")
    print("- Escキーで終了")
    
    # アプリケーションを実行
    app.run()


if __name__ == "__main__":
    main()
