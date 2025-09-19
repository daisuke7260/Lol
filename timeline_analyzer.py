import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class SoloKillEvent:
    """ソロキルイベント情報"""
    timestamp_ms: int
    game_time_seconds: int
    killer_participant_id: int
    victim_participant_id: int
    killer_level: int
    victim_level: int
    killer_gold: int
    victim_gold: int
    killer_position: Tuple[int, int]
    victim_position: Tuple[int, int]
    is_first_blood: bool
    is_shutdown: bool
    bounty_gold: int
    killer_items: List[int]
    victim_items: List[int]

@dataclass
class ParticipantFrame:
    """参加者のフレーム情報"""
    participant_id: int
    level: int
    current_gold: int
    total_gold: int
    xp: int
    minions_killed: int
    jungle_minions_killed: int
    position: Tuple[int, int]

@dataclass
class LeagueEntryDTO:
    """リーグエントリ情報"""
    league_id: str
    queue_type: str
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int
    hot_streak: bool
    veteran: bool
    fresh_blood: bool
    inactive: bool

class RiotAPIClient:
    """Riot APIクライアント"""
    def __init__(self, api_key: str, region: str = "jp1"):
        self.api_key = api_key
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"
        self.headers = {"X-Riot-Token": self.api_key}
        logger.info(f"RiotAPIClientを初期化しました。Region: {self.region}")

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTPエラーが発生しました: {http_err} - レスポンス: {response.text}")
            return None
        except requests.exceptions.RequestException as req_err:
            logger.error(f"リクエストエラーが発生しました: {req_err}")
            return None

    def get_league_entries_by_puuid(self, puuid: str) -> List[LeagueEntryDTO]:
        """PUUIDからプレイヤーのリーグエントリ（ランク情報）を取得"""
        endpoint = f"/lol/league/v4/entries/by-puuid/{puuid}"
        data = self._make_request(endpoint)
        if data:
            league_entries = []
            for entry in data:
                if entry.get("queueType") == "RANKED_SOLO_5x5":
                    league_entries.append(LeagueEntryDTO(
                        league_id=entry.get("leagueId", ""),
                        queue_type=entry.get("queueType", ""),
                        tier=entry.get("tier", ""),
                        rank=entry.get("rank", ""),
                        league_points=entry.get("leaguePoints", 0),
                        wins=entry.get("wins", 0),
                        losses=entry.get("losses", 0),
                        hot_streak=entry.get("hotStreak", False),
                        veteran=entry.get("veteran", False),
                        fresh_blood=entry.get("freshBlood", False),
                        inactive=entry.get("inactive", False),
                    ))
            return league_entries
        return []

