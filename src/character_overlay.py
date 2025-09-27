#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャラクター付きオーバーレイアプリケーション
キャラクターと吹き出しでメッセージを表示する
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import sys
import os
import logging


class CharacterOverlay(tk.Toplevel):
    """キャラクター付きオーバーレイウィンドウ"""

    def __init__(self, parent=None, width=350, height=250, x=100, y=100):
        # 親ウィンドウが指定されていない場合は新しいルートを作成
        if parent is None:
            self.root = tk.Tk()
            super().__init__(self.root)
            self.is_standalone = True
        else:
            super().__init__(parent)
            self.root = parent
            self.is_standalone = False
            
        self.window_width = width
        self.window_height = height
        self.window_x = x
        self.window_y = y
        
        # 画像オブジェクトの初期化
        self.character_image = None
        self.speech_bubble_image = None

        self._setup_window()
        self._load_images()
        self._create_widgets()
        self._setup_events()

    def _setup_window(self):
        self.title("Character Overlay")
        self.geometry(f"{self.window_width}x{self.window_height}+{self.window_x}+{self.window_y}")
        self.wm_attributes("-topmost", True)
        self.overrideredirect(True)
        self.focus_force()
        try:
            if sys.platform.startswith('win'):
                self.configure(bg='#FF00FF')
                self.wm_attributes('-transparentcolor', '#FF00FF')
            else:
                self.configure(bg='#f0f0f0')
        except tk.TclError:
            self.configure(bg='lightblue')

    def _load_images(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [os.path.join(script_dir, 'character.png'), os.path.join(os.getcwd(), 'character.png')]
            found = False
            for path in candidates:
                if os.path.exists(path):
                    img = Image.open(path).convert('RGBA')
                    self.character_image = ImageTk.PhotoImage(img.resize((80, 80), Image.Resampling.LANCZOS))
                    found = True
                    break
            if not found:
                self.character_image = self._create_default_character()
        except Exception as e:
            logging.getLogger(__name__).exception(f"画像読み込みエラー: {e}")
            self.character_image = self._create_default_character()

    def _create_default_character(self):
        img = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        w, h = 80, 80
        pad = 10
        draw.ellipse([pad, pad, w - pad, h - pad], fill='#FFE4B5', outline='#DEB887', width=2)
        draw.ellipse([w*0.31, h*0.38, w*0.44, h*0.5], fill='black')
        draw.ellipse([w*0.62, h*0.38, w*0.77, h*0.5], fill='black')
        draw.arc([w*0.37, h*0.57, w*0.63, h*0.7], start=0, end=180, fill='black', width=2)
        return ImageTk.PhotoImage(img)

    def _get_japanese_font(self, size=12):
        """日本語対応フォントを取得"""
        try:
            # Windowsの標準日本語フォントを試す
            font_candidates = [
                "C:/Windows/Fonts/msgothic.ttc",  # MS ゴシック
                "C:/Windows/Fonts/meiryo.ttc",    # メイリオ
                "C:/Windows/Fonts/YuGothM.ttc",   # 游ゴシック Medium
                "C:/Windows/Fonts/NotoSansCJK-Regular.ttc",  # Noto Sans CJK
                "arial.ttf"  # フォールバック
            ]
            
            for font_path in font_candidates:
                try:
                    if os.path.exists(font_path):
                        return ImageFont.truetype(font_path, size)
                    else:
                        # システムフォントとして試す
                        return ImageFont.truetype(os.path.basename(font_path), size)
                except (IOError, OSError):
                    continue
            
            # 最後の手段：デフォルトフォント
            return ImageFont.load_default()
            
        except Exception as e:
            logging.getLogger(__name__).debug(f"フォント取得エラー: {e}")
            return ImageFont.load_default()

    def _create_speech_bubble(self, text, width=200, height=100):
        """吹き出しを作成する関数"""
        try:
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 尻尾
            tail_points = [(6, height//3), (22, height//3 - 10), (22, height//3 + 10)]
            draw.polygon(tail_points, fill='white', outline='#333333')
            
            # 吹き出し本体
            bubble_rect = [12, 10, width - 10, height - 10]
            draw.rounded_rectangle(bubble_rect, radius=15, fill='white', outline='#333333', width=2)
            
            # 日本語対応フォントを取得
            font = self._get_japanese_font(size=12)
            
            # テキストを描画
            lines = text.split('\n')
            line_height = 18
            start_y = bubble_rect[1] + 10
            
            for i, line in enumerate(lines):
                y = start_y + i * line_height
                if y + line_height <= bubble_rect[3] - 10:
                    draw.text((bubble_rect[0] + 10, y), line, fill='black', font=font)
            
            return ImageTk.PhotoImage(img)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"吹き出し作成エラー: {e}")
            # 最小限の吹き出しを作成
            try:
                simple_img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
                simple_draw = ImageDraw.Draw(simple_img)
                simple_draw.rectangle([0, 0, width-1, height-1], outline='black')
                font = self._get_japanese_font(size=10)
                simple_draw.text((10, 10), text[:20], fill='black', font=font)
                return ImageTk.PhotoImage(simple_img)
            except:
                return None

    def _create_widgets(self):
        # メインフレーム作成
        self.main_frame = tk.Frame(self, bg=self.cget('bg'))
        self.main_frame.pack(fill='both', expand=False)

        # キャラクター部分
        self.character_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.character_frame.pack(side='left', anchor='n', padx=10, pady=10)
        
        # 画像が正常に作成されている場合のみラベルを作成
        if self.character_image:
            self.character_label = tk.Label(self.character_frame, image=self.character_image, bg=self.cget('bg'))
            self.character_label.pack(anchor='n')
        else:
            # フォールバック: テキストラベル
            self.character_label = tk.Label(self.character_frame, text="🤖", 
                                          font=('MS Gothic', 40), bg=self.cget('bg'))
            self.character_label.pack(anchor='n')

        # 吹き出し部分
        self.bubble_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.bubble_frame.pack(side='left', anchor='n', padx=10, pady=10)
        
        # 初期吹き出しを作成
        try:
            self.speech_bubble_image = self._create_speech_bubble("こんにちは！")
            self.bubble_label = tk.Label(self.bubble_frame, image=self.speech_bubble_image, bg=self.cget('bg'))
        except Exception as e:
            logging.getLogger(__name__).error(f"吹き出し作成エラー: {e}")
            # フォールバック: テキストのみ
            self.bubble_label = tk.Label(self.bubble_frame, text="こんにちは！", 
                                       bg='white', relief='solid', borderwidth=1, 
                                       font=('MS Gothic', 10),
                                       padx=10, pady=5, wraplength=150)
        
        self.bubble_label.pack(anchor='n')

    def _setup_events(self):
        self.offset_x = None
        self.offset_y = None
        
        widgets = [self, self.main_frame, self.character_frame, self.character_label, self.bubble_frame, self.bubble_label]
        for widget in widgets:
            widget.bind('<Button-1>', self._on_mouse_click)
            widget.bind('<B1-Motion>', self._on_mouse_drag)
            widget.bind('<ButtonRelease-1>', self._on_mouse_release)
            widget.bind('<Button-3>', self._on_right_click)
        self.bind('<Escape>', self._on_escape)
        self.focus_set()

    def _on_mouse_click(self, event):
        self.offset_x = self.winfo_pointerx() - self.winfo_rootx()
        self.offset_y = self.winfo_pointery() - self.winfo_rooty()

    def _on_mouse_drag(self, event):
        if self.offset_x is not None and self.offset_y is not None:
            new_x = self.winfo_pointerx() - self.offset_x
            new_y = self.winfo_pointery() - self.offset_y
            self.geometry(f'+{new_x}+{new_y}')

    def _on_mouse_release(self, event):
        self.offset_x = None
        self.offset_y = None

    def _on_right_click(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='メッセージ変更', command=self._change_message)
        menu.add_separator()
        menu.add_command(label='終了', command=self.quit_overlay)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_escape(self, event):
        self.quit_overlay()

    def _change_message(self):
        new_message = simpledialog.askstring('メッセージ変更', '新しいメッセージを入力してください:', initialvalue="こんにちは！")
        if new_message is not None:
            self.set_message(new_message)

    def set_message(self, message):
        """メッセージを更新する"""
        try:
            # 新しい吹き出し画像を作成
            new_bubble_image = self._create_speech_bubble(message)
            
            # 古い画像の参照を保持してからクリア
            old_image = getattr(self, 'speech_bubble_image', None)
            
            # 新しい画像を設定
            self.speech_bubble_image = new_bubble_image
            self.bubble_label.configure(image=self.speech_bubble_image)
            
            # ガベージコレクション用に少し待つ
            self.after_idle(lambda: None)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"メッセージ更新エラー: {e}")
            # フォールバックとしてテキストのみ表示
            self.bubble_label.configure(image='', text=message, 
                                      bg='white', relief='solid', borderwidth=1,
                                      font=('MS Gothic', 10),
                                      padx=10, pady=5, wraplength=150)

    def run(self):
        """オーバーレイを実行"""
        try:
            if self.is_standalone:
                # スタンドアロンモードの場合のみmainloopを実行
                self.root.mainloop()
            else:
                # 子ウィンドウの場合は表示のみ
                self.deiconify()
        except KeyboardInterrupt:
            logging.getLogger(__name__).info('アプリケーションを終了します...')
            self.quit_overlay()
    
    def quit_overlay(self):
        """オーバーレイを終了"""
        try:
            if self.is_standalone:
                self.root.quit()
                self.root.destroy()
            else:
                self.destroy()
        except:
            pass


def main():
    try:
        from PIL import Image, ImageTk, ImageDraw, ImageFont
    except ImportError:
        print('PILライブラリが必要です。インストールしてください:')
        print('pip install Pillow')
        return
    app = CharacterOverlay(width=350, height=200, x=200, y=150)
    app.run()


if __name__ == '__main__':
    main()
