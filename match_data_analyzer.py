"""
Match Data Analyzer for League of Legends
試合データから対面チャンピオン情報を抽出・分析するモジュール
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Lane(Enum):
    """レーン定義"""
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"
    UTILITY = "UTILITY"

@dataclass
class PlayerMatchData:
    """プレイヤーの試合データ"""
    puuid: str
    champion_id: int
    champion_name: str
    champion_level: int
    lane: str
    team_position: str
    team_id: int
    
    # アイテム情報
    items: List[int]  # item0-item6
    gold_earned: int
    gold_spent: int
    
    # 戦績
    kills: int
    deaths: int
    assists: int
    win: bool
    
    # ダメージ情報
    total_damage_dealt_to_champions: int
    total_damage_taken: int
    
    # その他の統計
    vision_score: int
    cs_total: int  # totalMinionsKilled + neutralMinionsKilled
    
    # 試合情報
    game_duration: int
    game_version: str

@dataclass
class MatchupData:
    """対面データ"""
    player1: PlayerMatchData
    player2: PlayerMatchData
    lane: str
    game_duration: int
    game_version: str
    match_id: str
    game_creation: int

class MatchDataAnalyzer:
    """試合データ分析クラス"""
    
    def __init__(self):
        self.champion_data = {}
        self.item_data = {}
    
    def set_static_data(self, champion_data: Dict, item_data: Dict):
        """
        静的データ（チャンピオン・アイテム情報）を設定
        
        Args:
            champion_data: チャンピオンデータ
            item_data: アイテムデータ
        """
        self.champion_data = champion_data
        self.item_data = item_data
    
    def extract_player_data(self, participant: Dict, match_info: Dict) -> PlayerMatchData:
        """
        参加者データからプレイヤー情報を抽出
        
        Args:
            participant: 参加者データ（ParticipantDto）
            match_info: 試合情報（InfoDto）
            
        Returns:
            プレイヤー試合データ
        """
        # アイテム情報を抽出
        items = [
            participant.get('item0', 0),
            participant.get('item1', 0),
            participant.get('item2', 0),
            participant.get('item3', 0),
            participant.get('item4', 0),
            participant.get('item5', 0),
            participant.get('item6', 0)
        ]
        
        # CS計算
        cs_total = (participant.get('totalMinionsKilled', 0) + 
                   participant.get('neutralMinionsKilled', 0))
        
        return PlayerMatchData(
            puuid=participant.get('puuid', ''),
            champion_id=participant.get('championId', 0),
            champion_name=participant.get('championName', ''),
            champion_level=participant.get('champLevel', 0),
            lane=participant.get('lane', ''),
            team_position=participant.get('teamPosition', ''),
            team_id=participant.get('teamId', 0),
            items=items,
            gold_earned=participant.get('goldEarned', 0),
            gold_spent=participant.get('goldSpent', 0),
            kills=participant.get('kills', 0),
            deaths=participant.get('deaths', 0),
            assists=participant.get('assists', 0),
            win=participant.get('win', False),
            total_damage_dealt_to_champions=participant.get('totalDamageDealtToChampions', 0),
            total_damage_taken=participant.get('totalDamageTaken', 0),
            vision_score=participant.get('visionScore', 0),
            cs_total=cs_total,
            game_duration=match_info.get('gameDuration', 0),
            game_version=match_info.get('gameVersion', '')
        )
    
    def find_lane_opponents(self, players: List[PlayerMatchData]) -> List[MatchupData]:
        """
        レーン別の対面チャンピオンを特定
        
        Args:
            players: プレイヤーデータ一覧
            
        Returns:
            対面データ一覧
        """
        matchups = []
        
        # チーム別にプレイヤーを分類
        team1_players = [p for p in players if p.team_id == 100]
        team2_players = [p for p in players if p.team_id == 200]
        
        # レーン別に対面を特定
        for lane in [Lane.TOP.value, Lane.JUNGLE.value, Lane.MIDDLE.value, Lane.BOTTOM.value, Lane.UTILITY.value]:
            team1_lane = [p for p in team1_players if p.team_position == lane]
            team2_lane = [p for p in team2_players if p.team_position == lane]
            
            # 1v1の対面のみを対象とする
            if len(team1_lane) == 1 and len(team2_lane) == 1:
                player1 = team1_lane[0]
                player2 = team2_lane[0]
                
                matchup = MatchupData(
                    player1=player1,
                    player2=player2,
                    lane=lane,
                    game_duration=player1.game_duration,
                    game_version=player1.game_version,
                    match_id="",  # 後で設定
                    game_creation=0  # 後で設定
                )
                matchups.append(matchup)
        
        return matchups
    
    def extract_matchups(self, match_data: Dict) -> List[MatchupData]:
        """
        試合データから対面情報を抽出（analyze_matchのエイリアス）
        
        Args:
            match_data: 試合データ（MatchDto）
            
        Returns:
            対面データ一覧
        """
        return self.analyze_match(match_data)
    
    def analyze_match(self, match_data: Dict) -> List[MatchupData]:
        """
        試合データを分析して対面情報を抽出
        
        Args:
            match_data: 試合データ（MatchDto）
            
        Returns:
            対面データ一覧
        """
        try:
            info = match_data.get('info', {})
            metadata = match_data.get('metadata', {})
            participants = info.get('participants', [])
            
            # プレイヤーデータを抽出
            players = []
            for participant in participants:
                player_data = self.extract_player_data(participant, info)
                players.append(player_data)
            
            # 対面を特定
            matchups = self.find_lane_opponents(players)
            
            # 試合情報を設定
            match_id = metadata.get('matchId', '')
            game_creation = info.get('gameCreation', 0)
            
            for matchup in matchups:
                matchup.match_id = match_id
                matchup.game_creation = game_creation
            
            return matchups
            
        except Exception as e:
            logger.error(f"試合データ分析エラー: {e}")
            return []
    
    def calculate_item_gold_value(self, items: List[int]) -> int:
        """
        アイテムの合計ゴールド価値を計算
        
        Args:
            items: アイテムID一覧
            
        Returns:
            合計ゴールド価値
        """
        total_gold = 0
        
        if not self.item_data:
            logger.warning("アイテムデータが設定されていません")
            return 0
        
        item_dict = self.item_data.get('data', {})
        
        for item_id in items:
            if item_id == 0:  # 空のスロット
                continue
                
            item_str = str(item_id)
            if item_str in item_dict:
                item_info = item_dict[item_str]
                gold_info = item_info.get('gold', {})
                total_value = gold_info.get('total', 0)
                total_gold += total_value
            else:
                logger.debug(f"アイテムID {item_id} が見つかりません")
        
        return total_gold
    
    def calculate_level_advantage(self, player1_level: int, player2_level: int) -> int:
        """
        レベル差を計算
        
        Args:
            player1_level: プレイヤー1のレベル
            player2_level: プレイヤー2のレベル
            
        Returns:
            レベル差（プレイヤー1 - プレイヤー2）
        """
        return player1_level - player2_level
    
    def calculate_gold_advantage(self, player1_items: List[int], player2_items: List[int]) -> int:
        """
        アイテムゴールド差を計算
        
        Args:
            player1_items: プレイヤー1のアイテム
            player2_items: プレイヤー2のアイテム
            
        Returns:
            ゴールド差（プレイヤー1 - プレイヤー2）
        """
        player1_gold = self.calculate_item_gold_value(player1_items)
        player2_gold = self.calculate_item_gold_value(player2_items)
        return player1_gold - player2_gold
    
    def get_matchup_features(self, matchup: MatchupData) -> Dict[str, Any]:
        """
        対面データから機械学習用の特徴量を抽出
        
        Args:
            matchup: 対面データ
            
        Returns:
            特徴量辞書
        """
        player1 = matchup.player1
        player2 = matchup.player2
        
        # 基本特徴量
        features = {
            'champion1_id': player1.champion_id,
            'champion2_id': player2.champion_id,
            'champion1_name': player1.champion_name,
            'champion2_name': player2.champion_name,
            'lane': matchup.lane,
            
            # レベル関連
            'level1': player1.champion_level,
            'level2': player2.champion_level,
            'level_diff': self.calculate_level_advantage(player1.champion_level, player2.champion_level),
            
            # ゴールド関連
            'gold_earned1': player1.gold_earned,
            'gold_earned2': player2.gold_earned,
            'gold_diff': player1.gold_earned - player2.gold_earned,
            
            # アイテム関連
            'item_gold1': self.calculate_item_gold_value(player1.items),
            'item_gold2': self.calculate_item_gold_value(player2.items),
            'item_gold_diff': self.calculate_gold_advantage(player1.items, player2.items),
            
            # 戦績関連
            'kills1': player1.kills,
            'deaths1': player1.deaths,
            'assists1': player1.assists,
            'kills2': player2.kills,
            'deaths2': player2.deaths,
            'assists2': player2.assists,
            'kda_diff': ((player1.kills + player1.assists) / max(player1.deaths, 1)) - 
                       ((player2.kills + player2.assists) / max(player2.deaths, 1)),
            
            # ダメージ関連
            'damage_dealt1': player1.total_damage_dealt_to_champions,
            'damage_dealt2': player2.total_damage_dealt_to_champions,
            'damage_taken1': player1.total_damage_taken,
            'damage_taken2': player2.total_damage_taken,
            
            # CS関連
            'cs1': player1.cs_total,
            'cs2': player2.cs_total,
            'cs_diff': player1.cs_total - player2.cs_total,
            
            # 試合情報
            'game_duration': matchup.game_duration,
            'game_version': matchup.game_version,
            
            # 勝敗（ターゲット変数）
            'player1_win': player1.win,
            'player2_win': player2.win
        }
        
        return features

def main():
    """テスト用のメイン関数"""
    analyzer = MatchDataAnalyzer()
    
    # サンプルデータでテスト
    sample_match = {
        'metadata': {
            'matchId': 'JP1_123456789'
        },
        'info': {
            'gameCreation': 1640995200000,
            'gameDuration': 1800,
            'gameVersion': '13.24.1',
            'participants': [
                {
                    'puuid': 'player1',
                    'championId': 1,
                    'championName': 'Annie',
                    'champLevel': 15,
                    'lane': 'MIDDLE',
                    'teamPosition': 'MIDDLE',
                    'teamId': 100,
                    'item0': 3020, 'item1': 3089, 'item2': 0, 'item3': 0, 'item4': 0, 'item5': 0, 'item6': 3340,
                    'goldEarned': 12000,
                    'goldSpent': 10000,
                    'kills': 5, 'deaths': 2, 'assists': 8,
                    'win': True,
                    'totalDamageDealtToChampions': 25000,
                    'totalDamageTaken': 15000,
                    'visionScore': 20,
                    'totalMinionsKilled': 150,
                    'neutralMinionsKilled': 10
                },
                {
                    'puuid': 'player2',
                    'championId': 103,
                    'championName': 'Ahri',
                    'champLevel': 14,
                    'lane': 'MIDDLE',
                    'teamPosition': 'MIDDLE',
                    'teamId': 200,
                    'item0': 3020, 'item1': 3135, 'item2': 0, 'item3': 0, 'item4': 0, 'item5': 0, 'item6': 3340,
                    'goldEarned': 11000,
                    'goldSpent': 9500,
                    'kills': 3, 'deaths': 5, 'assists': 6,
                    'win': False,
                    'totalDamageDealtToChampions': 22000,
                    'totalDamageTaken': 18000,
                    'visionScore': 18,
                    'totalMinionsKilled': 140,
                    'neutralMinionsKilled': 5
                }
            ]
        }
    }
    
    matchups = analyzer.analyze_match(sample_match)
    print(f"対面数: {len(matchups)}")
    
    if matchups:
        matchup = matchups[0]
        features = analyzer.get_matchup_features(matchup)
        print(f"特徴量: {features}")

if __name__ == "__main__":
    main()

