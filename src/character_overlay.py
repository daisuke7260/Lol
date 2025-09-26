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


class CharacterOverlay(tk.Tk):
    """キャラクター付きオーバーレイウィンドウ"""

    def __init__(self, width=350, height=250, x=100, y=100):
        super().__init__()
        self.window_width = width
        self.window_height = height
        self.window_x = x
        self.window_y = y

    # スケーリングの基準となるウィンドウの基本サイズ
        self._base_window_width = width
        self._base_window_height = height

    # アセット（画像）の基本サイズ
        self._char_base_size = (80, 80)  # width, height
        self._bubble_base_size = (200, 100)

    # リサンプリング用に元のPIL画像を保持
        self._char_pil = None

        self.offset_x = None
        self.offset_y = None

        self.current_message = "こんにちわ"
        self.message_history = []

        self.character_image = None
        self.speech_bubble_image = None

    # リサイズ状態の変数
        self.resizing = False
        self.start_x = 0
        self.start_y = 0
        self.start_width = width
        self.start_height = height

        self._setup_window()
        self._load_images()
        self._create_widgets()
        self._setup_events()
        # predictions.txt を監視して吹き出しを更新するためのパス
        try:
            self._pred_file = os.path.join(os.path.dirname(__file__), 'predictions.txt')
        except Exception:
            self._pred_file = os.path.join('.', 'predictions.txt')
        # 最後に読み込んだファイル内容ハッシュを保持して冗長更新を防ぐ
        self._last_pred_content = None
        # ポーリング開始（アプリケーションのメインループ内で動作）
        self.after(1000, self._poll_predictions_file)

    def _setup_window(self):
        self.title("Character Overlay")
        self.geometry(f"{self.window_width}x{self.window_height}+{self.window_x}+{self.window_y}")
        self.wm_attributes("-topmost", True)
        self.overrideredirect(True)
        self.focus_force()
        try:
            #self.wm_attributes("-alpha", 0.95)
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
                    # 後でリサンプリングするため、基準サイズのPILイメージを保持する
                    self._char_pil = img.resize(self._char_base_size, Image.Resampling.LANCZOS)
                    self.character_image = ImageTk.PhotoImage(self._char_pil)
                    found = True
                    break
            if not found:
                # デフォルトのPILキャラクターを作成して保持する
                self._char_pil = self._create_default_character_pil()
                self.character_image = ImageTk.PhotoImage(self._char_pil)
        except Exception as e:
            logging.getLogger(__name__).exception(f"画像読み込みエラー: {e}")
            self._char_pil = self._create_default_character_pil()
            self.character_image = ImageTk.PhotoImage(self._char_pil)

    def _create_default_character_pil(self):
        # PIL Image（基準サイズ）を返す
        img = Image.new('RGBA', self._char_base_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        w, h = self._char_base_size
        pad = 10
        draw.ellipse([pad, pad, w - pad, h - pad], fill='#FFE4B5', outline='#DEB887', width=2)
        draw.ellipse([w*0.31, h*0.38, w*0.44, h*0.5], fill='black')
        draw.ellipse([w*0.62, h*0.38, w*0.77, h*0.5], fill='black')
        draw.arc([w*0.37, h*0.57, w*0.63, h*0.7], start=0, end=180, fill='black', width=2)
        return img

    def _create_default_character(self):
        # 互換性のためのヘルパー: ImageTk.PhotoImage を返す
        pil = self._create_default_character_pil()
        return ImageTk.PhotoImage(pil)

    def _create_speech_bubble(self, text, width=200, height=100):
        """吹き出しを作成する関数"""
        # 描画幅を測定してワードラップを行うための初期画像を作成
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 尻尾は左側に配置する（キャラクター画像のすぐ右、やや上寄せになるよう調整）
        # tail_x は吹き出し左端に近い位置にし、tail_y はやや上寄せ
        tail_y = max(int(height * 0.33), height // 3)
        tail_points = [(6, tail_y), (22, tail_y - max(6, int(height * 0.12))), (22, tail_y + max(6, int(height * 0.12)))]

        # 吹き出し描画領域（左側に小さめの尻尾スペースを残す）
        left_pad = 12
        right_pad = 10
        top_pad = 10
        bottom_pad = 10
        bubble_rect = [left_pad, top_pad, width - right_pad, height - bottom_pad]

        # 吹き出しの高さに応じたフォントサイズを決定
        try:
            font_size = max(8, int(height * 0.22))
        except Exception:
            font_size = 12

        font = None
        # プラットフォームに応じたフォント候補（日本語対応を優先）
        if sys.platform.startswith('win'):
            candidates = ('meiryo.ttc', 'meiryo.ttf', 'YuGothic.ttf', 'YuGothicUI.ttf', 'msgothic.ttc', 'msyh.ttc', 'arialuni.ttf', 'arial.ttf')
        elif sys.platform.startswith('darwin'):
            candidates = ('Hiragino Maru Gothic ProN.ttf', 'Hiragino Sans W3.ttc', 'Arial Unicode.ttf', 'DejaVuSans.ttf')
        else:
            candidates = ('NotoSansCJK-Regular.ttc', 'NotoSansCJKjp-Regular.otf', 'DejaVuSans.ttf', 'DroidSansFallback.ttf')

        for fname in candidates:
            try:
                font = ImageFont.truetype(fname, font_size)
                break
            except Exception:
                font = None

        if font is None:
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

        # 吹き出し内で使用可能なテキスト幅を算出（尻尾領域を除外）
        text_area_x = bubble_rect[0] + 10
        text_area_w = bubble_rect[2] - text_area_x - 10

        # 描画幅を測定してワードラップを行う。行が収まらない場合は幅を拡張して再試行する
        # 非常に長い単語は文字単位で分割して折り返す
        max_allowed_width = 3000
        lines_out = []
        while True:
            lines_out = []
            max_line_px = 0
            for para in text.split('\n'):
                words = para.split(' ')
                cur = ''
                for w in words:
                    # 関数: 長すぎる単語を幅に収まるチャンクに分割
                    def split_long_word(word, draw_obj, font_obj, max_px):
                        parts = []
                        s = word
                        while s:
                            # 二分探索で最大フィット長を探す
                            lo, hi = 1, len(s)  
                            fit = 0
                            while lo <= hi:
                                mid = (lo + hi) // 2
                                try:
                                    bbox = draw_obj.textbbox((0, 0), s[:mid], font=font_obj)
                                    w_px = bbox[2] - bbox[0]
                                except Exception:
                                    w_px = mid * (font_obj.size if hasattr(font_obj, 'size') else 8)
                                if w_px <= max_px:
                                    fit = mid
                                    lo = mid + 1
                                else:
                                    hi = mid - 1
                            if fit == 0:
                                # 1文字も入らない場合は強制的に1文字を取り出す
                                fit = 1
                            parts.append(s[:fit])
                            s = s[fit:]
                        return parts

                    candidate = w if cur == '' else cur + ' ' + w
                    try:
                        bbox = draw.textbbox((0, 0), candidate, font=font)
                        w_px = bbox[2] - bbox[0]
                    except Exception:
                        w_px = len(candidate) * (font.size if hasattr(font, 'size') else 8)

                    if w_px <= text_area_w:
                        cur = candidate
                        max_line_px = max(max_line_px, w_px)
                    else:
                        # まず現在の蓄積を行に確定
                        if cur:
                            lines_out.append(cur)
                            try:
                                bbox_cur = draw.textbbox((0, 0), cur, font=font)
                                max_line_px = max(max_line_px, bbox_cur[2] - bbox_cur[0])
                            except Exception:
                                pass
                        # この単語自体が長すぎる場合は分割して挿入
                        try:
                            bbox_w = draw.textbbox((0, 0), w, font=font)[2] - draw.textbbox((0, 0), w, font=font)[0]
                        except Exception:
                            bbox_w = len(w) * (font.size if hasattr(font, 'size') else 8)
                        if bbox_w > text_area_w:
                            parts = split_long_word(w, draw, font, text_area_w)
                            for i, p in enumerate(parts):
                                if i == 0:
                                    # 最初のチャンクは cur が空の状態で追加
                                    lines_out.append(p)
                                else:
                                    lines_out.append(p)
                                try:
                                    bbox_p = draw.textbbox((0, 0), p, font=font)
                                    max_line_px = max(max_line_px, bbox_p[2] - bbox_p[0])
                                except Exception:
                                    pass
                            cur = ''
                        else:
                            # 単語は分割不要だが現在の行には入らない -> 新しい行として開始
                            cur = w
                if cur:
                    lines_out.append(cur)
                    try:
                        bbox_cur = draw.textbbox((0, 0), cur, font=font)
                        max_line_px = max(max_line_px, bbox_cur[2] - bbox_cur[0])
                    except Exception:
                        pass

            # 最長行がはみ出す場合は幅を拡張（上限を大きくして可能な限り収める）
            if max_line_px > text_area_w and width < max_allowed_width:
                extra = max_line_px - text_area_w + 40
                width = min(max_allowed_width, width + extra)
                # 新しい幅で画像/描画を再生成し、吹き出し領域とテキスト幅を再計算
                img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                bubble_rect = [left_pad, top_pad, width - right_pad, height - bottom_pad]
                text_area_x = bubble_rect[0] + 10
                text_area_w = bubble_rect[2] - text_area_x - 10
                # ループを継続して再ラップ
                continue
            break

        # フォントメトリクスから行高さを決定
        try:
            ascent, descent = font.getmetrics() if hasattr(font, 'getmetrics') else (0, 0)
            char_h = ascent + descent if ascent + descent > 0 else (draw.textbbox((0, 0), 'A', font=font)[3])
        except Exception:
            try:
                char_h = draw.textbbox((0, 0), 'A', font=font)[3]
            except Exception:
                char_h = 12
        line_height = int(char_h + max(4, font_size * 0.15))

        # 必要な高さを計算し、必要なら画像高さを拡張
        required_text_h = len(lines_out) * line_height + top_pad + bottom_pad
        required_h = max(height, required_text_h + 10)
        if required_h != height:
            img = Image.new('RGBA', (width, required_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            bubble_rect = [left_pad, top_pad, width - right_pad, required_h - bottom_pad]
            tail_y = max(int(required_h * 0.33), (bubble_rect[1] + bubble_rect[3]) // 2)
            tail_points = [(6, tail_y), (22, tail_y - max(6, int(required_h * 0.12))), (22, tail_y + max(6, int(required_h * 0.12)))]

        # 尻尾を先に描画し、その後に吹き出し本体を描画することで尻尾を後ろに配置する
        draw.polygon(tail_points, fill='white', outline='#333333')
        draw.rounded_rectangle(bubble_rect, radius=15, fill='white', outline='#333333', width=2)

        # テキスト行を描画
        text_x = text_area_x
        start_y = bubble_rect[1] + 8
        for i, line in enumerate(lines_out):
            y = start_y + i * line_height
            draw.text((text_x, y), line, fill='black', font=font)

        return ImageTk.PhotoImage(img)

    def _create_widgets(self):
    # メインコンテナ: リサイズ時に子ウィジェットのレイアウトが再配置されないよう固定する
        self.main_frame = tk.Frame(self, bg=self.cget('bg'))
        self.main_frame.pack(fill='both', expand=False)

    # キャラクター表示領域（左上）
        self.character_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.character_frame.pack(side='left', anchor='n', padx=10, pady=10)
        self.character_label = tk.Label(self.character_frame, image=self.character_image, bg=self.cget('bg'))
        self.character_label.pack(anchor='n')

    # キャラクター横の吹き出し表示領域
        self.bubble_frame = tk.Frame(self.main_frame, bg=self.cget('bg'))
        self.bubble_frame.pack(side='left', anchor='n', padx=10, pady=10)
        self.speech_bubble_image = self._create_speech_bubble(self.current_message)
        self.bubble_label = tk.Label(self.bubble_frame, image=self.speech_bubble_image, bg=self.cget('bg'))
        self.bubble_label.pack(anchor='n')

    # リサイズハンドル（吹き出しの右下上に表示する）
    # 小さな青い丸をCanvasに描画して使用する
        self.resize_handle = tk.Canvas(self, width=16, height=16, highlightthickness=0, bg=self.cget('bg'), cursor='size_nw_se')
    # 円を描画（内側に少しパディング）
        self._resize_oval_id = self.resize_handle.create_oval(2, 2, 14, 14, fill='blue', outline='')
    # 初期は一時配置（正しい位置は _position_resize_handle で決定する）
        self.resize_handle.place(x=0, y=0)
        self.resize_handle.bind('<Button-1>', self._start_resize)
        self.resize_handle.bind('<B1-Motion>', self._resize_window)
        self.resize_handle.bind('<ButtonRelease-1>', self._stop_resize)
    # マウスホバー時に色を変更する
        self.resize_handle.bind('<Enter>', lambda e: self.resize_handle.itemconfig(self._resize_oval_id, fill='#3399ff'))
        self.resize_handle.bind('<Leave>', lambda e: self.resize_handle.itemconfig(self._resize_oval_id, fill='blue'))
        try:
            self.resize_handle.lift()
        except Exception:
            pass
        # 吹き出し位置にハンドルを移動（layout が安定してから）
        self.after(50, self._position_resize_handle)

    def _update_images_for_size(self, new_width: int, new_height: int):
        """ウィンドウのスケールに合わせてキャラクター画像をリサンプリングし、吹き出しを再生成する。

        基準ウィンドウの高さに対する新しい高さ比を使って一様にスケールすることで、
        画像がウィンドウに対して相対的に同じサイズを保つようにする。
        """
        try:
            if self._char_pil is None:
                return
            # 高さ比に基づく一様スケール
            scale = float(new_height) / max(1, self._base_window_height)
            # 新しいサイズを計算する
            char_w = max(24, int(self._char_base_size[0] * scale))
            char_h = max(24, int(self._char_base_size[1] * scale))
            bubble_w = max(80, int(self._bubble_base_size[0] * scale))
            bubble_h = max(40, int(self._bubble_base_size[1] * scale))

            # キャラクター画像をリサンプリングする
            char_resized = self._char_pil.resize((char_w, char_h), Image.Resampling.LANCZOS)
            self.character_image = ImageTk.PhotoImage(char_resized)
            self.character_label.configure(image=self.character_image)

            # 新しいサイズで吹き出しを再作成する
            self.speech_bubble_image = self._create_speech_bubble(self.current_message, width=bubble_w, height=bubble_h)
            self.bubble_label.configure(image=self.speech_bubble_image)
            # 吹き出しサイズが変わったのでハンドル位置を調整
            self._position_resize_handle()
        except Exception:
            logging.getLogger(__name__).exception('画像更新エラー')

    def _setup_events(self):
        widgets = [self, self.main_frame, self.character_frame, self.character_label, self.bubble_frame, self.bubble_label]
        for widget in widgets:
            widget.bind('<Button-1>', self._on_mouse_click)
            widget.bind('<B1-Motion>', self._on_mouse_drag)
            widget.bind('<ButtonRelease-1>', self._on_mouse_release)
            widget.bind('<Button-3>', self._on_right_click)
        self.bind('<Escape>', self._on_escape)
        self.bind('<Return>', self._on_enter)
        self.focus_set()

    def _on_mouse_click(self, event):
        # start move (unless resizing)
        self.offset_x = self.winfo_pointerx() - self.winfo_rootx()
        self.offset_y = self.winfo_pointery() - self.winfo_rooty()

    def _on_mouse_drag(self, event):
        if self.offset_x is not None and self.offset_y is not None and not getattr(self, 'resizing', False):
            new_x = self.winfo_pointerx() - self.offset_x
            new_y = self.winfo_pointery() - self.offset_y
            self.geometry(f'+{new_x}+{new_y}')

    def _on_mouse_release(self, event):
        self.offset_x = None
        self.offset_y = None

    def _on_right_click(self, event):
        self._show_context_menu(event)

    def _on_escape(self, event):
        self.quit()

    def _on_enter(self, event):
        self._change_message()

    def _show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='メッセージ変更', command=self._change_message)
        menu.add_command(label='定型メッセージ', command=self._show_preset_messages)
        menu.add_separator()
        menu.add_command(label='透明度設定', command=self._change_transparency)
        menu.add_command(label='常に最前面', command=self._toggle_topmost)
        menu.add_separator()
        menu.add_command(label='終了', command=self.quit)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _change_message(self):
        new_message = simpledialog.askstring('メッセージ変更', '新しいメッセージを入力してください:', initialvalue=self.current_message)
        if new_message is not None:
            self.set_message(new_message)

    def _start_resize(self, event):
        self.resizing = True
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.start_width = self.winfo_width()
        self.start_height = self.winfo_height()

    def _resize_window(self, event):
        if getattr(self, 'resizing', False):
            dx = event.x_root - self.start_x
            dy = event.y_root - self.start_y
            new_width = max(self.start_width + dx, 100)
            new_height = max(self.start_height + dy, 60)
            self.geometry(f'{new_width}x{new_height}')
            # update images proportionally
            self._update_images_for_size(new_width, new_height)
            # ハンドル位置を吹き出しに合わせて更新
            self._position_resize_handle()

    def _stop_resize(self, event):
        self.resizing = False

    def _show_preset_messages(self):
        preset_window = tk.Toplevel(self)
        preset_window.title('定型メッセージ')
        preset_window.geometry('300x400')
        preset_window.wm_attributes('-topmost', True)
        presets = [
            'こんにちは！', 'お疲れ様です', '作業中です...', '休憩中', '会議中', '集中モード', '質問があります', '確認お願いします', '完了しました！', 'ありがとうございます'
        ]
        tk.Label(preset_window, text='定型メッセージを選択:', font=('Arial', 12)).pack(pady=10)
        listbox = tk.Listbox(preset_window, height=10)
        listbox.pack(fill='both', expand=True, padx=10, pady=5)
        for p in presets:
            listbox.insert(tk.END, p)
        def select_preset():
            sel = listbox.curselection()
            if sel:
                self.set_message(presets[sel[0]])
                preset_window.destroy()
        tk.Button(preset_window, text='選択', command=select_preset).pack(pady=5)
        tk.Button(preset_window, text='キャンセル', command=preset_window.destroy).pack(pady=5)

    def _change_transparency(self):
        try:
            current_alpha = self.wm_attributes('-alpha')
            new_alpha = simpledialog.askfloat('透明度設定', '透明度を入力してください (0.1-1.0):', initialvalue=current_alpha, minvalue=0.1, maxvalue=1.0)
            if new_alpha is not None:
                self.wm_attributes('-alpha', new_alpha)
        except tk.TclError:
            messagebox.showwarning('警告', '透明度設定はサポートされていません')

    def _toggle_topmost(self):
        current_topmost = self.wm_attributes('-topmost')
        self.wm_attributes('-topmost', not current_topmost)
        status = '有効' if not current_topmost else '無効'
        messagebox.showinfo('設定変更', f'常に最前面表示を{status}にしました')

    def _position_resize_handle(self):
        """吹き出しの右下上にリサイズハンドルを配置する"""
        try:
            self.update_idletasks()
            # bubble_label のスクリーン座標
            bx_root = self.bubble_label.winfo_rootx()
            by_root = self.bubble_label.winfo_rooty()
            b_width = self.bubble_label.winfo_width()
            b_height = self.bubble_label.winfo_height()
            # ウィンドウのスクリーン左上
            win_root_x = self.winfo_rootx()
            win_root_y = self.winfo_rooty()
            # bubble の右下をウィンドウ内部座標に変換
            bubble_right = bx_root - win_root_x + b_width
            bubble_bottom = by_root - win_root_y + b_height

            # ウィジェットの実際の幅・高さを取得
            handle_w = max(1, self.resize_handle.winfo_width())
            handle_h = max(1, self.resize_handle.winfo_height())

            # ハンドルを吹き出し右下の上に配置（少し内側・上寄せ）
            x = max(0, bubble_right - handle_w - 6)
            y = max(0, bubble_bottom - handle_h - 12)
            self.resize_handle.place(x=x, y=y)
            try:
                self.resize_handle.lift()
            except Exception:
                pass
        except Exception:
            # Widget が未配置などで失敗する場合は無視
            pass

    def set_message(self, message):
        self.current_message = message
        self.message_history.append(message)
        self.speech_bubble_image = self._create_speech_bubble(message)
        self.bubble_label.configure(image=self.speech_bubble_image)
        logging.getLogger(__name__).info(f'メッセージを更新: {message}')

    def _poll_predictions_file(self):
        """predictions.txt を定期的にチェックして内容が変わったら吹き出しを更新する"""
        try:
            if os.path.exists(self._pred_file):
                try:
                    with open(self._pred_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    content = None
                if content and content != self._last_pred_content:
                    # 先頭行（要約）を吹き出しメッセージに使う
                    first_line = content.splitlines()[0].strip() if content.splitlines() else content.strip()
                    if first_line:
                        self.set_message(first_line)
                        self._last_pred_content = content
            # 1秒ごとに再チェック
        except Exception:
            logging.getLogger(__name__).exception('predictions ファイルの監視でエラーが発生しました')
        finally:
            try:
                self.after(1000, self._poll_predictions_file)
            except Exception:
                pass

    def get_message(self):
        return self.current_message

    def run(self):
        try:
            self.mainloop()
        except KeyboardInterrupt:
            logging.getLogger(__name__).info('アプリケーションを終了します...')
            self.quit()


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
