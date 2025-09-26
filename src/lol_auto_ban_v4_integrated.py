#!/usr/bin/env python3
"""
LOL Auto BAN Tool V4 - 統合システム
完全動作版
"""

import os
import sys
import json
import time
import threading
import logging
from datetime import datetime
import requests

class LOLAutoBanV4System:
    """LOL Auto BAN Tool V4 統合システム"""
    
    def __init__(self, config):
        """初期化"""
        self.config = config
        self.is_monitoring = False
        self.monitoring_thread = None
        self.current_game_data = None
        self.winrate_predictions = {}
        
        # ログ設定
        self.logger = logging.getLogger(__name__)
        
        # データディレクトリ
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # チャンピオンデータ読み込み
        self.load_champion_data()
        
        print("[INFO] LOL Auto BAN Tool V4 システム初期化完了")
    
    def load_champion_data(self):
        """チャンピオンデータの読み込み"""
        try:
            champions_file = os.path.join(self.data_dir, 'champions_data.json')
            with open(champions_file, 'r', encoding='utf-8') as f:
                self.champions_data = json.load(f)
            print(f"[SUCCESS] チャンピオンデータを読み込みました ({len(self.champions_data)} チャンピオン)")
        except Exception as e:
            print(f"[WARNING] チャンピオンデータ読み込みエラー: {e}")
            self.champions_data = {}
    
    def start_monitoring(self):
        """監視開始"""
        if self.is_monitoring:
            print("[WARNING] 既に監視中です")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("[INFO] ゲーム監視を開始しました")
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("[INFO] ゲーム監視を停止しました")
    
    def _monitoring_loop(self):
        """監視ループ"""
        while self.is_monitoring:
            try:
                # ゲームデータ取得
                game_data = self.get_live_game_data()
                if game_data:
                    self.current_game_data = game_data
                    
                    # 勝率予測
                    predictions = self.calculate_winrate_predictions(game_data)
                    self.winrate_predictions = predictions
                    
                    # ログ出力
                    if predictions:
                        for team, winrate in predictions.items():
                            print(f"[PREDICTION] {team}: {winrate:.1f}% 勝率")
                
                # 監視間隔
                interval = self.config.get('v4_settings', {}).get('monitoring_interval', 3)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"監視ループエラー: {e}")
                time.sleep(5)
    
    def get_live_game_data(self):
        print("ライブゲームデータ取得")
        try:
            # League of Legends Live Client Data API
            response = requests.get('https://127.0.0.1:2999/liveclientdata/allgamedata', 
                                  timeout=2, verify=False)
            print(response.json())
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def calculate_winrate_predictions(self, game_data):
        """勝率予測計算"""
        try:
            if not game_data or 'allPlayers' not in game_data:
                return {}
            
            # 簡単な勝率計算（実際のV4では機械学習を使用）
            blue_team_strength = 0
            red_team_strength = 0
            
            for player in game_data['allPlayers']:
                champion_name = player.get('championName', '')
                team = player.get('team', '')
                level = player.get('level', 1)
                
                # チャンピオン強度（簡易版）
                champion_strength = self.get_champion_strength(champion_name, level)
                
                if team == 'ORDER':  # Blue team
                    blue_team_strength += champion_strength
                else:  # Red team
                    red_team_strength += champion_strength
            
            # 勝率計算
            total_strength = blue_team_strength + red_team_strength
            if total_strength > 0:
                blue_winrate = (blue_team_strength / total_strength) * 100
                red_winrate = (red_team_strength / total_strength) * 100
                
                return {
                    'blue_team': blue_winrate,
                    'red_team': red_winrate
                }
        
        except Exception as e:
            self.logger.error(f"勝率予測計算エラー: {e}")
        
        return {}
    
    def get_champion_strength(self, champion_name, level):
        """チャンピオン強度取得"""
        # 簡易的な強度計算
        base_strength = 50
        level_bonus = level * 2
        
        # チャンピオン固有ボーナス（簡易版）
        champion_bonus = 0
        if champion_name in ['Yasuo', 'Zed', 'Katarina']:
            champion_bonus = 10
        elif champion_name in ['Garen', 'Malphite', 'Amumu']:
            champion_bonus = 5
        
        return base_strength + level_bonus + champion_bonus
    
    def get_ban_recommendations(self):
        """BAN推奨チャンピオン取得"""
        # 簡易的なBAN推奨
        high_threat_champions = ['Yasuo', 'Zed', 'Katarina', 'Vayne', 'Darius']
        return high_threat_champions[:3]
    
    def get_current_predictions(self):
        """現在の予測取得"""
        return self.winrate_predictions
    
    def get_game_status(self):
        """ゲーム状態取得"""
        if self.current_game_data:
            return {
                'in_game': True,
                'game_time': self.current_game_data.get('gameData', {}).get('gameTime', 0),
                'players_count': len(self.current_game_data.get('allPlayers', []))
            }
        return {'in_game': False}
