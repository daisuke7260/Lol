#!/usr/bin/env python3
"""
LOL Auto BAN Tool V4 - Main Application
完全動作版
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback
import json
import logging

# パスの設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, current_dir)

def setup_logging():
    """ログ設定"""
    log_dir = os.path.join(current_dir, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'v4_main.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def check_required_files():
    """必要ファイルの存在確認"""
    required_files = [
        'src/lol_auto_ban_v4_integrated.py',
        'src/lol_auto_ban_v4_gui.py',
        'data/champions_data.json',
        'config/v4_config.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"[ERROR] 必要なファイルが見つかりません:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        print(f"[INFO] EXTRACT_ALL.batを実行して完全展開を行ってください")
        return False
    
    return True

def import_modules():
    """モジュールのインポート"""
    try:
        print("[INFO] モジュールをインポート中...")
        
        # V4統合システムのインポート
        from lol_auto_ban_v4_integrated import LOLAutoBanV4System
        print("[SUCCESS] V4統合システムをインポートしました")

        # V3統合システムのインポート
        from lol_auto_ban_v3_core import LOLAutoBanV3Core
        print("[SUCCESS] V3統合システムをインポートしました")

        # GUIモジュールのインポート
        from lol_auto_ban_v4_gui import LOLV4GUI
        print("[SUCCESS] GUIモジュールをインポートしました")
        
        print("[SUCCESS] オーバーレイモジュールをインポートしました")
        return LOLAutoBanV4System, LOLAutoBanV3Core, LOLV4GUI

    except ImportError as e:
        print(f"[ERROR] モジュールインポートエラー: {e}")
        print(f"[INFO] 詳細エラー情報:")
        traceback.print_exc()
        return None, None
    except Exception as e:
        print(f"[ERROR] 予期しないエラー: {e}")
        traceback.print_exc()
        return None, None

def load_config():
    """設定ファイルの読み込み"""
    config_path = os.path.join(current_dir, 'config', 'v4_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("[SUCCESS] 設定ファイルを読み込みました")
        return config
    except Exception as e:
        print(f"[ERROR] 設定ファイル読み込みエラー: {e}")
        # デフォルト設定を返す
        return {
            "version": "4.0.0",
            "v3_settings": {
                "auto_accept_enabled": False,
                "auto_ban_enabled": False,
                "auto_pick_enabled": False,
                "ban_champion": "Yasuo"
            },
            "v4_settings": {
                "winrate_analysis_enabled": True,
                "monitoring_interval": 3,
                "overlay_enabled": True
            }
        }

def run_gui_mode():
    """GUIモードで実行"""
    print("[INFO] GUIモードで起動中...")
    
    # 必要ファイルチェック
    if not check_required_files():
        input("Enterキーを押して終了...")
        return False
    
    # モジュールインポート
    LOLAutoBanV4System, LOLAutoBanV3Core, LOLV4GUI = import_modules()
    if not LOLAutoBanV4System or not LOLAutoBanV4System or not LOLV4GUI:
        print("[ERROR] 必要なモジュールをインポートできませんでした")
        input("Enterキーを押して終了...")
        return False
    
    # 設定読み込み
    config = load_config()
    
    try:
        # V4システム初期化
        print("[INFO] V4システムを初期化中...")
        v4_system = LOLAutoBanV4System(config)

        print("[INFO] V3システムを初期化中...")
        v3_system = LOLAutoBanV3Core()

        # GUI初期化
        print("[INFO] GUIを初期化中...")
        root = tk.Tk()
        app = LOLV4GUI(root, v4_system, v3_system)

        print("[SUCCESS] LOL Auto BAN Tool V4 が正常に起動しました")
        print("[INFO] GUIウィンドウが表示されます...")
        
        # GUI実行
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] アプリケーション実行エラー: {e}")
        traceback.print_exc()
        
        # エラーダイアログ表示
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "LOL Auto BAN Tool V4 - エラー",
                f"アプリケーションの起動に失敗しました:\n\n{str(e)}\n\ndiagnostic.batを実行して詳細を確認してください。"
            )
        except:
            pass
        
        return False

def run_cli_mode():
    """CLIモードで実行"""
    print("[INFO] CLIモードで起動中...")
    
    # 必要ファイルチェック
    if not check_required_files():
        return False
    
    # モジュールインポート
    LOLAutoBanV4System, _ = import_modules()
    if not LOLAutoBanV4System:
        print("[ERROR] 必要なモジュールをインポートできませんでした")
        return False
    
    # 設定読み込み
    config = load_config()
    
    try:
        # V4システム初期化
        print("[INFO] V4システムを初期化中...")
        v4_system = LOLAutoBanV4System(config)
        
        print("[SUCCESS] LOL Auto BAN Tool V4 (CLI) が正常に起動しました")
        print("[INFO] CLIモードで実行中...")
        print("[INFO] Ctrl+C で終了")
        
        # CLI実行ループ
        v4_system.start_monitoring()
        
        # 無限ループ（Ctrl+Cで終了）
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] ユーザーによって終了されました")
            v4_system.stop_monitoring()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] CLIモード実行エラー: {e}")
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("========================================")
    print("LOL Auto BAN Tool V4 - 完全動作版")
    print("========================================")
    print()
    
    # ログ設定
    setup_logging()
    logging.info("LOL Auto BAN Tool V4 起動開始")
    
    # 現在のディレクトリ情報
    print(f"[INFO] 現在のディレクトリ: {current_dir}")
    print(f"[INFO] Pythonバージョン: {sys.version}")
    
    # コマンドライン引数チェック
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        success = run_cli_mode()
    else:
        success = run_gui_mode()
    
    if success:
        print("[INFO] アプリケーションが正常に終了しました")
        logging.info("LOL Auto BAN Tool V4 正常終了")
    else:
        print("[ERROR] アプリケーションがエラーで終了しました")
        logging.error("LOL Auto BAN Tool V4 エラー終了")
        input("Enterキーを押して終了...")

if __name__ == "__main__":
    main()
