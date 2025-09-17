"""
Realtime Data Collector for LOL Winrate System
リアルタイム勝率予測システム用の統合データ収集システム
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from riot_api_client import RiotAPIClient
from timeline_analyzer import TimelineAnalyzer, SoloKillEvent
from database_manager_realtime import RealtimeDatabaseManager
from match_data_analyzer import MatchDataAnalyzer

logger = logging.getLogger(__name__)

class RealtimeDataCollector:
    """リアルタイム勝率予測用データ収集システム"""
    
    def __init__(self, api_key: str, mysql_config: Dict, region: str = 'jp1'):
        """
        データ収集システムを初期化
        
        Args:
            api_key: Riot Games APIキー
            mysql_config: MySQL接続設定
            region: リージョン
        """
        self.api_client = RiotAPIClient(api_key, region)
        self.db_manager = RealtimeDatabaseManager(**mysql_config)
        self.timeline_analyzer = TimelineAnalyzer()
        self.match_analyzer = MatchDataAnalyzer()
        
        # 統計情報
        self.stats = {
            'matches_processed': 0,
            'solo_kills_found': 0,
            'matchups_created': 0,
            'timeline_analyzed': 0,
            'failed_requests': 0,
            'start_time': None
        }
        
        logger.info("リアルタイムデータ収集システムを初期化しました")
    
    def setup_static_data(self) -> bool:
        """静的データ（チャンピオン、アイテム、バージョン）をセットアップ"""
        try:
            logger.info("静的データのセットアップを開始...")
            
            # 最新バージョンを取得
            latest_version = self.api_client.get_latest_version()
            if not latest_version:
                logger.error("最新バージョンの取得に失敗")
                return False
            
            # ゲームバージョンを挿入
            if not self.db_manager.insert_game_version(latest_version, is_active=True):
                logger.error("ゲームバージョンの挿入に失敗")
                return False
            
            # チャンピオンデータを取得・挿入
            champion_data = self.api_client.get_champion_data(latest_version)
            if champion_data:
                champions_inserted = 0
                for champion_key, champion_info in champion_data.get('data', {}).items():
                    success = self.db_manager.insert_champion(
                        champion_id=int(champion_info.get('key')),
                        key_name=champion_key,
                        name=champion_info.get('name'),
                        title=champion_info.get('title'),
                        tags=champion_info.get('tags', []),
                        version=latest_version
                    )
                    if success:
                        champions_inserted += 1
                
                logger.info(f"チャンピオンデータを挿入: {champions_inserted}体")
            
            # アイテムデータを取得・挿入
            item_data = self.api_client.get_item_data(latest_version)
            if item_data:
                items_inserted = 0
                for item_id, item_info in item_data.get('data', {}).items():
                    gold_info = item_info.get('gold', {})
                    success = self.db_manager.insert_item(
                        item_id=int(item_id),
                        name=item_info.get('name'),
                        description=item_info.get('description'),
                        gold_base=gold_info.get('base', 0),
                        gold_total=gold_info.get('total', 0),
                        gold_sell=gold_info.get('sell', 0),
                        tags=item_info.get('tags', []),
                        stats=item_info.get('stats', {}),
                        version=latest_version
                    )
                    if success:
                        items_inserted += 1
                
                logger.info(f"アイテムデータを挿入: {items_inserted}個")
            
            logger.info("静的データのセットアップが完了しました")
            return True
            
        except Exception as e:
            logger.error(f"静的データセットアップエラー: {e}")
            return False
    
    def collect_match_with_timeline(self, match_id: str) -> bool:
        """試合データとタイムラインを収集・分析"""
        try:
            logger.info(f"試合データ収集開始: {match_id}")
            
            # 試合データを取得
            match_data = self.api_client.get_match_data(match_id)
            if not match_data:
                logger.warning(f"試合データの取得に失敗: {match_id}")
                self.stats['failed_requests'] += 1
                return False
            
            # タイムラインデータを取得
            timeline_data = self.api_client.get_match_timeline(match_id)
            if not timeline_data:
                logger.warning(f"タイムラインデータの取得に失敗: {match_id}")
                # タイムラインなしでも基本データは保存
                return self._process_match_without_timeline(match_data)
            
            # 試合データを挿入
            if not self.db_manager.insert_match(match_data):
                logger.error(f"試合データの挿入に失敗: {match_id}")
                return False
            
            # 参加者データを挿入
            participants = match_data.get('info', {}).get('participants', [])
            for participant in participants:
                if not self.db_manager.insert_participant(match_id, participant):
                    logger.warning(f"参加者データの挿入に失敗: {participant.get('participantId')}")
            
            # タイムライン分析
            timeline_result = self.timeline_analyzer.analyze_timeline(timeline_data, match_data)
            if not timeline_result:
                logger.warning(f"タイムライン分析に失敗: {match_id}")
                return False
            
            self.stats['timeline_analyzed'] += 1
            
            # 対面データとソロキルを処理
            success = self._process_matchups_and_solo_kills(match_data, timeline_result)
            
            if success:
                self.stats['matches_processed'] += 1
                logger.info(f"試合データ処理完了: {match_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"試合データ収集エラー: {match_id} - {e}")
            self.stats['failed_requests'] += 1
            return False
    
    def _process_match_without_timeline(self, match_data: Dict) -> bool:
        """タイムラインなしで試合データを処理"""
        try:
            match_id = match_data.get('metadata', {}).get('matchId')
            
            # 試合データを挿入
            if not self.db_manager.insert_match(match_data):
                return False
            
            # 参加者データを挿入
            participants = match_data.get('info', {}).get('participants', [])
            for participant in participants:
                self.db_manager.insert_participant(match_id, participant)
            
            # 基本的な対面データを作成（ソロキル情報なし）
            matchups = self.match_analyzer.extract_matchups(match_data)
            for matchup in matchups:
                self.db_manager.insert_matchup(matchup)
                self.stats['matchups_created'] += 1
            
            self.stats['matches_processed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"タイムラインなし試合処理エラー: {e}")
            return False
    
    def _process_matchups_and_solo_kills(self, match_data: Dict, timeline_result: Dict) -> bool:
        """対面データとソロキル情報を処理"""
        try:
            match_id = match_data.get('metadata', {}).get('matchId')
            participants = timeline_result.get('participants', {})
            lane_solo_kills = timeline_result.get('lane_solo_kills', {})
            
            # 対面データを作成
            matchups = self.match_analyzer.extract_matchups(match_data)
            
            for matchup in matchups:
                # MatchupDataオブジェクトを辞書に変換
                if hasattr(matchup, '__dict__'):
                    matchup_dict = self._convert_matchup_to_dict(matchup)
                else:
                    matchup_dict = matchup
                
                lane = matchup_dict.get('lane')
                
                # 対面データを挿入
                matchup_id = self.db_manager.insert_matchup(matchup_dict)
                if not matchup_id:
                    continue
                
                self.stats['matchups_created'] += 1
                
                # このレーンのソロキルを取得
                lane_kills = self.timeline_analyzer.get_matchup_solo_kills(
                    lane_solo_kills, participants, lane
                )
                
                # ソロキルデータを挿入
                for solo_kill in lane_kills:
                    solo_kill_data = self._prepare_solo_kill_data(
                        solo_kill, match_id, matchup_id, participants
                    )
                    
                    solo_kill_id = self.db_manager.insert_solo_kill(solo_kill_data)
                    if solo_kill_id:
                        # キル時アイテム情報を挿入
                        self._insert_kill_items(solo_kill, solo_kill_id)
                        self.stats['solo_kills_found'] += 1
                
                # リアルタイム統計を更新
                self._update_realtime_stats(matchup_dict)
            
            return True
            
        except Exception as e:
            logger.error(f"対面・ソロキル処理エラー: {e}")
            return False
    
    def _convert_matchup_to_dict(self, matchup) -> Dict:
        """MatchupDataオブジェクトを辞書に変換"""
        try:
            if hasattr(matchup, 'player1') and hasattr(matchup, 'player2'):
                # MatchupDataオブジェクトの場合
                player1 = matchup.player1
                player2 = matchup.player2
                
                # BOTレーンの場合、追加プレイヤーを探す
                player3_data = None
                player4_data = None
                
                if matchup.lane == 'BOTTOM':
                    # BOTレーンの場合は2vs2なので、追加のプレイヤーデータが必要
                    # 現在の実装では1vs1のみなので、NULLで設定
                    pass
                
                matchup_dict = {
                    'match_id': matchup.match_id,
                    'lane': matchup.lane,
                    'player1_puuid': player1.puuid,
                    'player1_participant_id': getattr(player1, 'participant_id', 1),
                    'player1_champion_id': player1.champion_id,
                    'player1_champion_name': player1.champion_name,
                    'player1_level': player1.champion_level,
                    'player1_team_id': player1.team_id,
                    'player2_puuid': player2.puuid,
                    'player2_participant_id': getattr(player2, 'participant_id', 2),
                    'player2_champion_id': player2.champion_id,
                    'player2_champion_name': player2.champion_name,
                    'player2_level': player2.champion_level,
                    'player2_team_id': player2.team_id,
                    'player3_puuid': None,
                    'player3_participant_id': None,
                    'player3_champion_id': None,
                    'player3_champion_name': None,
                    'player3_level': None,
                    'player3_team_id': None,
                    'player4_puuid': None,
                    'player4_participant_id': None,
                    'player4_champion_id': None,
                    'player4_champion_name': None,
                    'player4_level': None,
                    'player4_team_id': None,
                    'level_diff': player1.champion_level - player2.champion_level,
                    'gold_diff': player1.gold_earned - player2.gold_earned,
                    'item_gold_diff': self._calculate_item_gold_diff(player1.items, player2.items),
                    'cs_diff': player1.cs_total - player2.cs_total,
                    'kda_diff': self._calculate_kda_diff(player1, player2),
                    'player1_win': player1.win,
                    'player2_win': player2.win,
                    'game_duration': matchup.game_duration,
                    'game_version': matchup.game_version,
                    'game_creation': matchup.game_creation
                }
                
                return matchup_dict
            else:
                # 既に辞書の場合
                return matchup
                
        except Exception as e:
            logger.error(f"MatchupData変換エラー: {e}")
            return {}
    
    def _calculate_item_gold_diff(self, items1: List[int], items2: List[int]) -> int:
        """アイテムのゴールド差を計算"""
        try:
            value1 = self.timeline_analyzer.calculate_item_value(items1)
            value2 = self.timeline_analyzer.calculate_item_value(items2)
            return value1 - value2
        except Exception:
            return 0
    
    def _calculate_kda_diff(self, player1, player2) -> float:
        """KDA差を計算"""
        try:
            kda1 = (player1.kills + player1.assists) / max(player1.deaths, 1)
            kda2 = (player2.kills + player2.assists) / max(player2.deaths, 1)
            return round(kda1 - kda2, 3)
        except Exception:
            return 0.0
    
    def _prepare_solo_kill_data(self, solo_kill: SoloKillEvent, match_id: str, 
                               matchup_id: int, participants: Dict) -> Dict:
        """ソロキルデータを準備"""
        killer_info = participants.get(solo_kill.killer_participant_id, {})
        victim_info = participants.get(solo_kill.victim_participant_id, {})
        
        return {
            'match_id': match_id,
            'matchup_id': matchup_id,
            'timestamp_ms': solo_kill.timestamp_ms,
            'game_time_seconds': solo_kill.game_time_seconds,
            'killer_participant_id': solo_kill.killer_participant_id,
            'killer_champion_id': killer_info.get('champion_id'),
            'killer_champion_name': killer_info.get('champion_name'),
            'killer_level': solo_kill.killer_level,
            'killer_gold': solo_kill.killer_gold,
            'killer_position_x': solo_kill.killer_position[0],
            'killer_position_y': solo_kill.killer_position[1],
            'victim_participant_id': solo_kill.victim_participant_id,
            'victim_champion_id': victim_info.get('champion_id'),
            'victim_champion_name': victim_info.get('champion_name'),
            'victim_level': solo_kill.victim_level,
            'victim_gold': solo_kill.victim_gold,
            'victim_position_x': solo_kill.victim_position[0],
            'victim_position_y': solo_kill.victim_position[1],
            'level_diff': solo_kill.killer_level - solo_kill.victim_level,
            'gold_diff': solo_kill.killer_gold - solo_kill.victim_gold,
            'is_first_blood': solo_kill.is_first_blood,
            'is_shutdown': solo_kill.is_shutdown,
            'bounty_gold': solo_kill.bounty_gold
        }
    
    def _insert_kill_items(self, solo_kill: SoloKillEvent, solo_kill_id: int):
        """キル時アイテム情報を挿入"""
        try:
            # キラーのアイテム
            killer_item_value = self.timeline_analyzer.calculate_item_value(solo_kill.killer_items)
            self.db_manager.insert_kill_items(
                solo_kill_id, solo_kill.killer_participant_id, 'killer',
                solo_kill.killer_items, killer_item_value
            )
            
            # 被害者のアイテム
            victim_item_value = self.timeline_analyzer.calculate_item_value(solo_kill.victim_items)
            self.db_manager.insert_kill_items(
                solo_kill_id, solo_kill.victim_participant_id, 'victim',
                solo_kill.victim_items, victim_item_value
            )
            
        except Exception as e:
            logger.error(f"キル時アイテム挿入エラー: {e}")
    
    def _update_realtime_stats(self, matchup: Dict):
        """リアルタイム統計を更新"""
        try:
            self.db_manager.update_realtime_stats(
                champion1_id=matchup.get('player1_champion_id'),
                champion2_id=matchup.get('player2_champion_id'),
                lane=matchup.get('lane'),
                game_version=matchup.get('game_version')
            )
        except Exception as e:
            logger.error(f"リアルタイム統計更新エラー: {e}")
    
    def collect_player_matches_with_timeline(self, puuid: str, summoner_name: str, 
                                           match_count: int = 20) -> int:
        """プレイヤーの試合データをタイムライン付きで収集"""
        try:
            logger.info(f"プレイヤー試合収集開始: {summoner_name} ({match_count}試合)")
            
            # 試合履歴を取得
            match_ids = self.api_client.get_match_history(
                puuid, count=match_count, queue=420  # ランクソロ
            )
            
            if not match_ids:
                logger.warning(f"試合履歴の取得に失敗: {summoner_name}")
                return 0
            
            collected_count = 0
            for i, match_id in enumerate(match_ids):
                logger.info(f"試合処理中: {i+1}/{len(match_ids)} - {match_id}")
                
                # 既に処理済みかチェック
                if self._is_match_processed(match_id):
                    logger.debug(f"試合は既に処理済み: {match_id}")
                    continue
                
                # 試合データを収集
                if self.collect_match_with_timeline(match_id):
                    collected_count += 1
                
                # レート制限対応
                time.sleep(1.2)
            
            logger.info(f"プレイヤー試合収集完了: {summoner_name} - {collected_count}試合")
            return collected_count
            
        except Exception as e:
            logger.error(f"プレイヤー試合収集エラー: {summoner_name} - {e}")
            return 0
    
    def _is_match_processed(self, match_id: str) -> bool:
        """試合が既に処理済みかチェック"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM matches WHERE match_id = %s", (match_id,))
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def get_high_rank_players(self, tier: str = 'GRANDMASTER', count: int = 50) -> List[Dict]:
        """高ランクプレイヤーを取得"""
        try:
            logger.info(f"{tier}ティアのプレイヤーを取得中...")
            
            if tier == 'CHALLENGER':
                league_data = self.api_client.get_challenger_league()
            elif tier == 'GRANDMASTER':
                league_data = self.api_client.get_grandmaster_league()
            elif tier == 'MASTER':
                league_data = self.api_client.get_master_league()
            else:
                logger.error(f"無効なティア: {tier}")
                return []
            
            if not league_data:
                logger.error(f"{tier}リーグデータの取得に失敗")
                return []
            
            entries = league_data.get('entries', [])[:count]
            logger.info(f"{tier}プレイヤーを取得: {len(entries)}人")
            
            return entries
            
        except Exception as e:
            logger.error(f"高ランクプレイヤー取得エラー: {e}")
            return []
    
    def collect_from_high_rank_players(self, tier: str = 'GRANDMASTER', 
                                     player_count: int = 20, matches_per_player: int = 15) -> Dict:
        """高ランクプレイヤーからデータを収集"""
        try:
            self.stats['start_time'] = datetime.now()
            logger.info(f"高ランクデータ収集開始: {tier} - {player_count}人, {matches_per_player}試合/人")
            
            # 高ランクプレイヤーを取得
            players = self.get_high_rank_players(tier, player_count)
            if not players:
                return self.stats
            
            total_collected = 0
            processed_players = 0
            
            for i, player in enumerate(players):
                summoner_id = player.get('summonerId')
                summoner_name = player.get('summonerName', f'Player_{i+1}')
                
                if not summoner_id:
                    continue
                
                logger.info(f"プレイヤー処理中: {i+1}/{len(players)} - {summoner_name}")
                
                try:
                    # サモナー情報を取得してPUUIDを取得
                    summoner_data = self.api_client.get_summoner_by_id(summoner_id)
                    if not summoner_data:
                        logger.warning(f"サモナー情報の取得に失敗: {summoner_name}")
                        continue
                    
                    puuid = summoner_data.get('puuid')
                    if not puuid:
                        logger.warning(f"PUUIDが見つかりません: {summoner_name}")
                        continue
                    
                    # 試合データを収集
                    collected = self.collect_player_matches_with_timeline(
                        puuid, summoner_name, matches_per_player
                    )
                    
                    total_collected += collected
                    processed_players += 1
                    
                    logger.info(f"プレイヤー完了: {summoner_name} - {collected}試合収集")
                    
                    # プレイヤー間の間隔
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"プレイヤー処理エラー: {summoner_name} - {e}")
                    continue
            
            # 結果をまとめ
            self.stats['end_time'] = datetime.now()
            self.stats['total_players_processed'] = processed_players
            self.stats['total_matches_collected'] = total_collected
            
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            self.stats['duration_seconds'] = duration
            
            logger.info(f"高ランクデータ収集完了: {processed_players}人, {total_collected}試合")
            return self.stats
            
        except Exception as e:
            logger.error(f"高ランクデータ収集エラー: {e}")
            return self.stats
    
    def get_collection_stats(self) -> Dict:
        """収集統計を取得"""
        stats = self.stats.copy()
        
        # データベース統計を追加
        db_stats = self.db_manager.get_database_stats()
        stats.update(db_stats)
        
        return stats

def main():
    """テスト用のメイン関数"""
    import logging
    from config import MYSQL_CONFIG, RIOT_API_KEY, RIOT_REGION
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # データ収集システムを初期化
        collector = RealtimeDataCollector(RIOT_API_KEY, MYSQL_CONFIG, RIOT_REGION)
        
        # 静的データをセットアップ
        if not collector.setup_static_data():
            logger.error("静的データのセットアップに失敗")
            return
        
        # 小規模テスト
        logger.info("小規模テストを開始...")
        results = collector.collect_from_high_rank_players(
            tier='GRANDMASTER',
            player_count=3,
            matches_per_player=5
        )
        
        # 結果を表示
        print("\n=== 収集結果 ===")
        for key, value in results.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        logger.error(f"メイン実行エラー: {e}")

if __name__ == "__main__":
    main()

