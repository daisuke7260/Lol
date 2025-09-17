"""
Configuration file for LOL Winrate System
LOL勝率システムの設定ファイル
"""

import os
from typing import Dict

# Riot Games API設定
RIOT_API_KEY = os.getenv('RIOT_API_KEY', 'RGAPI-your-api-key-here')
RIOT_REGION = os.getenv('RIOT_REGION', 'jp1')

# MySQL データベース設定
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'lol_winrate_db'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True
}

# データ収集設定
DATA_COLLECTION_CONFIG = {
    'matches_per_player': 20,  # プレイヤーあたりの試合数
    'target_matches': 1000,    # 目標試合数
    'queue_types': [420],      # 対象キュー（420=ランク戦ソロ/デュオ）
    'min_game_duration': 600,  # 最小試合時間（秒）
    'max_requests_per_second': 1,  # 秒あたりの最大リクエスト数
    'request_delay': 1.2,      # リクエスト間の遅延（秒）
}

# 機械学習設定
ML_CONFIG = {
    'model_types': ['random_forest'],  # 使用するモデルタイプ
    'test_size': 0.2,          # テストデータの割合
    'random_state': 42,        # 乱数シード
    'cv_folds': 5,             # クロスバリデーションのフォールド数
    'min_samples_for_training': 100,  # 学習に必要な最小サンプル数
}

# ログ設定
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'lol_winrate_system.log',
    'max_bytes': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# 高ランクティア設定
HIGH_RANK_TIERS = ['CHALLENGER', 'GRANDMASTER', 'MASTER']

# レーン設定
VALID_LANES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']

# チャンピオンロール設定
CHAMPION_ROLES = {
    'Assassin': 'アサシン',
    'Fighter': 'ファイター',
    'Mage': 'メイジ',
    'Marksman': 'マークスマン',
    'Support': 'サポート',
    'Tank': 'タンク'
}