class TimelineAnalyzer:
    """タイムラインデータ分析クラス"""
    
    def __init__(self, api_key: Optional[str] = None, region: str = "jp1"):
        """タイムライン分析器を初期化"""
        self.lane_positions = {
            'TOP': {'x_range': (0, 14000), 'y_range': (0, 14000)},
            'JUNGLE': {'x_range': (0, 14000), 'y_range': (0, 14000)},
            'MIDDLE': {'x_range': (6000, 8000), 'y_range': (6000, 8000)},
            'BOTTOM': {'x_range': (0, 14000), 'y_range': (0, 14000)},
            'UTILITY': {'x_range': (0, 14000), 'y_range': (0, 14000)}
        }
        self.api_client = RiotAPIClient(api_key, region) if api_key else None
        
        # アイテム価値マッピング
        self.item_values = {
            0: 0,        # 空スロット
            1001: 300,   # ブーツ
            1036: 350,   # ロングソード
            1052: 435,   # アンプトーム
            1029: 400,   # クロスソード
            1058: 850,   # ニードレスリーロッド
            3020: 1100,  # ソーサラーシューズ
            3006: 1100,  # バーサーカーグリーブ
            3047: 1100,  # プレートスチールキャップ
            3111: 1100,  # マーキュリーブーツ
            3089: 3200,  # ラバドンデスキャップ
            3135: 2700,  # ヴォイドスタッフ
            3157: 2600,  # ゾーニャの砂時計
            3116: 2600,  # ライライクリスタルセプター
            3165: 2200,  # モレロノミコン
            3285: 3200,  # ルーデンエコー
            3031: 3400,  # インフィニティエッジ
            3094: 2600,  # ラピッドファイアキャノン
            3085: 2600,  # ランナンズハリケーン
            3072: 3300,  # ブラッドサースター
            2003: 50,    # ヘルスポーション
            2031: 500,   # リフィルポーション
            3340: 0,     # ステルスワード
            3364: 0,     # 遠見改良
        }
        
        logger.info("タイムライン分析器を初期化しました")
    
    def calculate_item_value(self, items: List[int]) -> int:
        """アイテムの総価値を計算"""
        if not items:
            return 0
        
        total_value = 0
        for item_id in items:
            if item_id in self.item_values:
                total_value += self.item_values[item_id]
            else:
                # 未知のアイテムは平均価値を使用
                total_value += 1000
        
        return total_value
    
    def analyze_timeline(self, timeline_data: Dict, match_data: Dict) -> Dict[str, Any]:
        """
        タイムラインデータを分析してソロキル情報を抽出
        """
        try:
            logger.info(f"タイムライン分析開始: {match_data.get('metadata', {}).get('matchId', 'Unknown')}")
            
            participants = self._get_participants_info(match_data)
            solo_kills = self._extract_solo_kills(timeline_data, participants)
            lane_solo_kills = self._classify_solo_kills_by_lane(solo_kills, participants)
            statistics = self._calculate_statistics(solo_kills, participants)
            
            result = {
                'match_id': match_data.get('metadata', {}).get('matchId'),
                'game_duration': match_data.get('info', {}).get('gameDuration', 0),
                'solo_kills': solo_kills,
                'lane_solo_kills': lane_solo_kills,
                'statistics': statistics,
                'participants': participants
            }
            
            logger.info(f"タイムライン分析完了: {len(solo_kills)}個のソロキルを検出")
            return result
            
        except Exception as e:
            logger.error(f"タイムライン分析エラー: {e}")
            return {}
    
    def _get_participants_info(self, match_data: Dict) -> Dict[int, Dict]:
        """参加者情報を取得"""
        participants = {}
        try:
            for participant in match_data.get('info', {}).get('participants', []):
                participant_id = participant.get('participantId')
                puuid = participant.get('puuid')
                
                participant_info = {
                    'puuid': puuid,
                    'champion_id': participant.get('championId'),
                    'champion_name': participant.get('championName'),
                    'team_id': participant.get('teamId'),
                    'lane': participant.get('lane'),
                    'team_position': participant.get('teamPosition'),
                    'win': participant.get('win', False)
                }
                
                # ランク情報を取得して追加
                if self.api_client and puuid:
                    league_entries = self.api_client.get_league_entries_by_puuid(puuid)
                    if league_entries:
                        solo_duo_rank = next((entry for entry in league_entries if entry.queue_type == "RANKED_SOLO_5x5"), None)
                        if solo_duo_rank:
                            participant_info['rank_tier'] = solo_duo_rank.tier
                            participant_info['rank_rank'] = solo_duo_rank.rank
                            participant_info['rank_lp'] = solo_duo_rank.league_points
                        else:
                            flex_rank = next((entry for entry in league_entries if entry.queue_type == "RANKED_FLEX_SR"), None)
                            if flex_rank:
                                participant_info['rank_tier'] = flex_rank.tier
                                participant_info['rank_rank'] = flex_rank.rank
                                participant_info['rank_lp'] = flex_rank.league_points
                            else:
                                participant_info['rank_tier'] = "UNRANKED"
                                participant_info['rank_rank'] = ""
                                participant_info['rank_lp'] = 0
                    else:
                        participant_info['rank_tier'] = "UNRANKED"
                        participant_info['rank_rank'] = ""
                        participant_info['rank_lp'] = 0
                else:
                    participant_info['rank_tier'] = "UNKNOWN"
                    participant_info['rank_rank'] = ""
                    participant_info['rank_lp'] = 0

                participants[participant_id] = participant_info
            return participants
        except Exception as e:
            logger.error(f"参加者情報取得エラー: {e}")
            return {}

    def _extract_solo_kills(self, timeline_data: Dict, participants: Dict) -> List[SoloKillEvent]:
        """ソロキルイベントを抽出（正確なキル直前レベル取得）"""
        solo_kills = []
        participant_inventories: Dict[int, List[int]] = {p_id: [] for p_id in participants.keys()}

        try:
            frames = timeline_data.get('info', {}).get('frames', [])
            for i, frame in enumerate(frames):
                timestamp = frame.get('timestamp', 0)
                game_time_seconds = timestamp // 1000
                current_participant_frames = self._parse_participant_frames(frame.get('participantFrames', {}))
                events_in_frame = sorted(frame.get('events', []), key=lambda x: x.get('timestamp', 0))

                # アイテムイベントとキルイベントを分離
                item_events = [e for e in events_in_frame if e.get('type') in ['ITEM_PURCHASED', 'ITEM_SOLD', 'ITEM_DESTROYED', 'ITEM_UNDO']]
                kill_events = [e for e in events_in_frame if e.get('type') == 'CHAMPION_KILL']
                level_up_events = [e for e in events_in_frame if e.get('type') == 'LEVEL_UP']

                # アイテムインベントリを更新
                for event in item_events:
                    participant_id = event.get('participantId')
                    item_id = event.get('itemId')
                    if participant_id and item_id and participant_id in participant_inventories:
                        if event['type'] == 'ITEM_PURCHASED':
                            participant_inventories[participant_id].append(item_id)
                        elif event['type'] == 'ITEM_SOLD' and item_id in participant_inventories[participant_id]:
                            participant_inventories[participant_id].remove(item_id)
                        elif event['type'] == 'ITEM_DESTROYED' and item_id in participant_inventories[participant_id]:
                            participant_inventories[participant_id].remove(item_id)
                        elif event['type'] == 'ITEM_UNDO' and participant_inventories[participant_id] and participant_inventories[participant_id][-1] == item_id:
                            participant_inventories[participant_id].pop()

                # キルイベントを処理
                for kill_event in kill_events:
                    killer_id = kill_event.get('killerId')
                    victim_id = kill_event.get('victimId')
                    kill_timestamp = kill_event.get('timestamp', timestamp)
                    
                    # キル時点でのアイテムを取得
                    killer_items_at_kill = participant_inventories.get(killer_id, [])[:]
                    victim_items_at_kill = participant_inventories.get(victim_id, [])[:]
                    
                    # アイテムリストを7個に調整
                    killer_items_padded = (killer_items_at_kill + [0] * 7)[:7]
                    victim_items_padded = (victim_items_at_kill + [0] * 7)[:7]

                    # キル直前のレベルを正確に取得
                    killer_level_before_kill = current_participant_frames.get(killer_id, ParticipantFrame(killer_id, 1, 0, 0, 0, 0, 0, (0, 0))).level
                    victim_level_before_kill = current_participant_frames.get(victim_id, ParticipantFrame(victim_id, 1, 0, 0, 0, 0, 0, (0, 0))).level

                    # キル後のレベルアップイベントをチェック
                    for level_up_event in level_up_events:
                        level_up_timestamp = level_up_event.get('timestamp', 0)
                        level_up_participant = level_up_event.get('participantId')
                        
                        # キル後にレベルアップした場合、キル前のレベルを調整
                        if level_up_timestamp > kill_timestamp:
                            if level_up_participant == killer_id:
                                # キラーがキル後にレベルアップした場合
                                new_level = level_up_event.get('level', killer_level_before_kill)
                                killer_level_before_kill = max(1, new_level - 1)
                                logger.debug(f"キラー{killer_id}のキル後レベルアップを検出: {new_level} -> キル前レベル: {killer_level_before_kill}")
                            elif level_up_participant == victim_id:
                                # 被害者がキル後にレベルアップした場合（稀だが可能性あり）
                                new_level = level_up_event.get('level', victim_level_before_kill)
                                victim_level_before_kill = max(1, new_level - 1)
                                logger.debug(f"被害者{victim_id}のキル後レベルアップを検出: {new_level} -> キル前レベル: {victim_level_before_kill}")

                    solo_kill = self._process_kill_event(
                        kill_event, kill_timestamp, game_time_seconds, 
                        current_participant_frames, participants,
                        killer_items=killer_items_padded,
                        victim_items=victim_items_padded,
                        killer_level_before_kill=killer_level_before_kill,
                        victim_level_before_kill=victim_level_before_kill
                    )
                    if solo_kill:
                        logger.debug(f"ソロキル検出: キラー{killer_id}(Lv{killer_level_before_kill}) vs 被害者{victim_id}(Lv{victim_level_before_kill})")
                        logger.debug(f"  キラーアイテム: {killer_items_padded}")
                        logger.debug(f"  被害者アイテム: {victim_items_padded}")
                        solo_kills.append(solo_kill)
                        
            return solo_kills
        except Exception as e:
            logger.error(f"ソロキルイベント抽出エラー: {e}")
            return []

    def _parse_participant_frames(self, participant_frames: Dict) -> Dict[int, ParticipantFrame]:
        """参加者フレーム情報を解析"""
        frames = {}
        try:
            for participant_id_str, frame_data in participant_frames.items():
                participant_id = int(participant_id_str)
                position = frame_data.get('position', {})
                frames[participant_id] = ParticipantFrame(
                    participant_id=participant_id,
                    level=frame_data.get('level', 1),
                    current_gold=frame_data.get('currentGold', 0),
                    total_gold=frame_data.get('totalGold', 0),
                    xp=frame_data.get('xp', 0),
                    minions_killed=frame_data.get('minionsKilled', 0),
                    jungle_minions_killed=frame_data.get('jungleMinionsKilled', 0),
                    position=(position.get('x', 0), position.get('y', 0)),
                )
            return frames
        except Exception as e:
            logger.error(f"参加者フレーム解析エラー: {e}")
            return {}

    def _process_kill_event(self, event: Dict, timestamp: int, game_time_seconds: int,
                           participant_frames: Dict[int, ParticipantFrame],
                           participants: Dict,
                           killer_items: List[int], victim_items: List[int],
                           killer_level_before_kill: int, victim_level_before_kill: int) -> Optional[SoloKillEvent]:
        """キルイベントを処理してソロキルかどうか判定（正確なキル直前レベル対応）"""
        try:
            killer_id = event.get('killerId')
            victim_id = event.get('victimId')
            assisting_ids = event.get('assistingParticipantIds', [])
            
            # ソロキルの条件：アシストがない
            if not assisting_ids and killer_id and victim_id:
                killer_frame = participant_frames.get(killer_id)
                victim_frame = participant_frames.get(victim_id)
                if not killer_frame or not victim_frame:
                    return None
                
                # 同じチームのキルは除外
                killer_team = participants.get(killer_id, {}).get('team_id')
                victim_team = participants.get(victim_id, {}).get('team_id')
                if killer_team == victim_team:
                    return None
                
                return SoloKillEvent(
                    timestamp_ms=timestamp,
                    game_time_seconds=game_time_seconds,
                    killer_participant_id=killer_id,
                    victim_participant_id=victim_id,
                    killer_level=killer_level_before_kill,  # 正確なキル直前レベル
                    victim_level=victim_level_before_kill,  # 正確なキル直前レベル
                    killer_gold=killer_frame.total_gold,
                    victim_gold=victim_frame.total_gold,
                    killer_position=killer_frame.position,
                    victim_position=victim_frame.position,
                    is_first_blood=event.get('type') == 'CHAMPION_KILL' and event.get('killType') == 'KILL_FIRST_BLOOD',
                    is_shutdown=event.get('shutdownBounty', 0) > 0,
                    bounty_gold=event.get('bounty', 0),
                    killer_items=killer_items,
                    victim_items=victim_items
                )
            return None
        except Exception as e:
            logger.error(f"キルイベント処理エラー: {e}")
            return None

    def _classify_solo_kills_by_lane(self, solo_kills: List[SoloKillEvent], 
                                   participants: Dict) -> Dict[str, List[SoloKillEvent]]:
        """ソロキルをレーン別に分類"""
        lane_kills = {'TOP': [], 'JUNGLE': [], 'MIDDLE': [], 'BOTTOM': [], 'UTILITY': [], 'UNKNOWN': []}
        try:
            for solo_kill in solo_kills:
                killer_lane = participants.get(solo_kill.killer_participant_id, {}).get('team_position', 'UNKNOWN')
                victim_lane = participants.get(solo_kill.victim_participant_id, {}).get('team_position', 'UNKNOWN')
                lane = killer_lane if killer_lane != 'UNKNOWN' else victim_lane
                if lane not in lane_kills:
                    lane = 'UNKNOWN'
                lane_kills[lane].append(solo_kill)
            return lane_kills
        except Exception as e:
            logger.error(f"レーン別分類エラー: {e}")
            return lane_kills

    def _calculate_statistics(self, solo_kills: List[SoloKillEvent], 
                            participants: Dict) -> Dict[str, Any]:
        """ソロキル統計を計算"""
        try:
            if not solo_kills:
                return {
                    'total_solo_kills': 0, 
                    'first_blood_time': 0, 
                    'average_level_diff': 0.0, 
                    'average_gold_diff': 0.0, 
                    'early_game_kills': 0, 
                    'mid_game_kills': 0, 
                    'late_game_kills': 0
                }
            
            total_kills = len(solo_kills)
            first_blood_time = min(kill.timestamp_ms for kill in solo_kills)
            level_diffs = [kill.killer_level - kill.victim_level for kill in solo_kills]
            gold_diffs = [kill.killer_gold - kill.victim_gold for kill in solo_kills]
            avg_level_diff = sum(level_diffs) / len(level_diffs) if level_diffs else 0.0
            avg_gold_diff = sum(gold_diffs) / len(gold_diffs) if gold_diffs else 0.0
            early_game_kills = len([k for k in solo_kills if k.game_time_seconds <= 900])
            mid_game_kills = len([k for k in solo_kills if 900 < k.game_time_seconds <= 1500])
            late_game_kills = len([k for k in solo_kills if k.game_time_seconds > 1500])
            
            return {
                'total_solo_kills': total_kills,
                'first_blood_time': first_blood_time,
                'average_level_diff': avg_level_diff,
                'average_gold_diff': avg_gold_diff,
                'early_game_kills': early_game_kills,
                'mid_game_kills': mid_game_kills,
                'late_game_kills': late_game_kills
            }
        except Exception as e:
            logger.error(f"統計計算エラー: {e}")
            return {
                'total_solo_kills': 0, 
                'first_blood_time': 0, 
                'average_level_diff': 0.0, 
                'average_gold_diff': 0.0, 
                'early_game_kills': 0, 
                'mid_game_kills': 0, 
                'late_game_kills': 0
            }

    def get_matchup_solo_kills(self, solo_kills: List[SoloKillEvent], 
                              participants: Dict) -> List[SoloKillEvent]:
        """対面チャンピオン間のソロキルのみを抽出"""
        matchup_kills = []
        try:
            for solo_kill in solo_kills:
                killer_lane = participants.get(solo_kill.killer_participant_id, {}).get('team_position', 'UNKNOWN')
                victim_lane = participants.get(solo_kill.victim_participant_id, {}).get('team_position', 'UNKNOWN')
                
                # 同じレーンの対面チャンピオン間のキルのみを抽出
                if killer_lane == victim_lane and killer_lane != 'UNKNOWN':
                    matchup_kills.append(solo_kill)
                    
            logger.info(f"対面ソロキル抽出: {len(matchup_kills)}個")
            return matchup_kills
        except Exception as e:
            logger.error(f"対面ソロキル抽出エラー: {e}")
            return []
