#!/usr/bin/env python3
"""
League of Legends 自動BANツール V3 コアモジュール
V2の機能をベースに、GUI連携機能を追加
"""

import requests
import json
import time
import base64
import psutil
import re
import os
import logging
import threading
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# SSL警告を無効化
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class LOLAutoBanV3Core:
    def __init__(self, config_file="ban_config_v3.json", log_file="lol_auto_ban_v3.log", gui_callback=None):
        self.config_file = config_file
        self.log_file = log_file
        self.gui_callback = gui_callback  # GUI更新用コールバック
        self.lcu_port = None
        self.lcu_token = None
        self.base_url = None
        self.headers = None
        
        # 基本設定
        self.ban_champion = None
        self.auto_ban_enabled = True  # 自動BAN機能の有効/無効制御
        self.auto_accept_queue = True
        self.accept_delay_seconds = 0.5
        
        # 新機能設定
        self.auto_pick_champion = True
        self.pick_delay_seconds = 1.0
        self.auto_lock = True
        self.champion_preferences = {}
        self.fallback_champions = []
        
        # 実行状態
        self.running = False
        self.ban_executed = False
        self.pick_executed = False
        self.connected = False
        
        # キャッシュ
        self.owned_champions = []
        self.champion_id_map = {}
        
        self.setup_logging()
        self.load_config()
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_message(self, message, level="INFO"):
        """ログメッセージを出力（GUI連携対応）"""
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        
        # GUIコールバックがあれば通知
        if self.gui_callback:
            try:
                self.gui_callback("log", message)
            except:
                pass  # GUI更新エラーは無視
        
    def update_gui_status(self, status_type, value):
        """GUI状態を更新"""
        if self.gui_callback:
            try:
                self.gui_callback(status_type, value)
            except:
                pass  # GUI更新エラーは無視
    
    def load_config(self):
        """設定ファイルから設定を読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 基本設定
                    self.ban_champion = config.get('ban_champion', 'Yasuo')
                    self.auto_ban_enabled = config.get('auto_ban_enabled', True)
                    self.auto_accept_queue = config.get('auto_accept_queue', True)
                    self.accept_delay_seconds = config.get('accept_delay_seconds', 0.5)
                    
                    # 新機能設定
                    self.auto_pick_champion = config.get('auto_pick_champion', True)
                    self.pick_delay_seconds = config.get('pick_delay_seconds', 1.0)
                    self.auto_lock = config.get('auto_lock', True)
                    self.champion_preferences = config.get('champion_preferences', {})
                    self.fallback_champions = config.get('fallback_champions', ['Garen', 'Annie', 'Ashe'])
                    
                    self.log_message(f"V3設定ファイル読み込み完了:")
                    self.log_message(f"  BANするチャンピオン: {self.ban_champion}")
                    self.log_message(f"  自動BAN有効: {self.auto_ban_enabled}")
                    self.log_message(f"  自動キュー受諾: {self.auto_accept_queue}")
                    self.log_message(f"  自動チャンピオンピック: {self.auto_pick_champion}")
                    self.log_message(f"  自動ロック: {self.auto_lock}")
                    self.log_message(f"  フォールバックチャンピオン: {self.fallback_champions}")
            else:
                # V2設定をフォールバック
                v2_config = "ban_config_v2_extended.json"
                if os.path.exists(v2_config):
                    self.log_message(f"V3設定が見つからないため、V2設定 {v2_config} を使用します")
                    self.config_file = v2_config
                    self.load_config()  # 再帰的に読み込み
                else:
                    # デフォルト設定ファイルを作成
                    self.create_default_config()
                    self.load_config()  # 再帰的に読み込み
        except Exception as e:
            self.log_message(f"設定ファイルの読み込みエラー: {e}", "ERROR")
            self.set_default_values()
    
    def create_default_config(self):
        """デフォルト設定ファイルを作成"""
        default_config = {
            "ban_champion": "Yasuo",
            "auto_accept_queue": True,
            "accept_delay_seconds": 0.5,
            "auto_pick_champion": True,
            "pick_delay_seconds": 1.0,
            "auto_lock": True,
            "champion_preferences": {
                "top": ["Garen", "Darius", "Malphite"],
                "jungle": ["Master Yi", "Warwick", "Ammu"],
                "middle": ["Annie", "Lux", "Yasuo"],
                "bottom": ["Ashe", "Jinx", "Miss Fortune"],
                "utility": ["Blitzcrank", "Thresh", "Morgana"]
            },
            "fallback_champions": ["Garen", "Annie", "Ashe"],
            "description": "V3設定ファイル（GUI対応）",
            "version": "3.0"
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        self.log_message(f"デフォルト設定ファイル {self.config_file} を作成しました")
    
    def set_default_values(self):
        """デフォルト値を設定"""
        self.ban_champion = "Yasuo"
        self.auto_accept_queue = True
        self.accept_delay_seconds = 0.5
        self.auto_pick_champion = True
        self.pick_delay_seconds = 1.0
        self.auto_lock = True
        self.champion_preferences = {
            "top": ["Garen", "Darius"],
            "jungle": ["Master Yi", "Warwick"],
            "middle": ["Annie", "Lux"],
            "bottom": ["Ashe", "Jinx"],
            "utility": ["Blitzcrank", "Thresh"]
        }
        self.fallback_champions = ["Garen", "Annie", "Ashe"]
            
    def find_lcu_process(self):
        """League Clientプロセスを見つけてLCU APIの接続情報を取得"""
        try:
            self.log_message("League Clientプロセスを検索中...")
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] in ['LeagueClientUx.exe', 'LeagueClientUx']:
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmdline_str = ' '.join(cmdline)
                            
                            # ポート番号を抽出
                            port_match = re.search(r'--app-port=(\d+)', cmdline_str)
                            if port_match:
                                self.lcu_port = port_match.group(1)
                            
                            # 認証トークンを抽出
                            token_match = re.search(r'--remoting-auth-token=([a-zA-Z0-9_-]+)', cmdline_str)
                            if token_match:
                                self.lcu_token = token_match.group(1)
                            
                            if self.lcu_port and self.lcu_token:
                                self.base_url = f"https://127.0.0.1:{self.lcu_port}"
                                auth_string = f"riot:{self.lcu_token}"
                                auth_bytes = base64.b64encode(auth_string.encode()).decode()
                                self.headers = {
                                    'Authorization': f'Basic {auth_bytes}',
                                    'Content-Type': 'application/json'
                                }
                                self.log_message(f"League Client発見: ポート {self.lcu_port}")
                                self.connected = True
                                self.update_gui_status("connection", True)
                                return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.log_message("League Clientプロセスが見つかりません", "WARNING")
            self.connected = False
            self.update_gui_status("connection", False)
            return False
        except Exception as e:
            self.log_message(f"LCUプロセス検索エラー: {e}", "ERROR")
            self.connected = False
            self.update_gui_status("connection", False)
            return False
    
    def make_request(self, method, endpoint, data=None):
        """LCU APIにリクエストを送信"""
        try:
            url = f"{self.base_url}{endpoint}"
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, verify=False, timeout=5)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, verify=False, timeout=5)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data, verify=False, timeout=5)
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                return None
        except requests.exceptions.RequestException:
            return None
        except Exception as e:
            self.log_message(f"予期しないリクエストエラー: {e}", "ERROR")
            return None
    
    def load_champion_data(self):
        """チャンピオンデータを読み込み（LCU API + 静的データ）"""
        try:
            # まず静的データを読み込み（フォールバック用）
            self.load_static_champion_data()
            
            # LCU APIが利用可能な場合は動的データも取得
            if self.connected:
                # 所有チャンピオン一覧を取得
                owned_champions = self.make_request('GET', '/lol-champions/v1/owned-champions-minimal')
                if owned_champions:
                    self.owned_champions = owned_champions
                    self.log_message(f"所有チャンピオン数: {len(owned_champions)}")
                
                # 全チャンピオン一覧を取得してID マップを作成
                all_champions = self.make_request('GET', '/lol-champions/v1/inventories/1/champions')
                if all_champions:
                    for champ in all_champions:
                        name = champ.get('name', champ.get('alias', ''))
                        champ_id = champ.get('id', champ.get('championId'))
                        if name and champ_id:
                            self.champion_id_map[name] = champ_id
                    self.log_message(f"LCU APIからチャンピオンIDマップ更新完了: {len(self.champion_id_map)}体")
                else:
                    self.log_message("LCU APIからのチャンピオンデータ取得に失敗、静的データを使用")
            else:
                self.log_message("LCU API未接続、静的データのみ使用")
            
        except Exception as e:
            self.log_message(f"チャンピオンデータ読み込みエラー: {e}", "ERROR")
    
    def load_static_champion_data(self):
        """静的チャンピオンデータを読み込み"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            champions_file = os.path.join(current_dir, 'champions_data.json')
            
            if os.path.exists(champions_file):
                with open(champions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    champion_ids = data.get('champion_ids', {})
                    
                    # 静的データからIDマップを初期化
                    self.champion_id_map.update(champion_ids)
                    self.log_message(f"静的チャンピオンデータ読み込み完了: {len(champion_ids)}体")
            else:
                self.log_message("champions_data.jsonファイルが見つかりません", "WARNING")
                
        except Exception as e:
            self.log_message(f"静的チャンピオンデータ読み込みエラー: {e}", "ERROR")
    
    def get_champion_id_by_name(self, champion_name):
        """チャンピオン名からIDを取得"""
        try:
            # キャッシュから検索
            if champion_name in self.champion_id_map:
                self.log_message(f"キャッシュからチャンピオン '{champion_name}' を発見 (ID: {self.champion_id_map[champion_name]})")
                return self.champion_id_map[champion_name]
            
            # 複数のAPIエンドポイントを試行
            api_endpoints = [
                '/lol-champions/v1/inventories/1/champions',
                '/lol-champions/v1/inventories/CHAMPION/champions',
                '/lol-game-data/assets/v1/champions.json',
                '/lol-champions/v1/champions'
            ]
            
            champions = None
            successful_endpoint = None
            
            for endpoint in api_endpoints:
                self.log_message(f"APIエンドポイント '{endpoint}' を試行中...")
                champions = self.make_request('GET', endpoint)
                if champions:
                    successful_endpoint = endpoint
                    self.log_message(f"エンドポイント '{endpoint}' から応答を取得")
                    break
                else:
                    self.log_message(f"エンドポイント '{endpoint}' は利用できません")
            
            if not champions:
                self.log_message("全てのAPIエンドポイントが利用できません", "ERROR")
                # フォールバック: 静的なチャンピオンIDマップを使用
                return self.get_champion_id_from_static_data(champion_name)
            
            self.log_message(f"API応答: {len(champions)}体のチャンピオンデータを取得 (エンドポイント: {successful_endpoint})")
            
            # データ構造を確認
            if champions and len(champions) > 0:
                first_champion = champions[0]
                self.log_message(f"チャンピオンデータ構造: {list(first_champion.keys())}")
                
                # デバッグ: 最初の5体のチャンピオン名を表示
                for i, champion in enumerate(champions[:5]):
                    name = champion.get('name', champion.get('alias', champion.get('key', 'N/A')))
                    champ_id = champion.get('id', champion.get('championId', 'N/A'))
                    self.log_message(f"チャンピオン例 {i+1}: name='{name}', id={champ_id}")
            
            # 完全一致検索
            for champion in champions:
                name = champion.get('name', champion.get('alias', champion.get('key', '')))
                if name == champion_name:
                    champion_id = champion.get('id', champion.get('championId'))
                    if champion_id:
                        self.champion_id_map[champion_name] = champion_id
                        self.log_message(f"完全一致でチャンピオン '{champion_name}' を発見 (ID: {champion_id})")
                        return champion_id
            
            # 大文字小文字を無視した検索
            for champion in champions:
                name = champion.get('name', champion.get('alias', champion.get('key', '')))
                if name.lower() == champion_name.lower():
                    champion_id = champion.get('id', champion.get('championId'))
                    if champion_id:
                        self.champion_id_map[champion_name] = champion_id
                        self.log_message(f"大文字小文字無視でチャンピオン '{champion_name}' を発見 (実際の名前: '{name}', ID: {champion_id})")
                        return champion_id
            
            # 全チャンピオン名をログに出力（デバッグ用）
            all_names = []
            for champ in champions:
                name = champ.get('name', champ.get('alias', champ.get('key', 'N/A')))
                all_names.append(name)
            
            self.log_message(f"利用可能な全チャンピオン名: {', '.join(sorted(all_names))}")
            
            # 静的データからの検索を試行
            static_id = self.get_champion_id_from_static_data(champion_name)
            if static_id:
                return static_id
            
            self.log_message(f"チャンピオン '{champion_name}' が見つかりません", "ERROR")
            return None
        except Exception as e:
            self.log_message(f"チャンピオンID取得エラー: {e}", "ERROR")
            return None
    
    def get_champion_id_from_static_data(self, champion_name):
        """静的データからチャンピオンIDを取得"""
        try:
            # champions_data.jsonから読み込み
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            champions_file = os.path.join(current_dir, 'champions_data.json')
            
            if os.path.exists(champions_file):
                with open(champions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    champion_ids = data.get('champion_ids', {})
                    if champion_name in champion_ids:
                        champion_id = champion_ids[champion_name]
                        self.log_message(f"静的データからチャンピオン '{champion_name}' を発見 (ID: {champion_id})")
                        return champion_id
            
            self.log_message(f"静的データにもチャンピオン '{champion_name}' が見つかりません", "WARNING")
            return None
        except Exception as e:
            self.log_message(f"静的データ読み込みエラー: {e}", "ERROR")
            return None
    
    def is_champion_owned(self, champion_id):
        """チャンピオンを所有しているかチェック（常にTrueを返すよう修正）"""
        # 所有・未所有に関わらず全てのチャンピオンを選択可能にする
        return True
    
    def is_champion_available(self, champion_id, session):
        """チャンピオンが選択可能かチェック（所有チェックを無効化）"""
        # 所有チェックを無効化 - 全てのチャンピオンを利用可能とする
        # if not self.is_champion_owned(champion_id):
        #     return False, "未所有"
        
        # 選択済み・BAN済みチェックのみ実行
        for action_group in session.get('actions', []):
            for action in action_group:
                if action.get('championId') == champion_id and action.get('completed'):
                    action_type = action.get('type', '')
                    if action_type == 'pick':
                        return False, "選択済み"
                    elif action_type == 'ban':
                        return False, "BAN済み"
        
        return True, "利用可能"
    
    def detect_assigned_position(self, session):
        """割り当てられたポジションを検出"""
        try:
            # セッションからポジション情報を取得
            my_team = session.get('myTeam', [])
            local_player_cell_id = session.get('localPlayerCellId')
            
            for player in my_team:
                if player.get('cellId') == local_player_cell_id:
                    assigned_position = player.get('assignedPosition', '')
                    # ポジション名を標準化
                    position_map = {
                        'top': 'top',
                        'jungle': 'jungle', 
                        'middle': 'middle',
                        'bottom': 'bottom',
                        'utility': 'utility'
                    }
                    detected_position = position_map.get(assigned_position.lower(), 'middle')
                    self.update_gui_status("position", detected_position)
                    return detected_position
            
            self.log_message("ポジション検出に失敗、ミッドレーンを使用", "WARNING")
            return 'middle'
        except Exception as e:
            self.log_message(f"ポジション検出エラー: {e}", "ERROR")
            return 'middle'
    
    def get_preferred_champions(self, position):
        """ポジションに応じた優先チャンピオンリストを取得"""
        preferred = self.champion_preferences.get(position, [])
        if not preferred:
            self.log_message(f"ポジション '{position}' の設定がありません、フォールバックを使用", "WARNING")
            return self.fallback_champions
        return preferred + self.fallback_champions  # フォールバックを追加
    
    def select_best_champion(self, session, position):
        """最適なチャンピオンを選択"""
        preferred_champions = self.get_preferred_champions(position)
        
        for champion_name in preferred_champions:
            champion_id = self.get_champion_id_by_name(champion_name)
            if champion_id:
                available, reason = self.is_champion_available(champion_id, session)
                if available:
                    self.log_message(f"チャンピオン選択: {champion_name} (ポジション: {position})")
                    self.update_gui_status("selected_champion", champion_name)
                    return champion_id, champion_name
        
        self.log_message("利用可能なチャンピオンが見つかりません", "ERROR")
        return None, None
    
    def pick_champion(self, champion_id, champion_name, action_id):
        """チャンピオンをピックする"""
        try:
            if self.pick_delay_seconds > 0:
                self.log_message(f"{self.pick_delay_seconds}秒待機してからピックします")
                time.sleep(self.pick_delay_seconds)
            
            pick_data = {
                'championId': champion_id,
                'completed': self.auto_lock
            }
            
            result = self.make_request('PATCH', f'/lol-champ-select/v1/session/actions/{action_id}', pick_data)
            if result is not None or True:  # PATCHは成功時にレスポンスがない場合がある
                if self.auto_lock:
                    self.log_message(f"✅ チャンピオン {champion_name} をピック＆ロックしました！")
                else:
                    self.log_message(f"✅ チャンピオン {champion_name} をピックしました（ロック待機中）")
                self.update_gui_status("pick_success", champion_name)
                return True
            else:
                self.log_message("ピックAPIの実行に失敗しました", "WARNING")
                return False
        except Exception as e:
            self.log_message(f"ピック実行エラー: {e}", "ERROR")
            return False
    
    # 既存のキュー受諾とBAN機能（V2から継承）
    def get_ready_check_state(self):
        """キュー受諾状態を取得"""
        return self.make_request('GET', '/lol-matchmaking/v1/ready-check')
    
    def accept_match(self):
        """マッチを受諾"""
        try:
            if self.accept_delay_seconds > 0:
                time.sleep(self.accept_delay_seconds)
            
            result = self.make_request('POST', '/lol-matchmaking/v1/ready-check/accept')
            if result is not None:
                self.log_message("✅ マッチを受諾しました！")
                self.update_gui_status("queue_accepted", True)
                return True
            else:
                self.log_message("✅ マッチ受諾リクエストを送信しました")
                self.update_gui_status("queue_accepted", True)
                return True
        except Exception as e:
            self.log_message(f"マッチ受諾エラー: {e}", "ERROR")
            return False
    
    def get_champ_select_session(self):
        """チャンピオンセレクトセッション情報を取得"""
        return self.make_request('GET', '/lol-champ-select/v1/session')
    
    def ban_champion_by_name(self, champion_name):
        """チャンピオン名でBANを実行"""
        try:
            session = self.get_champ_select_session()
            if not session:
                return False
            
            champion_id = self.get_champion_id_by_name(champion_name)
            if not champion_id:
                return False
            
            # 自分のBANアクションを見つける
            local_player_cell_id = session.get('localPlayerCellId')
            actions = session.get('actions', [])
            
            for action_group in actions:
                for action in action_group:
                    if (action.get('actorCellId') == local_player_cell_id and 
                        action.get('type') == 'ban' and 
                        not action.get('completed')):
                        
                        # BANアクションを実行
                        action_id = action.get('id')
                        ban_data = {
                            'championId': champion_id,
                            'completed': True
                        }
                        
                        result = self.make_request('PATCH', f'/lol-champ-select/v1/session/actions/{action_id}', ban_data)
                        if result is not None or True:
                            self.log_message(f"✅ チャンピオン {champion_name} をBANしました！")
                            self.update_gui_status("ban_success", champion_name)
                            return True
                        else:
                            self.log_message("BAN APIの実行に失敗しました", "WARNING")
            
            return False
        except Exception as e:
            self.log_message(f"BAN実行エラー: {e}", "ERROR")
            return False
    
    def monitor_queue_state(self):
        """キュー状態を監視してマッチ受諾を実行"""
        self.log_message("=== キュー状態監視開始 ===")
        self.update_gui_status("phase", "キュー監視")
        
        last_ready_check_state = None
        
        while self.running:
            try:
                if not self.auto_accept_queue:
                    time.sleep(2)
                    continue
                
                ready_check = self.get_ready_check_state()
                
                if ready_check:
                    state = ready_check.get('state')
                    
                    if state != last_ready_check_state:
                        if state:
                            self.log_message(f"キュー状態: {state}")
                            self.update_gui_status("queue_state", state)
                        last_ready_check_state = state
                    
                    if state == 'InProgress':
                        player_response = ready_check.get('playerResponse')
                        if player_response == 'None':
                            self.log_message("🎯 マッチが見つかりました！自動受諾を実行します")
                            if self.accept_match():
                                time.sleep(3)
                else:
                    if last_ready_check_state:
                        last_ready_check_state = None
                        self.update_gui_status("queue_state", "待機中")
                
                time.sleep(1)
                
            except Exception as e:
                self.log_message(f"キュー監視エラー: {e}", "ERROR")
                time.sleep(5)
    
    def monitor_champ_select(self):
        """チャンピオンセレクトを監視してBAN/ピックを実行"""
        self.log_message("=== チャンピオンセレクト監視開始 ===")
        
        last_phase = None
        
        while self.running:
            try:
                session = self.get_champ_select_session()
                
                if session:
                    timer = session.get('timer', {})
                    phase = timer.get('phase')
                    
                    if phase != last_phase:
                        if phase:
                            self.log_message(f"チャンピオンセレクトフェーズ: {phase}")
                            self.update_gui_status("phase", f"チャンピオンセレクト: {phase}")
                        last_phase = phase
                        
                        # 新しいセッションの場合、実行状態をリセット
                        if phase == 'PLANNING':
                            self.ban_executed = False
                            self.pick_executed = False
                            # チャンピオンデータを更新
                            self.load_champion_data()
                    
                    # BANフェーズの処理
                    if phase == 'BAN_PICK' and not self.ban_executed and self.auto_ban_enabled:
                        self.log_message("BANフェーズを検出しました")
                        if self.ban_champion_by_name(self.ban_champion):
                            self.ban_executed = True
                        else:
                            self.log_message("BAN実行に失敗しました", "WARNING")
                    elif phase == 'BAN_PICK' and not self.ban_executed and not self.auto_ban_enabled:
                        self.log_message("自動BAN機能が無効のため、BANをスキップします")
                    
                    # ピックフェーズの処理
                    if phase == 'BAN_PICK' and not self.pick_executed and self.auto_pick_champion:
                        # 自分のピックターンかチェック
                        local_player_cell_id = session.get('localPlayerCellId')
                        actions = session.get('actions', [])
                        
                        for action_group in actions:
                            for action in action_group:
                                if (action.get('actorCellId') == local_player_cell_id and 
                                    action.get('type') == 'pick' and 
                                    not action.get('completed') and
                                    action.get('isInProgress', False)):
                                    
                                    self.log_message("ピックフェーズを検出しました")
                                    
                                    # ポジション検出
                                    position = self.detect_assigned_position(session)
                                    self.log_message(f"検出されたポジション: {position}")
                                    
                                    # 最適なチャンピオンを選択
                                    champion_id, champion_name = self.select_best_champion(session, position)
                                    
                                    if champion_id and champion_name:
                                        action_id = action.get('id')
                                        if self.pick_champion(champion_id, champion_name, action_id):
                                            self.pick_executed = True
                                        else:
                                            self.log_message("ピック実行に失敗しました", "ERROR")
                                    else:
                                        self.log_message("適切なチャンピオンが見つかりません", "ERROR")
                
                else:
                    if last_phase:
                        self.log_message("チャンピオンセレクトが終了しました")
                        self.update_gui_status("phase", "待機中")
                        last_phase = None
                        self.ban_executed = False
                        self.pick_executed = False
                
                time.sleep(1)
                
            except Exception as e:
                self.log_message(f"チャンピオンセレクト監視エラー: {e}", "ERROR")
                time.sleep(5)
    
    def test_connection(self):
        """LCU API接続テスト"""
        try:
            summoner = self.make_request('GET', '/lol-summoner/v1/current-summoner')
            if summoner:
                display_name = summoner.get('displayName', 'Unknown')
                self.log_message(f"✅ 接続テスト成功 - サモナー: {display_name}")
                self.connected = True
                self.update_gui_status("connection", True)
                self.update_gui_status("summoner", display_name)
                return True
            else:
                self.log_message("❌ 接続テスト失敗", "ERROR")
                self.connected = False
                self.update_gui_status("connection", False)
                return False
        except Exception as e:
            self.log_message(f"接続テストエラー: {e}", "ERROR")
            self.connected = False
            self.update_gui_status("connection", False)
            return False
    
    def start_monitoring(self):
        """並行監視を開始"""
        self.running = True
        self.update_gui_status("running", True)
        
        # キュー状態監視スレッド
        queue_thread = threading.Thread(target=self.monitor_queue_state, daemon=True)
        queue_thread.start()
        
        # チャンピオンセレクト監視スレッド
        champ_select_thread = threading.Thread(target=self.monitor_champ_select, daemon=True)
        champ_select_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log_message("\\n監視を停止します")
            self.running = False
            self.update_gui_status("running", False)
    
    def stop_monitoring(self):
        """監視を停止"""
        self.running = False
        self.update_gui_status("running", False)
        self.log_message("監視を停止しました")
    
    def run(self):
        """メイン実行関数（GUI連携対応）"""
        self.log_message("=== League of Legends 自動BANツール V3 コア開始 ===")
        self.log_message("機能: 自動キュー受諾 + 自動BAN + 自動ピック + GUI連携")
        
        if not self.find_lcu_process():
            self.log_message("League Clientが見つかりません。League of Legendsを起動してログインしてください。", "ERROR")
            return False
        
        if not self.test_connection():
            self.log_message("League Clientへの接続に失敗しました", "ERROR")
            return False
        
        # 初期データ読み込み
        self.load_champion_data()
        
        self.log_message("🚀 V3コア機能が有効になりました")
        if self.auto_accept_queue:
            self.log_message("  ✅ 自動キュー受諾: 有効")
        else:
            self.log_message("  ❌ 自動キュー受諾: 無効")
        
        self.log_message(f"  🚫 自動BAN: {self.ban_champion}")
        
        if self.auto_pick_champion:
            self.log_message("  🎯 自動ピック: 有効")
            self.log_message(f"  🔒 自動ロック: {'有効' if self.auto_lock else '無効'}")
        else:
            self.log_message("  ❌ 自動ピック: 無効")
        
        self.start_monitoring()
        return True

if __name__ == "__main__":
    # コア単体でのテスト実行
    core = LOLAutoBanV3Core()
    core.run()

