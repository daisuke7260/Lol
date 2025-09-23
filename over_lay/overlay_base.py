#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本的なオーバーレイウィンドウクラス
他のアプリケーションの上に常に表示されるウィンドウを作成
"""

import tkinter as tk
from tkinter import ttk
import sys


class OverlayWindow(tk.Tk):
    """
    オーバーレイウィンドウの基底クラス
    常に最前面表示、ドラッグ移動、ボーダーレス機能を提供
    """
    
    def __init__(self, width=300, height=200, x=100, y=100):
        super().__init__()
        
        # ウィンドウサイズと位置
        self.window_width = width
        self.window_height = height
        self.window_x = x
        self.window_y = y
        
        # ドラッグ移動用の変数
        self.offset_x = None
        self.offset_y = None
        
        # ウィンドウの初期設定
        self._setup_window()
        self._setup_events()
    
    def _setup_window(self):
        """ウィンドウの基本設定を行う"""
        # ウィンドウタイトル
        self.title("Overlay Window")
        
        # ウィンドウサイズと位置を設定
        geometry = f"{self.window_width}x{self.window_height}+{self.window_x}+{self.window_y}"
        self.geometry(geometry)
        
        # 常に最前面に表示
        self.wm_attributes("-topmost", True)
        
        # ウィンドウボーダーを削除（リサイズ防止）
        self.overrideredirect(True)
        
        # フォーカスを強制取得
        self.focus_force()
        
        # 背景色を設定
        self.configure(bg='lightblue')
        
        # プラットフォーム固有の設定
        self._setup_platform_specific()
    
    def _setup_platform_specific(self):
        """プラットフォーム固有の設定"""
        try:
            # Windowsの場合の透明化設定（オプション）
            if sys.platform.startswith('win'):
                # 特定の色を透明にする場合（後で使用）
                # self.wm_attributes("-transparentcolor", "white")
                pass
            elif sys.platform.startswith('darwin'):
                # macOSの場合
                # self.wm_attributes("-transparent", True)
                pass
        except tk.TclError:
            # 透明化がサポートされていない場合は無視
            pass
    
    def _setup_events(self):
        """イベントハンドラーを設定"""
        # マウスイベントをバインド
        self.bind("<Button-1>", self._on_mouse_click)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_release)
        
        # 右クリックメニュー用
        self.bind("<Button-3>", self._on_right_click)
        
        # キーボードイベント
        self.bind("<Escape>", self._on_escape)
        self.focus_set()  # キーボードフォーカスを設定
    
    def _on_mouse_click(self, event):
        """マウスクリック時の処理"""
        # マウス位置とウィンドウ位置のオフセットを計算
        self.offset_x = self.winfo_pointerx() - self.winfo_rootx()
        self.offset_y = self.winfo_pointery() - self.winfo_rooty()
    
    def _on_mouse_drag(self, event):
        """マウスドラッグ時の処理"""
        if self.offset_x is not None and self.offset_y is not None:
            # 新しいウィンドウ位置を計算
            new_x = self.winfo_pointerx() - self.offset_x
            new_y = self.winfo_pointery() - self.offset_y
            
            # ウィンドウを移動
            self.geometry(f"+{new_x}+{new_y}")
    
    def _on_mouse_release(self, event):
        """マウスリリース時の処理"""
        # オフセットをリセット
        self.offset_x = None
        self.offset_y = None
    
    def _on_right_click(self, event):
        """右クリック時の処理"""
        # 右クリックメニューを表示
        self._show_context_menu(event)
    
    def _on_escape(self, event):
        """Escapeキー押下時の処理"""
        self.quit()
    
    def _show_context_menu(self, event):
        """コンテキストメニューを表示"""
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="設定", command=self._show_settings)
        context_menu.add_separator()
        context_menu.add_command(label="終了", command=self.quit)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _show_settings(self):
        """設定ダイアログを表示（プレースホルダー）"""
        print("設定ダイアログ（未実装）")
    
    def set_transparency(self, alpha=0.8):
        """ウィンドウの透明度を設定"""
        try:
            self.wm_attributes("-alpha", alpha)
        except tk.TclError:
            print("透明度設定はサポートされていません")
    
    def set_always_on_top(self, on_top=True):
        """常に最前面表示の設定を変更"""
        self.wm_attributes("-topmost", on_top)
    
    def run(self):
        """アプリケーションを実行"""
        try:
            self.mainloop()
        except KeyboardInterrupt:
            print("\nアプリケーションを終了します...")
            self.quit()


def main():
    """メイン関数 - テスト用"""
    # 基本的なオーバーレイウィンドウを作成
    overlay = OverlayWindow(width=400, height=300, x=200, y=150)
    
    # テスト用のラベルを追加
    test_label = tk.Label(
        overlay,
        text="オーバーレイウィンドウ\n\nドラッグで移動\n右クリックでメニュー\nEscで終了",
        bg='lightblue',
        fg='darkblue',
        font=('Arial', 12),
        justify='center'
    )
    test_label.pack(expand=True)
    
    # 透明度を設定
    overlay.set_transparency(0.9)
    
    print("オーバーレイウィンドウを起動しました")
    print("- ドラッグで移動できます")
    print("- 右クリックでコンテキストメニュー")
    print("- Escキーで終了")
    
    # アプリケーションを実行
    overlay.run()


if __name__ == "__main__":
    main()
