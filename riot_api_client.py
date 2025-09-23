"""
Riot Games API Client for League of Legends Data Collection
対面チャンピオン勝率計算システム用のAPIクライアント
"""

import requests
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from config import RIOT_API_KEY

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateLimitInfo:
    """レート制限情報を管理するクラス"""
    requests_per_second: int = 20
    requests_per_two_minutes: int = 100
    last_request_time: float = 0
    request_count_1s: int = 0
    request_count_2m: int = 0
    request_times_2m: List[float] = None
    
    def __post_init__(self):
        if self.request_times_2m is None:
            self.request_times_2m = []

class RiotAPIClient:
    
    def __init__(self, api_key: str, region: str = 'jp1'):
        """
        APIクライアントを初期化
        
        Args:
            api_key: Riot Games API キー
            region: 地域コード (例: 'jp1', 'kr', 'na1')
        """
        self.api_key = api_key
        self.region = region
        self.rate_limit = RateLimitInfo()
        
        # 地域エンドポイントを設定
        self.base_url = self.REGIONAL_ENDPOINTS.get(region, self.REGIONAL_ENDPOINTS['jp1'])
        
        # 地域に応じた大陸エンドポイントを設定
        if region in ['na1', 'br1', 'la1', 'la2']:
            self.continental_region = 'americas'
        elif region in ['kr', 'jp1']:
            self.continental_region = 'asia'
        else:
            self.continental_region = 'europe'
        
        self.continental_url = self.CONTINENTAL_ENDPOINTS.get(self.continental_region)
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Riot-Token': self.api_key,
            'User-Agent': 'LOL-Winrate-Calculator/1.0'
        })
    
    def get_league_entries_by_tier_division(self, tier: str, division: str, queue: str = 'RANKED_SOLO_5x5', page: int = 1) -> Optional[List[Dict]]:
        """
        指定したtier/divisionのリーグエントリー一覧を取得
        Args:
            tier: ティア（例: 'GOLD', 'SILVER', 'BRONZE', ...）
            division: ディビジョン（'I', 'II', 'III', 'IV'）
            queue: キューの種類（デフォルト: RANKED_SOLO_5x5）
            page: ページ番号（デフォルト: 1）
        Returns:
            プレイヤー情報リスト
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/league/v4/entries/{queue}/{tier}/{division}"
        params = {'page': page}
        return self._make_request(url, params)
    """Riot Games API クライアント"""
    
    # 地域別エンドポイント
    REGIONAL_ENDPOINTS = {
        'na1': 'https://na1.api.riotgames.com',
        'euw1': 'https://euw1.api.riotgames.com',
        'eun1': 'https://eun1.api.riotgames.com',
        'kr': 'https://kr.api.riotgames.com',
        'jp1': 'https://jp1.api.riotgames.com',
        'br1': 'https://br1.api.riotgames.com',
        'la1': 'https://la1.api.riotgames.com',
        'la2': 'https://la2.api.riotgames.com',
        'oc1': 'https://oc1.api.riotgames.com',
        'tr1': 'https://tr1.api.riotgames.com',
        'ru': 'https://ru.api.riotgames.com'
    }
    
    # 大陸別エンドポイント（アカウント情報用）
    CONTINENTAL_ENDPOINTS = {
        'americas': 'https://americas.api.riotgames.com',
        'asia': 'https://asia.api.riotgames.com',
        'europe': 'https://europe.api.riotgames.com'
    }
    
    def _wait_for_rate_limit(self):
        """レート制限に従って待機"""
        current_time = time.time()
        
        # 2分間のリクエスト履歴をクリーンアップ
        self.rate_limit.request_times_2m = [
            t for t in self.rate_limit.request_times_2m 
            if current_time - t < 120
        ]
        
        # 1秒間のレート制限チェック
        if current_time - self.rate_limit.last_request_time < 1:
            if self.rate_limit.request_count_1s >= self.rate_limit.requests_per_second:
                wait_time = 1 - (current_time - self.rate_limit.last_request_time)
                logger.info(f"レート制限により {wait_time:.2f}秒待機中...")
                time.sleep(wait_time)
                self.rate_limit.request_count_1s = 0
        else:
            self.rate_limit.request_count_1s = 0
        
        # 2分間のレート制限チェック
        if len(self.rate_limit.request_times_2m) >= self.rate_limit.requests_per_two_minutes:
            oldest_request = min(self.rate_limit.request_times_2m)
            wait_time = 120 - (current_time - oldest_request)
            if wait_time > 0:
                logger.info(f"レート制限により {wait_time:.2f}秒待機中...")
                time.sleep(wait_time)
        
        # リクエスト記録を更新
        self.rate_limit.last_request_time = current_time
        self.rate_limit.request_count_1s += 1
        self.rate_limit.request_times_2m.append(current_time)
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        APIリクエストを実行
        
        Args:
            url: リクエストURL
            params: クエリパラメータ
            
        Returns:
            APIレスポンス（JSON）
        """
        self._wait_for_rate_limit()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # レート制限エラー
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"レート制限に達しました。{retry_after}秒後にリトライします。")
                time.sleep(retry_after)
                return self._make_request(url, params)
            elif response.status_code == 404:
                logger.warning(f"データが見つかりません: {url}")
                return None
            else:
                logger.error(f"APIエラー: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"リクエストエラー: {e}")
            return None
    
    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> Optional[Dict]:
        """
        Riot IDからアカウント情報を取得
        
        Args:
            game_name: ゲーム名
            tag_line: タグライン
            
        Returns:
            アカウント情報
        """
        base_url = self.CONTINENTAL_ENDPOINTS[self.continental_region]
        url = f"{base_url}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return self._make_request(url)
    
    def get_summoner_by_puuid(self, puuid: str) -> Optional[Dict]:
        """
        PUUIDからサモナー情報を取得
        
        Args:
            puuid: プレイヤーのPUUID
            
        Returns:
            サモナー情報
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._make_request(url)
    
    def get_match_ids_by_puuid(self, puuid: str, start: int = 0, count: int = 20, 
                              queue: Optional[int] = None, type_filter: Optional[str] = None,
                              start_time: Optional[int] = None, end_time: Optional[int] = None) -> Optional[List[str]]:
        """
        PUUIDから試合ID一覧を取得
        
        Args:
            puuid: プレイヤーのPUUID
            start: 開始インデックス
            count: 取得件数（最大100）
            queue: キューID（例: 420=ランクソロ, 440=ランクフレックス）
            type_filter: 試合タイプフィルター
            start_time: 開始時刻（Unix timestamp）
            end_time: 終了時刻（Unix timestamp）
            
        Returns:
            試合ID一覧
        """
        base_url = self.CONTINENTAL_ENDPOINTS[self.continental_region]
        url = f"{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        
        params = {
            'start': start,
            'count': min(count, 100)  # 最大100件
        }
        
        if queue:
            params['queue'] = queue
        if type_filter:
            params['type'] = type_filter
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._make_request(url, params)
    
    def get_match_by_id(self, match_id: str) -> Optional[Dict]:
        """
        試合IDから試合詳細データを取得
        
        Args:
            match_id: 試合ID
            
        Returns:
            試合詳細データ
        """
        base_url = self.CONTINENTAL_ENDPOINTS[self.continental_region]
        url = f"{base_url}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)
    
    def get_match_data(self, match_id: str) -> Optional[Dict]:
        """
        試合IDから試合詳細データを取得（get_match_by_idのエイリアス）
        
        Args:
            match_id: 試合ID
            
        Returns:
            試合詳細データ
        """
        return self.get_match_by_id(match_id)
    
    def get_match_history(self, puuid: str, start: int = 0, count: int = 20, 
                         queue: Optional[int] = None, type_filter: Optional[str] = None,
                         start_time: Optional[int] = None, end_time: Optional[int] = None) -> Optional[List[str]]:
        """
        PUUIDから試合履歴を取得（get_match_ids_by_puuidのエイリアス）
        
        Args:
            puuid: プレイヤーのPUUID
            start: 開始インデックス
            count: 取得件数（最大100）
            queue: キューID（例: 420=ランクソロ, 440=ランクフレックス）
            type_filter: 試合タイプフィルター
            start_time: 開始時刻（Unix timestamp）
            end_time: 終了時刻（Unix timestamp）
            
        Returns:
            試合ID一覧
        """
        return self.get_match_ids_by_puuid(puuid, start, count, queue, type_filter, start_time, end_time)
    
    def get_match_timeline(self, match_id: str) -> Optional[Dict]:
        """
        試合IDからタイムライン詳細を取得
        
        Args:
            match_id: 試合ID
            
        Returns:
            タイムライン詳細データ
        """
        base_url = self.CONTINENTAL_ENDPOINTS[self.continental_region]
        url = f"{base_url}/lol/match/v5/matches/{match_id}/timeline"
        return self._make_request(url)
    
    def get_champion_data(self, version: str = "13.24.1") -> Optional[Dict]:
        """
        チャンピオンデータを取得（Data Dragon API）
        
        Args:
            version: ゲームバージョン
            
        Returns:
            チャンピオンデータ
        """
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/champion.json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"チャンピオンデータ取得エラー: {response.status_code}")
            return None
    
    def get_item_data(self, version: str = "13.24.1") -> Optional[Dict]:
        """
        アイテムデータを取得（Data Dragon API）
        
        Args:
            version: ゲームバージョン
            
        Returns:
            アイテムデータ
        """
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/ja_JP/item.json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"アイテムデータ取得エラー: {response.status_code}")
            return None
    
    def get_latest_version(self) -> Optional[str]:
        """
        最新のゲームバージョンを取得
        
        Returns:
            最新バージョン文字列
        """
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            versions = response.json()
            return versions[0] if versions else None
        else:
            logger.error(f"バージョン情報取得エラー: {response.status_code}")
            return None
    
    def get_summoner_by_id(self, summoner_id: str) -> Optional[Dict]:
        """
        サモナーIDでサモナー情報を取得
        
        Args:
            summoner_id: サモナーID
            
        Returns:
            サモナー情報
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/summoner/v4/summoners/{summoner_id}"
        return self._make_request(url)
    
    def get_summoner_by_name(self, summoner_name: str) -> Optional[Dict]:
        """
        サモナー名でサモナー情報を取得
        
        Args:
            summoner_name: サモナー名
            
        Returns:
            サモナー情報
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/summoner/v4/summoners/by-name/{summoner_name}"
        return self._make_request(url)

    def get_summoner_rank_tier(self, summoner_id: str) -> Optional[str]:
        """
        指定された（暗号化された）サモナーIDのランクティア（簡略名）を取得。
        ソロランク（RANKED_SOLO_5x5）を優先的に返します。

        Returns:
            例: 'SILVER', 'GOLD', 'PLATINUM' など。取得できない場合は None を返す。
        """
        if not summoner_id:
            return None
        entries = self.get_league_entries_by_summoner(summoner_id)
        if not entries:
            return None
        print("★★")

        # ソロランクを優先して探す
        solo_entry = None
        for e in entries:
            if e.get('queueType') == 'RANKED_SOLO_5x5':
                solo_entry = e
                break

        entry = solo_entry or entries[0]
        tier = entry.get('tier')
        return tier.upper() if tier else None

    def get_match_average_tier_by_match_id(self, match_data: Dict) -> Optional[str]:
        """
        試合IDから参加者のランクを Riot API で取得し、平均的なティアを返す。

        戻り値は簡略ティア名（例: 'SILVER', 'GOLD'）のみ。数値は返しません。
        実装は以下の流れ:
          1. match の詳細を取得
          2. 各 participant の暗号化された summonerId が無ければ puuid から取得
          3. 各サモナーのソロランクティアを取得
          4. ティアを順序にマップして平均を計算し、最も近いティア名を返す

        注意: 参加者ごとに追加の API 呼び出しが発生するため、実行は遅くなる可能性があります。
        """
        participants = match_data.get('info', {}).get('participants', [])
        if not participants:
            return None
        tier_order = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
        tier_to_value = {t: i+1 for i, t in enumerate(tier_order)}

        values = []
        for p in participants:
            summoner_id = p.get('summonerId')
            if not summoner_id:
                puuid = p.get('puuid')
                if puuid:
                    summoner = self.get_summoner_by_puuid(puuid)
                    if summoner:
                        summoner_id = summoner.get('id')
            if not summoner_id:
                continue
            tier = self.get_summoner_rank_tier(summoner_id)
            if tier and tier in tier_to_value:
                values.append(tier_to_value[tier])

        if not values:
            return None

        avg = sum(values) / len(values)
        # 最も近い整数に丸めて対応するティアを返す
        rounded = int(round(avg))
        # clamp
        rounded = max(1, min(rounded, len(tier_order)))
        return tier_order[rounded-1]
    
    def get_challenger_league(self, queue: str = 'RANKED_SOLO_5x5') -> Optional[Dict]:
        """
        チャレンジャーリーグ情報を取得
        
        Args:
            queue: キューの種類
            
        Returns:
            チャレンジャーリーグ情報
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/league/v4/challengerleagues/by-queue/{queue}"
        return self._make_request(url)
    
    def get_grandmaster_league(self, queue: str = 'RANKED_SOLO_5x5') -> Optional[Dict]:
        """
        グランドマスターリーグ情報を取得
        
        Args:
            queue: キューの種類
            
        Returns:
            グランドマスターリーグ情報
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/league/v4/grandmasterleagues/by-queue/{queue}"
        return self._make_request(url)
    
    def get_master_league(self, queue: str = 'RANKED_SOLO_5x5') -> Optional[Dict]:
        """
        マスターリーグ情報を取得
        
        Args:
            queue: キューの種類
            
        Returns:
            マスターリーグ情報
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/league/v4/masterleagues/by-queue/{queue}"
        return self._make_request(url)
    
    def get_league_entries_by_summoner(self, summoner_id: str) -> Optional[List[Dict]]:
        """
        サモナーのリーグエントリー情報を取得
        
        Args:
            summoner_id: サモナーID
            
        Returns:
            リーグエントリー情報のリスト
        """
        base_url = self.REGIONAL_ENDPOINTS[self.region]
        url = f"{base_url}/lol/league/v4/entries/by-summoner/{summoner_id}"
        return self._make_request(url)

def main():
    """テスト用のメイン関数"""
    # APIキーは `config.py` の `RIOT_API_KEY` を使う
    api_key = RIOT_API_KEY if 'RIOT_API_KEY' in globals() else None

    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("APIキーを設定してください")
        return
    
    client = RiotAPIClient(api_key, region='jp1')
    
    # 最新バージョン取得テスト
    version = client.get_latest_version()
    print(f"最新バージョン: {version}")
    
    # チャンピオンデータ取得テスト
    champion_data = client.get_champion_data(version)
    if champion_data:
        print(f"チャンピオン数: {len(champion_data['data'])}")
    
    # アイテムデータ取得テスト
    item_data = client.get_item_data(version)
    if item_data:
        print(f"アイテム数: {len(item_data['data'])}")

if __name__ == "__main__":
    main()

