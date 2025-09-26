"""
Database Manager for LOL Realtime Winrate System
リアルタイム勝率予測システム用のMySQLデータベース管理クラス
"""

import mysql.connector
from mysql.connector import Error
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class RealtimeDatabaseManager:
    def get_1v1_matchup_features(self, limit: int = 10000) -> List[Dict]:
        """
        1vs1対面勝率予測用の特徴量データを取得
        - 自分と対面のアイテム（item0～item6）
        - レベル（player1_level, player2_level）
        - アイテムゴールド総量（item_gold1, item_gold2）
        Args:
            limit: 取得件数上限
        Returns:
            特徴量データのリスト（辞書）
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                query = f'''
                SELECT
                    m.id AS matchup_id,
                    m.player1_champion_id,
                    m.player2_champion_id,
                    m.player1_level,
                    m.player2_level,
                    m.player1_champion_name,
                    m.player2_champion_name,
                    m.lane,
                    m.game_version,
                    p1.item0 AS p1_item0, p1.item1 AS p1_item1, p1.item2 AS p1_item2, p1.item3 AS p1_item3, p1.item4 AS p1_item4, p1.item5 AS p1_item5, p1.item6 AS p1_item6,
                    p2.item0 AS p2_item0, p2.item1 AS p2_item1, p2.item2 AS p2_item2, p2.item3 AS p2_item3, p2.item4 AS p2_item4, p2.item5 AS p2_item5, p2.item6 AS p2_item6,
                    p1.champion_level AS p1_level,
                    p2.champion_level AS p2_level,
                    p1.gold_earned AS p1_gold_earned,
                    p2.gold_earned AS p2_gold_earned
                FROM matchups m
                JOIN participants p1 ON m.match_id = p1.match_id AND m.player1_participant_id = p1.participant_id
                JOIN participants p2 ON m.match_id = p2.match_id AND m.player2_participant_id = p2.participant_id
                LIMIT %s
                '''
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                logger.info(f"1v1特徴量データ取得: {len(results)}件")
                return results
        except Exception as e:
            logger.error(f"1v1特徴量データ取得エラー: {e}")
            return []
    """リアルタイム勝率予測用データベース管理クラス"""
    
    def __init__(self, **mysql_config):
        """
        データベース管理クラスを初期化
        
        Args:
            **mysql_config: MySQL接続設定
        """
        self.config = mysql_config
        self.connection_pool = None
        self._init_connection_pool()
        
        logger.info("リアルタイムデータベース管理クラスを初期化しました")
    
    def _init_connection_pool(self):
        """コネクションプールを初期化"""
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="realtime_pool",
                pool_size=10,
                pool_reset_session=True,
                **self.config
            )
            logger.info("データベースコネクションプールを初期化しました")
        except Error as e:
            logger.error(f"コネクションプール初期化エラー: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """コネクションを取得（コンテキストマネージャー）"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"データベース接続エラー: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def insert_game_version(self, version: str, release_date: str = None, is_active: bool = True) -> bool:
        """ゲームバージョンを挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT IGNORE INTO game_versions (version, release_date, is_active)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                release_date = VALUES(release_date),
                is_active = VALUES(is_active)
                """
                
                cursor.execute(query, (version, release_date, is_active))
                conn.commit()
                
                logger.info(f"ゲームバージョンを挿入: {version}")
                return True
                
        except Error as e:
            logger.error(f"ゲームバージョン挿入エラー: {e}")
            return False
    
    def insert_champion(self, champion_id: int, key_name: str, name: str, 
                       title: str = None, tags: List[str] = None, version: str = None) -> bool:
        """チャンピオン情報を挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT INTO champions (id, key_name, name, title, tags, version)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                key_name = VALUES(key_name),
                name = VALUES(name),
                title = VALUES(title),
                tags = VALUES(tags),
                version = VALUES(version)
                """
                
                tags_json = json.dumps(tags) if tags else None
                cursor.execute(query, (champion_id, key_name, name, title, tags_json, version))
                conn.commit()
                
                logger.debug(f"チャンピオン情報を挿入: {name} (ID: {champion_id})")
                return True
                
        except Error as e:
            logger.error(f"チャンピオン挿入エラー: {e}")
            return False
    
    def insert_item(self, item_id: int, name: str, description: str = None,
                   gold_base: int = 0, gold_total: int = 0, gold_sell: int = 0,
                   tags: List[str] = None, stats: Dict = None, version: str = None) -> bool:
        """アイテム情報を挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT INTO items (id, name, description, gold_base, gold_total, gold_sell, tags, stats, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                description = VALUES(description),
                gold_base = VALUES(gold_base),
                gold_total = VALUES(gold_total),
                gold_sell = VALUES(gold_sell),
                tags = VALUES(tags),
                stats = VALUES(stats),
                version = VALUES(version)
                """
                
                tags_json = json.dumps(tags) if tags else None
                stats_json = json.dumps(stats) if stats else None
                
                cursor.execute(query, (item_id, name, description, gold_base, gold_total, 
                                     gold_sell, tags_json, stats_json, version))
                conn.commit()
                
                logger.debug(f"アイテム情報を挿入: {name} (ID: {item_id})")
                return True
                
        except Error as e:
            logger.error(f"アイテム挿入エラー: {e}")
            return False
    
    def insert_match(self, match_data: Dict, tier: int) -> bool:
        game_version = match_data.get('info', {}).get('gameVersion')
        self.insert_game_version(game_version)
        """試合情報を挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                info = match_data.get('info', {})
                match_id = match_data.get('metadata', {}).get('matchId')
                
                query = """
                INSERT INTO matches (
                    match_id, game_creation, game_duration, game_end_timestamp,
                    game_mode, game_type, game_version, map_id, platform_id,
                    queue_id, tournament_code, has_timeline, tier
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                game_duration = VALUES(game_duration),
                has_timeline = VALUES(has_timeline)
                """
                
                values = (
                    match_id,
                    info.get('gameCreation', 0),
                    info.get('gameDuration', 0),
                    info.get('gameEndTimestamp', 0),
                    info.get('gameMode'),
                    info.get('gameType'),
                    info.get('gameVersion'),
                    info.get('mapId'),
                    info.get('platformId'),
                    info.get('queueId'),
                    info.get('tournamentCode'),
                    0,  # has_timeline は後で更新
                    tier,
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                logger.debug(f"試合情報を挿入: {match_id}")
                return True
                
        except Error as e:
            logger.error(f"試合挿入エラー: {e}")
            return False
    
    def insert_participant(self, match_id: str, participant_data: Dict) -> bool:
        """参加者情報を挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT INTO participants (
                    match_id, puuid, participant_id, champion_id, champion_name,
                    champion_level, lane, team_position, team_id,
                    item0, item1, item2, item3, item4, item5, item6,
                    gold_earned, gold_spent, kills, deaths, assists, win,
                    total_damage_dealt, total_damage_dealt_to_champions, total_damage_taken,
                    magic_damage_dealt, physical_damage_dealt, true_damage_dealt,
                    total_minions_killed, neutral_minions_killed,
                    vision_score, wards_placed, wards_killed,
                    largest_killing_spree, largest_multi_kill, longest_time_spent_living
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                champion_level = VALUES(champion_level),
                gold_earned = VALUES(gold_earned),
                kills = VALUES(kills),
                deaths = VALUES(deaths),
                assists = VALUES(assists)
                """
                
                values = (
                    match_id,
                    participant_data.get('puuid'),
                    participant_data.get('participantId'),
                    participant_data.get('championId'),
                    participant_data.get('championName'),
                    participant_data.get('champLevel', 1),
                    participant_data.get('lane'),
                    participant_data.get('teamPosition'),
                    participant_data.get('teamId'),
                    participant_data.get('item0', 0),
                    participant_data.get('item1', 0),
                    participant_data.get('item2', 0),
                    participant_data.get('item3', 0),
                    participant_data.get('item4', 0),
                    participant_data.get('item5', 0),
                    participant_data.get('item6', 0),
                    participant_data.get('goldEarned', 0),
                    participant_data.get('goldSpent', 0),
                    participant_data.get('kills', 0),
                    participant_data.get('deaths', 0),
                    participant_data.get('assists', 0),
                    participant_data.get('win', False),
                    participant_data.get('totalDamageDealt', 0),
                    participant_data.get('totalDamageDealtToChampions', 0),
                    participant_data.get('totalDamageTaken', 0),
                    participant_data.get('magicDamageDealt', 0),
                    participant_data.get('physicalDamageDealt', 0),
                    participant_data.get('trueDamageDealt', 0),
                    participant_data.get('totalMinionsKilled', 0),
                    participant_data.get('neutralMinionsKilled', 0),
                    participant_data.get('visionScore', 0),
                    participant_data.get('wardsPlaced', 0),
                    participant_data.get('wardsKilled', 0),
                    participant_data.get('largestKillingSpree', 0),
                    participant_data.get('largestMultiKill', 0),
                    participant_data.get('longestTimeSpentLiving', 0)
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                logger.debug(f"参加者情報を挿入: {participant_data.get('championName')} (ID: {participant_data.get('participantId')})")
                return True
                
        except Error as e:
            logger.error(f"参加者挿入エラー: {e}")
            return False
    
    def insert_matchup(self, matchup_data: Dict) -> Optional[int]:
        """対面データを挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT INTO matchups (
                    match_id, lane,
                    player1_puuid, player1_participant_id, player1_champion_id, player1_champion_name,
                    player1_level, player1_team_id,
                    player2_puuid, player2_participant_id, player2_champion_id, player2_champion_name,
                    player2_level, player2_team_id,
                    player3_puuid, player3_participant_id, player3_champion_id, player3_champion_name,
                    player3_level, player3_team_id,
                    player4_puuid, player4_participant_id, player4_champion_id, player4_champion_name,
                    player4_level, player4_team_id,
                    level_diff, gold_diff, item_gold_diff, cs_diff, kda_diff,
                    player1_win, player2_win, game_duration, game_version, game_creation
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    matchup_data.get('match_id'),
                    matchup_data.get('lane'),
                    matchup_data.get('player1_puuid'),
                    matchup_data.get('player1_participant_id'),
                    matchup_data.get('player1_champion_id'),
                    matchup_data.get('player1_champion_name'),
                    matchup_data.get('player1_level'),
                    matchup_data.get('player1_team_id'),
                    matchup_data.get('player2_puuid'),
                    matchup_data.get('player2_participant_id'),
                    matchup_data.get('player2_champion_id'),
                    matchup_data.get('player2_champion_name'),
                    matchup_data.get('player2_level'),
                    matchup_data.get('player2_team_id'),
                    matchup_data.get('player3_puuid'),
                    matchup_data.get('player3_participant_id'),
                    matchup_data.get('player3_champion_id'),
                    matchup_data.get('player3_champion_name'),
                    matchup_data.get('player3_level'),
                    matchup_data.get('player3_team_id'),
                    matchup_data.get('player4_puuid'),
                    matchup_data.get('player4_participant_id'),
                    matchup_data.get('player4_champion_id'),
                    matchup_data.get('player4_champion_name'),
                    matchup_data.get('player4_level'),
                    matchup_data.get('player4_team_id'),
                    matchup_data.get('level_diff'),
                    matchup_data.get('gold_diff'),
                    matchup_data.get('item_gold_diff'),
                    matchup_data.get('cs_diff'),
                    matchup_data.get('kda_diff'),
                    matchup_data.get('player1_win'),
                    matchup_data.get('player2_win'),
                    matchup_data.get('game_duration'),
                    matchup_data.get('game_version'),
                    matchup_data.get('game_creation')
                )
                
                cursor.execute(query, values)
                matchup_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"対面データを挿入: {matchup_data.get('lane')} (ID: {matchup_id})")
                return matchup_id
                
        except Error as e:
            logger.error(f"対面データ挿入エラー: {e}")
            return None
    
    def insert_solo_kill(self, solo_kill_data: Dict) -> Optional[int]:
        """ソロキル情報を挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT INTO solo_kills (
                    match_id, matchup_id, timestamp_ms, game_time_seconds,
                    killer_participant_id, killer_champion_id, killer_champion_name,
                    killer_level, killer_gold, killer_position_x, killer_position_y,
                    victim_participant_id, victim_champion_id, victim_champion_name,
                    victim_level, victim_gold, victim_position_x, victim_position_y,
                    level_diff, gold_diff, is_first_blood, is_shutdown, bounty_gold
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                values = (
                    solo_kill_data.get('match_id'),
                    solo_kill_data.get('matchup_id'),
                    solo_kill_data.get('timestamp_ms'),
                    solo_kill_data.get('game_time_seconds'),
                    solo_kill_data.get('killer_participant_id'),
                    solo_kill_data.get('killer_champion_id'),
                    solo_kill_data.get('killer_champion_name'),
                    solo_kill_data.get('killer_level'),
                    solo_kill_data.get('killer_gold'),
                    solo_kill_data.get('killer_position_x'),
                    solo_kill_data.get('killer_position_y'),
                    solo_kill_data.get('victim_participant_id'),
                    solo_kill_data.get('victim_champion_id'),
                    solo_kill_data.get('victim_champion_name'),
                    solo_kill_data.get('victim_level'),
                    solo_kill_data.get('victim_gold'),
                    solo_kill_data.get('victim_position_x'),
                    solo_kill_data.get('victim_position_y'),
                    solo_kill_data.get('level_diff'),
                    solo_kill_data.get('gold_diff'),
                    solo_kill_data.get('is_first_blood'),
                    solo_kill_data.get('is_shutdown'),
                    solo_kill_data.get('bounty_gold')
                )
                
                cursor.execute(query, values)
                solo_kill_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"ソロキル情報を挿入: ID {solo_kill_id}")
                return solo_kill_id
                
        except Error as e:
            logger.error(f"ソロキル挿入エラー: {e}")
            return None
    
    def insert_kill_items(self, solo_kill_id: int, participant_id: int, 
                         participant_type: str, items: List[int], total_value: int = 0) -> bool:
        """キル時アイテム情報を挿入"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                INSERT INTO kill_items (
                    solo_kill_id, participant_id, participant_type,
                    item0, item1, item2, item3, item4, item5, item6, total_item_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # アイテムリストを7個に調整
                items_padded = (items + [0] * 7)[:7]
                
                values = (
                    solo_kill_id, participant_id, participant_type,
                    *items_padded, total_value
                )
                
                cursor.execute(query, values)
                conn.commit()
                
                logger.debug(f"キル時アイテム情報を挿入: ソロキルID {solo_kill_id}, 参加者 {participant_id}")
                return True
                
        except Error as e:
            logger.error(f"キル時アイテム挿入エラー: {e}")
            return False
    
    def update_realtime_stats(self, champion1_id: int, champion2_id: int, 
                            lane: str, game_version: str) -> bool:
        """リアルタイム統計を更新"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 統計を再計算
                stats_query = """
                SELECT 
                    COUNT(*) as total_matchups,
                    SUM(CASE WHEN player1_win = 1 THEN 1 ELSE 0 END) as champion1_wins,
                    SUM(CASE WHEN player2_win = 1 THEN 1 ELSE 0 END) as champion2_wins,
                    COALESCE(SUM(total_solo_kills), 0) as total_solo_kills,
                    AVG(CASE WHEN first_blood_time > 0 THEN first_blood_time ELSE NULL END) as avg_first_kill_time
                FROM matchups 
                WHERE (player1_champion_id = %s AND player2_champion_id = %s)
                   OR (player1_champion_id = %s AND player2_champion_id = %s)
                   AND lane = %s AND game_version = %s
                """
                
                cursor.execute(stats_query, (champion1_id, champion2_id, champion2_id, champion1_id, lane, game_version))
                stats = cursor.fetchone()
                
                if stats and stats[0] > 0:
                    total_matchups, champion1_wins, champion2_wins, total_solo_kills, avg_first_kill_time = stats
                    
                    champion1_winrate = (champion1_wins / total_matchups) * 100
                    champion2_winrate = (champion2_wins / total_matchups) * 100
                    
                    # 統計を更新
                    update_query = """
                    INSERT INTO realtime_winrate_stats (
                        champion1_id, champion2_id, lane, game_version,
                        total_matchups, champion1_wins, champion2_wins,
                        champion1_winrate, champion2_winrate, total_solo_kills,
                        avg_first_kill_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        total_matchups = VALUES(total_matchups),
                        champion1_wins = VALUES(champion1_wins),
                        champion2_wins = VALUES(champion2_wins),
                        champion1_winrate = VALUES(champion1_winrate),
                        champion2_winrate = VALUES(champion2_winrate),
                        total_solo_kills = VALUES(total_solo_kills),
                        avg_first_kill_time = VALUES(avg_first_kill_time)
                    """
                    
                    cursor.execute(update_query, (
                        champion1_id, champion2_id, lane, game_version,
                        total_matchups, champion1_wins, champion2_wins,
                        champion1_winrate, champion2_winrate, total_solo_kills,
                        avg_first_kill_time or 0
                    ))
                    
                    conn.commit()
                    logger.debug(f"リアルタイム統計を更新: {champion1_id} vs {champion2_id} ({lane})")
                    return True
                
                return False
                
        except Error as e:
            logger.error(f"リアルタイム統計更新エラー: {e}")
            return False
    
    def get_realtime_winrate(self, champion1_id: int, champion2_id: int, 
                           lane: str, game_version: str = None) -> Optional[Dict]:
        """リアルタイム勝率を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                query = """
                SELECT * FROM realtime_winrate_stats
                WHERE ((champion1_id = %s AND champion2_id = %s) 
                       OR (champion1_id = %s AND champion2_id = %s))
                  AND lane = %s
                """
                params = [champion1_id, champion2_id, champion2_id, champion1_id, lane]
                
                if game_version:
                    query += " AND game_version = %s"
                    params.append(game_version)
                
                query += " ORDER BY last_updated DESC LIMIT 1"
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    logger.debug(f"リアルタイム勝率を取得: {champion1_id} vs {champion2_id}")
                    return dict(result)
                
                return None
                
        except Error as e:
            logger.error(f"リアルタイム勝率取得エラー: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, int]:
        """データベース統計を取得"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 各テーブルの件数を取得
                tables = [
                    'game_versions', 'champions', 'items', 'matches', 
                    'participants', 'matchups', 'solo_kills', 'kill_items',
                    'timeline_events', 'realtime_winrate_stats', 'ml_models'
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[f"{table}_count"] = count
                
                logger.info("データベース統計を取得しました")
                return stats
                
        except Error as e:
            logger.error(f"データベース統計取得エラー: {e}")
            return {}

    def select_training_data(self, limit: int = 1, mychampion: int = None, enemyChampion: int = None, debug: bool = False) -> list:

        """学習用データを取得する。

        Args:
            limit: 取得上限

        Returns:
            list[dict]: 結果の行のリスト。空の場合は空リストを返します。
        """
        try:
            with self.get_connection() as conn:
                # 辞書形式で結果を受け取る
                cursor = conn.cursor(dictionary=True)
                query = """
                SELECT
                    P1_solo_kills                       AS P1_solo_kills           ,
                    P1_match_id                         AS P1_match_id             ,
                    P1_killer_champion_id               AS P1_killer_champion_id   ,
                    P1_killer_champion_name             AS P1_killer_champion_name ,
                    COALESCE(P1_ITEM0.gold_total, 0) +
                    COALESCE(P1_ITEM1.gold_total, 0) +
                    COALESCE(P1_ITEM2.gold_total, 0) +
                    COALESCE(P1_ITEM3.gold_total, 0) +
                    COALESCE(P1_ITEM4.gold_total, 0) +
                    COALESCE(P1_ITEM5.gold_total, 0) +
                    COALESCE(P1_ITEM6.gold_total, 0)    AS P1_total_gold_value     ,
                    P2_victim_champion_id               AS P2_victim_champion_id   ,
                    P2_victim_champion_name             AS P2_victim_champion_name ,
                    COALESCE(P2_ITEM0.gold_total, 0) +
                    COALESCE(P2_ITEM1.gold_total, 0) +
                    COALESCE(P2_ITEM2.gold_total, 0) +
                    COALESCE(P2_ITEM3.gold_total, 0) +
                    COALESCE(P2_ITEM4.gold_total, 0) +
                    COALESCE(P2_ITEM5.gold_total, 0) +
                    COALESCE(P2_ITEM6.gold_total, 0)    AS P2_total_gold_value     ,
                    CASE P1_participant_type
                        WHEN 'killer' THEN
                            'P1'
                        ELSE
                            'P2'
                    END                                 AS Win_Judgment            ,
                    P1_killer_level                     AS P1_killer_level         ,
                    P1_item0                            AS P1_item0                ,
                    P1_ITEM0.name                       AS P1_ITEM0_name           ,
                    P1_item1                            AS P1_item1                ,
                    P1_ITEM1.name                       AS P1_ITEM1_name           ,
                    P1_item2                            AS P1_item2                ,
                    P1_ITEM2.name                       AS P1_ITEM2_name           ,
                    P1_item3                            AS P1_item3                ,
                    P1_ITEM3.name                       AS P1_ITEM3_name           ,
                    P1_item4                            AS P1_item4                ,
                    P1_ITEM4.name                       AS P1_ITEM4_name           ,
                    P1_item5                            AS P1_item5                ,
                    P1_ITEM5.name                       AS P1_ITEM5_name           ,
                    P1_item6                            AS P1_item6                ,
                    P1_ITEM6.name                       AS P1_ITEM6_name           ,
                    P2_killer_level                     AS P2_killer_level         ,
                    P2_item0                            AS P2_item0                ,
                    P2_ITEM0.name                       AS P2_ITEM0_name           ,
                    P2_item1                            AS P2_item1                ,
                    P2_ITEM1.name                       AS P2_ITEM1_name           ,
                    P2_item2                            AS P2_item2                ,
                    P2_ITEM2.name                       AS P2_ITEM2_name           ,
                    P2_item3                            AS P2_item3                ,
                    P2_ITEM3.name                       AS P2_ITEM3_name           ,
                    P2_item4                            AS P2_item4                ,
                    P2_ITEM4.name                       AS P2_ITEM4_name           ,
                    P2_item5                            AS P2_item5                ,
                    P2_ITEM5.name                       AS P2_ITEM5_name           ,
                    P2_item6                            AS P2_item6                ,
                    P2_ITEM6.name                       AS P2_ITEM6_name           ,
                    matches.game_version                AS matches_game_version
                FROM(
                (
                SELECT *
                FROM (
                    SELECT
                    ki.id                     AS P1_id                     ,
                    ki.solo_kill_id           AS P1_solo_kill_id           ,
                    ki.participant_id         AS P1_participant_id         ,
                    ki.participant_type       AS P1_participant_type       ,
                    ki.ITEM0                  AS P1_item0                  ,
                    ki.ITEM1                  AS P1_item1                  ,
                    ki.ITEM2                  AS P1_item2                  ,
                    ki.ITEM3                  AS P1_item3                  ,
                    ki.ITEM4                  AS P1_item4                  ,
                    ki.ITEM5                  AS P1_item5                  ,
                    ki.ITEM6                  AS P1_item6                  ,
                    ki.total_item_value       AS P1_total_item_value       ,
                    ki.created_at             AS P1_kill_created_at        ,
                    sk.id                     AS P1_solo_kills             ,
                    sk.match_id               AS P1_match_id               ,
                    sk.matchup_id             AS P1_matchup_id             ,
                    sk.timestamp_ms           AS P1_timestamp_ms           ,
                    sk.game_time_seconds      AS P1_game_time_seconds      ,
                    sk.killer_participant_id  AS P1_killer_participant_id  ,
                    sk.killer_champion_id     AS P1_killer_champion_id     ,
                    sk.killer_champion_name   AS P1_killer_champion_name   ,
                    sk.killer_level           AS P1_killer_level           ,
                    sk.killer_gold            AS P1_killer_gold            ,
                    sk.killer_position_x      AS P1_killer_position_x      ,
                    sk.killer_position_y      AS P1_killer_position_y      ,
                    sk.victim_participant_id  AS P1_victim_participant_id  ,
                    sk.victim_champion_id     AS P1_victim_champion_id     ,
                    sk.victim_champion_name   AS P1_victim_champion_name   ,
                    sk.victim_level           AS P1_victim_level           ,
                    sk.victim_gold            AS P1_victim_gold            ,
                    sk.victim_position_x      AS P1_victim_position_x      ,
                    sk.victim_position_y      AS P1_victim_position_y      ,
                    sk.level_diff             AS P1_level_diff             ,
                    sk.gold_diff              AS P1_gold_diff              ,
                    sk.is_first_blood         AS P1_is_first_blood         ,
                    sk.is_shutdown            AS P1_is_shutdown            ,
                    sk.bounty_gold            AS P1_bounty_gold            ,
                    sk.created_at             AS P1_solo_created_at        
                    FROM solo_kills AS sk
                    INNER JOIN kill_items AS ki ON ki.solo_kill_id = sk.id
                    WHERE sk.killer_champion_id < sk.victim_champion_id
                      AND ki.id = (
                          SELECT MIN(id)
                          FROM kill_items
                          WHERE solo_kill_id = ki.solo_kill_id
                      )
                ) AS P1
                INNER JOIN (
                    SELECT
                    ki.id                     AS P2_id                     ,
                    ki.solo_kill_id           AS P2_solo_kill_id           ,
                    ki.participant_id         AS P2_participant_id         ,
                    ki.participant_type       AS P2_participant_type       ,
                    ki.ITEM0                  AS P2_item0                  ,
                    ki.ITEM1                  AS P2_item1                  ,
                    ki.ITEM2                  AS P2_item2                  ,
                    ki.ITEM3                  AS P2_item3                  ,
                    ki.ITEM4                  AS P2_item4                  ,
                    ki.ITEM5                  AS P2_item5                  ,
                    ki.ITEM6                  AS P2_item6                  ,
                    ki.total_item_value       AS P2_total_item_value       ,
                    ki.created_at             AS P2_kill_created_at        ,
                    sk.id                     AS P2_solo_kills             ,
                    sk.match_id               AS P2_match_id               ,
                    sk.matchup_id             AS P2_matchup_id             ,
                    sk.timestamp_ms           AS P2_timestamp_ms           ,
                    sk.game_time_seconds      AS P2_game_time_seconds      ,
                    sk.killer_participant_id  AS P2_killer_participant_id  ,
                    sk.killer_champion_id     AS P2_killer_champion_id     ,
                    sk.killer_champion_name   AS P2_killer_champion_name   ,
                    sk.killer_level           AS P2_killer_level           ,
                    sk.killer_gold            AS P2_killer_gold            ,
                    sk.killer_position_x      AS P2_killer_position_x      ,
                    sk.killer_position_y      AS P2_killer_position_y      ,
                    sk.victim_participant_id  AS P2_victim_participant_id  ,
                    sk.victim_champion_id     AS P2_victim_champion_id     ,
                    sk.victim_champion_name   AS P2_victim_champion_name   ,
                    sk.victim_level           AS P2_victim_level           ,
                    sk.victim_gold            AS P2_victim_gold            ,
                    sk.victim_position_x      AS P2_victim_position_x      ,
                    sk.victim_position_y      AS P2_victim_position_y      ,
                    sk.level_diff             AS P2_level_diff             ,
                    sk.gold_diff              AS P2_gold_diff              ,
                    sk.is_first_blood         AS P2_is_first_blood         ,
                    sk.is_shutdown            AS P2_is_shutdown            ,
                    sk.bounty_gold            AS P2_bounty_gold            ,
                    sk.created_at             AS P2_solo_created_at        
                    FROM solo_kills AS sk
                    INNER JOIN kill_items AS ki ON ki.solo_kill_id = sk.id
                    WHERE sk.killer_champion_id < sk.victim_champion_id
                      AND ki.id = (
                          SELECT MAX(id)
                          FROM kill_items
                          WHERE solo_kill_id = ki.solo_kill_id
                      )
                ) AS P2
                ON P1.P1_solo_kill_id = P2.P2_solo_kill_id
                )
                UNION ALL
                (
                SELECT *
                FROM (
                    SELECT
                    ki.id                     AS P1_id                     ,
                    ki.solo_kill_id           AS P1_solo_kill_id           ,
                    ki.participant_id         AS P1_participant_id         ,
                    ki.participant_type       AS P1_participant_type       ,
                    ki.ITEM0                  AS P1_item0                  ,
                    ki.ITEM1                  AS P1_item1                  ,
                    ki.ITEM2                  AS P1_item2                  ,
                    ki.ITEM3                  AS P1_item3                  ,
                    ki.ITEM4                  AS P1_item4                  ,
                    ki.ITEM5                  AS P1_item5                  ,
                    ki.ITEM6                  AS P1_item6                  ,
                    ki.total_item_value       AS P1_total_item_value       ,
                    ki.created_at             AS P1_kill_created_at        ,
                    sk.id                     AS P1_solo_kills             ,
                    sk.match_id               AS P1_match_id               ,
                    sk.matchup_id             AS P1_matchup_id             ,
                    sk.timestamp_ms           AS P1_timestamp_ms           ,
                    sk.game_time_seconds      AS P1_game_time_seconds      ,
                    sk.killer_participant_id  AS P1_killer_participant_id  ,
                    sk.killer_champion_id     AS P1_killer_champion_id     ,
                    sk.killer_champion_name   AS P1_killer_champion_name   ,
                    sk.killer_level           AS P1_killer_level           ,
                    sk.killer_gold            AS P1_killer_gold            ,
                    sk.killer_position_x      AS P1_killer_position_x      ,
                    sk.killer_position_y      AS P1_killer_position_y      ,
                    sk.victim_participant_id  AS P1_victim_participant_id  ,
                    sk.victim_champion_id     AS P1_victim_champion_id     ,
                    sk.victim_champion_name   AS P1_victim_champion_name   ,
                    sk.victim_level           AS P1_victim_level           ,
                    sk.victim_gold            AS P1_victim_gold            ,
                    sk.victim_position_x      AS P1_victim_position_x      ,
                    sk.victim_position_y      AS P1_victim_position_y      ,
                    sk.level_diff             AS P1_level_diff             ,
                    sk.gold_diff              AS P1_gold_diff              ,
                    sk.is_first_blood         AS P1_is_first_blood         ,
                    sk.is_shutdown            AS P1_is_shutdown            ,
                    sk.bounty_gold            AS P1_bounty_gold            ,
                    sk.created_at             AS P1_solo_created_at        
                    FROM solo_kills AS sk
                    INNER JOIN kill_items AS ki ON ki.solo_kill_id = sk.id
                    WHERE sk.killer_champion_id > sk.victim_champion_id
                      AND ki.id = (
                          SELECT MAX(id)
                          FROM kill_items
                          WHERE solo_kill_id = ki.solo_kill_id
                      )
                ) AS P1
                INNER JOIN (
                    SELECT
                    ki.id                     AS P2_id                     ,
                    ki.solo_kill_id           AS P2_solo_kill_id           ,
                    ki.participant_id         AS P2_participant_id         ,
                    ki.participant_type       AS P2_participant_type       ,
                    ki.ITEM0                  AS P2_item0                  ,
                    ki.ITEM1                  AS P2_item1                  ,
                    ki.ITEM2                  AS P2_item2                  ,
                    ki.ITEM3                  AS P2_item3                  ,
                    ki.ITEM4                  AS P2_item4                  ,
                    ki.ITEM5                  AS P2_item5                  ,
                    ki.ITEM6                  AS P2_item6                  ,
                    ki.total_item_value       AS P2_total_item_value       ,
                    ki.created_at             AS P2_kill_created_at        ,
                    sk.id                     AS P2_solo_kills             ,
                    sk.match_id               AS P2_match_id               ,
                    sk.matchup_id             AS P2_matchup_id             ,
                    sk.timestamp_ms           AS P2_timestamp_ms           ,
                    sk.game_time_seconds      AS P2_game_time_seconds      ,
                    sk.killer_participant_id  AS P2_killer_participant_id  ,
                    sk.killer_champion_id     AS P2_killer_champion_id     ,
                    sk.killer_champion_name   AS P2_killer_champion_name   ,
                    sk.killer_level           AS P2_killer_level           ,
                    sk.killer_gold            AS P2_killer_gold            ,
                    sk.killer_position_x      AS P2_killer_position_x      ,
                    sk.killer_position_y      AS P2_killer_position_y      ,
                    sk.victim_participant_id  AS P2_victim_participant_id  ,
                    sk.victim_champion_id     AS P2_victim_champion_id     ,
                    sk.victim_champion_name   AS P2_victim_champion_name   ,
                    sk.victim_level           AS P2_victim_level           ,
                    sk.victim_gold            AS P2_victim_gold            ,
                    sk.victim_position_x      AS P2_victim_position_x      ,
                    sk.victim_position_y      AS P2_victim_position_y      ,
                    sk.level_diff             AS P2_level_diff             ,
                    sk.gold_diff              AS P2_gold_diff              ,
                    sk.is_first_blood         AS P2_is_first_blood         ,
                    sk.is_shutdown            AS P2_is_shutdown            ,
                    sk.bounty_gold            AS P2_bounty_gold            ,
                    sk.created_at             AS P2_solo_created_at        
                    FROM solo_kills AS sk
                    INNER JOIN kill_items AS ki ON ki.solo_kill_id = sk.id
                    WHERE sk.killer_champion_id > sk.victim_champion_id
                      AND ki.id = (
                          SELECT MIN(id)
                          FROM kill_items
                          WHERE solo_kill_id = ki.solo_kill_id
                      )
                ) AS P2
                ON P1.P1_solo_kill_id = P2.P2_solo_kill_id
                )) AS SOLO_KILL_ITEM_PAIRS
                LEFT JOIN items AS P1_ITEM0 ON P1_ITEM0.id = SOLO_KILL_ITEM_PAIRS.P1_item0
                LEFT JOIN items AS P1_ITEM1 ON P1_ITEM1.id = SOLO_KILL_ITEM_PAIRS.P1_item1
                LEFT JOIN items AS P1_ITEM2 ON P1_ITEM2.id = SOLO_KILL_ITEM_PAIRS.P1_item2
                LEFT JOIN items AS P1_ITEM3 ON P1_ITEM3.id = SOLO_KILL_ITEM_PAIRS.P1_item3
                LEFT JOIN items AS P1_ITEM4 ON P1_ITEM4.id = SOLO_KILL_ITEM_PAIRS.P1_item4
                LEFT JOIN items AS P1_ITEM5 ON P1_ITEM5.id = SOLO_KILL_ITEM_PAIRS.P1_item5
                LEFT JOIN items AS P1_ITEM6 ON P1_ITEM6.id = SOLO_KILL_ITEM_PAIRS.P1_item6
                LEFT JOIN items AS P2_ITEM0 ON P2_ITEM0.id = SOLO_KILL_ITEM_PAIRS.P2_item0
                LEFT JOIN items AS P2_ITEM1 ON P2_ITEM1.id = SOLO_KILL_ITEM_PAIRS.P2_item1
                LEFT JOIN items AS P2_ITEM2 ON P2_ITEM2.id = SOLO_KILL_ITEM_PAIRS.P2_item2
                LEFT JOIN items AS P2_ITEM3 ON P2_ITEM3.id = SOLO_KILL_ITEM_PAIRS.P2_item3
                LEFT JOIN items AS P2_ITEM4 ON P2_ITEM4.id = SOLO_KILL_ITEM_PAIRS.P2_item4
                LEFT JOIN items AS P2_ITEM5 ON P2_ITEM5.id = SOLO_KILL_ITEM_PAIRS.P2_item5
                LEFT JOIN items AS P2_ITEM6 ON P2_ITEM6.id = SOLO_KILL_ITEM_PAIRS.P2_item6
                INNER JOIN matches AS matches ON P1_match_id = matches.match_id
                """
                # 出力は明示的な debug フラグがあるときだけ行う
                if debug:
                    # 標準出力に出してコピーしやすくする
                    print("--- select_training_data SQL (debug) ---")
                    print(query)
                    print("--- params ---")
                    print(params)
                params = []

                # トップレベルの WHERE 条件を安全に構築する
                top_level_clauses = []

                if mychampion is not None:
                    # mychampion が P1 または P2 のどちらかに一致する行のみを取得
                    # enemyChampion が指定されていれば、(my vs enemy) OR (enemy vs my) の対称条件を使う
                    if enemyChampion is not None:
                        top_level_clauses.append("((SOLO_KILL_ITEM_PAIRS.P1_killer_champion_id = %s AND SOLO_KILL_ITEM_PAIRS.P2_victim_champion_id = %s) OR (SOLO_KILL_ITEM_PAIRS.P1_killer_champion_id = %s AND SOLO_KILL_ITEM_PAIRS.P2_victim_champion_id = %s))"
                        )
                        # プレースホルダ順: my, enemy, enemy, my
                        params.extend([mychampion, enemyChampion, enemyChampion, mychampion])
                    else:
                        # 単純に mychampion が P1 または P2 に一致する行
                        top_level_clauses.append("(SOLO_KILL_ITEM_PAIRS.P1_killer_champion_id = %s OR SOLO_KILL_ITEM_PAIRS.P2_victim_champion_id = %s)")
                        params.extend([mychampion, mychampion])
                        # 安全な書き方
                if top_level_clauses:
                    # 組み立てたトップレベル WHERE を安全に追記する（既存の内部トークンを壊さない）
                    where_clause = "\nWHERE " + " AND ".join(top_level_clauses) + "\n"
                    # 末尾に改行がなければ追加してから WHERE を付与
                    if not query.endswith('\n'):
                        query = query + '\n'
                    query = query + where_clause

                # LIMIT は整数化してインラインで追加（例: LIMIT 100）
                try:
                    limit_int = int(limit) if limit is not None else 0
                    if limit_int > 0:
                        if not query.endswith('\n'):
                            query = query + '\n'
                        query = query + f"LIMIT {limit_int}\n"
                except Exception:
                    logger.warning(f"無効な limit 指定を無視します: {limit}")

                # ログは debug フラグで制御。ユーザーが要求したとおり最終SQLを出力するのは debug=True のときだけ
                #print("select_training_data - final query:\n%s", query)
                #print("select_training_data params: %s", params)
                # 標準出力に出してコピーしやすくする
                #print("--- select_training_data SQL (debug) ---")
                #print(query)
                #print("--- params ---")
                #print(params)

                cursor.execute(query, params if params else None)
                rows = cursor.fetchall()

                logger.info("select_training_data - fetched rows: %d", len(rows) if rows else 0)

                # 辞書 cursor を使っているのでそのまま返す
                return [dict(r) for r in rows] if rows else []

        except Error as e:
            logger.error(f"学習データを取得エラー: {e}")
            return []

def main():
    """テスト用のメイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # テスト用の設定
    mysql_config = {
        'host': '160.251.214.153',
        'port': 3306,
        'database': 'loldb',
        'user': 'admin',
        'password': 'RO3f7p6k$!',
        'charset': 'utf8mb4'
    }
    
    try:
        db_manager = RealtimeDatabaseManager(**mysql_config)
        
        # データベース統計を表示
        stats = db_manager.get_database_stats()
        print("=== データベース統計 ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        db_manager.select_training_data(limit=1000000, mychampion=None, enemyChampion=None)
    except Exception as e:
        print(f"データベース接続テストエラー: {e}")

if __name__ == "__main__":
    main()