#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
オーバーレイアプリケーション実行スクリプト
使用するバージョンを選択して実行
"""

import sys
import os
import subprocess

def check_dependencies():
    """依存関係をチェック"""
    try:
        import tkinter
        print("✓ tkinter: OK")
    except ImportError:
        print("✗ tkinter: 見つかりません")
        print("  インストール: sudo apt install python3-tk")
        return False
    
    try:
        from PIL import Image, ImageTk, ImageDraw, ImageFont
        print("✓ Pillow: OK")
    except ImportError:
        print("✗ Pillow: 見つかりません")
        print("  インストール: pip install Pillow")
        return False
    
    return True

def show_menu():
    """メニューを表示"""
    print("\n" + "="*50)
    print("  キャラクターオーバーレイアプリケーション")
    print("="*50)
    print()
    print("実行するバージョンを選択してください:")
    print()
    print("1. 基本版 (overlay_base.py)")
    print("   - シンプルなオーバーレイウィンドウ")
    print("   - ドラッグ移動、右クリックメニュー")
    print()
    print("2. キャラクター版 (character_overlay.py)")
    print("   - キャラクターと吹き出し表示")
    print("   - メッセージ変更機能")
    print()
    print("3. 高機能版 (advanced_character_overlay.py) ★推奨")
    print("   - 全機能搭載")
    print("   - カスタマイズ、設定保存、アニメーション")
    print()
    print("4. 依存関係チェック")
    print("5. 終了")
    print()

def run_application(choice):
    """選択されたアプリケーションを実行"""
    scripts = {
        '1': 'overlay_base.py',
        '2': 'character_overlay.py',
        '3': 'advanced_character_overlay.py'
    }
    
    if choice in scripts:
        script_path = scripts[choice]
        if os.path.exists(script_path):
            print(f"\n{script_path} を実行中...")
            print("終了するには Escape キーを押してください。")
            print("-" * 40)
            try:
                subprocess.run([sys.executable, script_path])
            except KeyboardInterrupt:
                print("\nアプリケーションを終了しました。")
        else:
            print(f"エラー: {script_path} が見つかりません。")
    elif choice == '4':
        print("\n依存関係をチェック中...")
        if check_dependencies():
            print("\n✓ すべての依存関係が満たされています。")
        else:
            print("\n✗ 依存関係に問題があります。上記の指示に従ってインストールしてください。")
    elif choice == '5':
        print("終了します。")
        sys.exit(0)
    else:
        print("無効な選択です。1-5の数字を入力してください。")

def main():
    """メイン関数"""
    print("キャラクターオーバーレイアプリケーション起動スクリプト")
    
    # 初回依存関係チェック
    if not check_dependencies():
        print("\n依存関係に問題があります。")
        print("必要なライブラリをインストールしてから再実行してください。")
        return
    
    while True:
        show_menu()
        try:
            choice = input("選択 (1-5): ").strip()
            run_application(choice)
            
            if choice != '5':
                input("\nEnterキーを押してメニューに戻る...")
        except KeyboardInterrupt:
            print("\n\n終了します。")
            break
        except EOFError:
            print("\n\n終了します。")
            break

if __name__ == "__main__":
    main()
