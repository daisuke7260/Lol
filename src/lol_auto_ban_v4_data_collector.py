#!/usr/bin/env python3
"""
LOL Auto BAN Tool V4 - Data Collector Module
"""

import requests
import json
import time

class DataCollector:
    """データ収集クラス"""
    
    def __init__(self):
        self.last_update = 0
        self.cache = {}
    
    def get_live_client_data(self):
        """ライブクライアントデータ取得"""
        try:
            response = requests.get('https://127.0.0.1:2999/liveclientdata/allgamedata', 
                                  timeout=2, verify=False)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_champion_data(self, champion_name):
        """チャンピオンデータ取得"""
        # キャッシュチェック
        if champion_name in self.cache:
            return self.cache[champion_name]
        
        # ダミーデータ
        data = {
            'name': champion_name,
            'winrate': 50.0,
            'pickrate': 10.0,
            'banrate': 5.0
        }
        
        self.cache[champion_name] = data
        return data
