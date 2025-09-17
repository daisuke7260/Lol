"""
Main execution script for LOL Realtime Winrate Data Collection
リアルタイム勝率予測システムのデータ収集実行スクリプト
"""

import logging
import sys
import argparse
from datetime import datetime
from pathlib import Path

from realtime_data_collector import RealtimeDataCollector
from config import MYSQL_CONFIG, RIOT_API_KEY, RIOT_REGION, DATA_COLLECTION_CONFIG

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_data_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_prerequisites() -> bool:
    """前提条件をチェック"""
    logger.info("前提条件をチェック中...")
    
    # APIキーのチェック
    if RIOT_API_KEY == 'RGAPI-your-api-key-here':
        logger.error("Riot Games APIキーが設定されていません")
        logger.error("config.pyまたは環境変数RIOT_API_KEYを設定してください")
        return False
    
    # データベース接続テスト
    try:
        from database_manager_realtime import RealtimeDatabaseManager
        db_manager = RealtimeDatabaseManager(**MYSQL_CONFIG)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result:
            logger.info("データベース接続テスト成功")
        else:
            logger.error("データベース接続テスト失敗")
            return False
            
    except Exception as e:
        logger.error(f"データベース接続エラー: {e}")
        logger.error("setup_realtime_database.py を実行してデータベースをセットアップしてください")
        return False
    
    # 必要なテーブルの存在確認
    try:
        stats = db_manager.get_database_stats()
        required_tables = ['champions', 'items', 'matches', 'solo_kills']
        
        for table in required_tables:
            if f"{table}_count" not in stats:
                logger.error(f"必要なテーブルが見つかりません: {table}")
                return False
        
        logger.info("データベーステーブル確認完了")
        
    except Exception as e:
        logger.error(f"テーブル確認エラー: {e}")
        return False
    
    logger.info("前提条件チェック完了")
    return True

def run_small_test() -> bool:
    """小規模テストを実行"""
    logger.info("小規模テスト開始...")
    
    try:
        # データ収集システムを初期化
        collector = RealtimeDataCollector(RIOT_API_KEY, MYSQL_CONFIG, RIOT_REGION)
        
        # 静的データをセットアップ
        logger.info("静的データセットアップ中...")
        if not collector.setup_static_data():
            logger.error("静的データセットアップに失敗")
            return False
        
        # 小規模データ収集
        logger.info("小規模データ収集開始...")
        results = collector.collect_from_high_rank_players(
            tier='GRANDMASTER',
            player_count=3,
            matches_per_player=5
        )
        
        # 結果を表示
        logger.info("=== 小規模テスト結果 ===")
        logger.info(f"処理プレイヤー数: {results.get('total_players_processed', 0)}")
        logger.info(f"収集試合数: {results.get('matches_processed', 0)}")
        logger.info(f"ソロキル数: {results.get('solo_kills_found', 0)}")
        logger.info(f"対面データ数: {results.get('matchups_created', 0)}")
        logger.info(f"タイムライン分析数: {results.get('timeline_analyzed', 0)}")
        logger.info(f"失敗リクエスト数: {results.get('failed_requests', 0)}")
        
        if results.get('matches_processed', 0) > 0:
            logger.info("小規模テスト成功")
            return True
        else:
            logger.warning("小規模テストで試合データを収集できませんでした")
            return False
        
    except Exception as e:
        logger.error(f"小規模テストエラー: {e}")
        return False

def run_full_collection(tier: str = 'ALL', player_count: int = 50, 
                       matches_per_player: int = 20) -> bool:
    """本格的なデータ収集を実行"""
    logger.info("本格的なデータ収集開始...")
    
    try:
        # データ収集システムを初期化
        collector = RealtimeDataCollector(RIOT_API_KEY, MYSQL_CONFIG, RIOT_REGION)
        
        # 静的データをセットアップ
        if not collector.setup_static_data():
            logger.error("静的データセットアップに失敗")
            return False
        
        # 収集前のデータベース統計
        logger.info("=== 収集前のデータベース統計 ===")
        db_stats_before = collector.get_collection_stats()
        for key, value in db_stats_before.items():
            if key.endswith('_count'):
                logger.info(f"{key}: {value}")
        
        # データ収集実行
        all_results = {}
        
        if tier == 'ALL':
            tiers = ['CHALLENGER', 'GRANDMASTER', 'MASTER']
            tier_player_count = player_count // len(tiers)
        else:
            tiers = [tier]
            tier_player_count = player_count
        
        total_stats = {
            'total_players_processed': 0,
            'total_matches_collected': 0,
            'total_solo_kills_found': 0,
            'total_matchups_created': 0,
            'total_timeline_analyzed': 0,
            'total_failed_requests': 0
        }
        
        for current_tier in tiers:
            logger.info(f"ティア処理開始: {current_tier}")
            
            try:
                tier_results = collector.collect_from_high_rank_players(
                    tier=current_tier,
                    player_count=tier_player_count,
                    matches_per_player=matches_per_player
                )
                
                all_results[current_tier] = tier_results
                
                # 統計を累積
                total_stats['total_players_processed'] += tier_results.get('total_players_processed', 0)
                total_stats['total_matches_collected'] += tier_results.get('matches_processed', 0)
                total_stats['total_solo_kills_found'] += tier_results.get('solo_kills_found', 0)
                total_stats['total_matchups_created'] += tier_results.get('matchups_created', 0)
                total_stats['total_timeline_analyzed'] += tier_results.get('timeline_analyzed', 0)
                total_stats['total_failed_requests'] += tier_results.get('failed_requests', 0)
                
                logger.info(f"ティア処理完了: {current_tier}")
                
            except Exception as e:
                logger.error(f"ティア処理エラー: {current_tier} - {e}")
                all_results[current_tier] = {'error': str(e)}
                continue
        
        # 収集後のデータベース統計
        logger.info("\n=== 収集後のデータベース統計 ===")
        db_stats_after = collector.get_collection_stats()
        for key, value in db_stats_after.items():
            if key.endswith('_count'):
                logger.info(f"{key}: {value}")
        
        # 最終結果サマリー
        logger.info("\n=== 最終結果サマリー ===")
        logger.info(f"総処理プレイヤー数: {total_stats['total_players_processed']}")
        logger.info(f"総収集試合数: {total_stats['total_matches_collected']}")
        logger.info(f"総ソロキル数: {total_stats['total_solo_kills_found']}")
        logger.info(f"総対面データ数: {total_stats['total_matchups_created']}")
        logger.info(f"総タイムライン分析数: {total_stats['total_timeline_analyzed']}")
        logger.info(f"総失敗リクエスト数: {total_stats['total_failed_requests']}")
        
        # 成功判定
        if total_stats['total_matches_collected'] > 0:
            logger.info("本格的なデータ収集成功")
            return True
        else:
            logger.warning("本格的なデータ収集で試合データを収集できませんでした")
            return False
        
    except Exception as e:
        logger.error(f"本格的なデータ収集エラー: {e}")
        return False

def run_single_match_test(match_id: str) -> bool:
    """単一試合のテスト"""
    logger.info(f"単一試合テスト開始: {match_id}")
    
    try:
        collector = RealtimeDataCollector(RIOT_API_KEY, MYSQL_CONFIG, RIOT_REGION)
        
        # 静的データをセットアップ
        if not collector.setup_static_data():
            logger.error("静的データセットアップに失敗")
            return False
        
        # 試合データを収集
        success = collector.collect_match_with_timeline(match_id)
        
        if success:
            logger.info("単一試合テスト成功")
            
            # 結果を表示
            stats = collector.get_collection_stats()
            logger.info(f"ソロキル数: {stats.get('solo_kills_found', 0)}")
            logger.info(f"対面データ数: {stats.get('matchups_created', 0)}")
            
            return True
        else:
            logger.error("単一試合テスト失敗")
            return False
        
    except Exception as e:
        logger.error(f"単一試合テストエラー: {e}")
        return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='LOLリアルタイム勝率予測システム データ収集')
    parser.add_argument('--mode', type=str, choices=['test', 'small', 'full', 'match'], 
                       default='interactive', help='実行モード')
    parser.add_argument('--tier', type=str, choices=['CHALLENGER', 'GRANDMASTER', 'MASTER', 'ALL'], 
                       default='ALL', help='収集対象ティア')
    parser.add_argument('--players', type=int, default=50, help='プレイヤー数')
    parser.add_argument('--matches', type=int, default=20, help='プレイヤーあたりの試合数')
    parser.add_argument('--match-id', type=str, help='単一試合テスト用の試合ID')
    
    args = parser.parse_args()
    
    logger.info("LOLリアルタイム勝率予測システム データ収集開始")
    logger.info(f"開始時刻: {datetime.now()}")
    
    # 前提条件チェック
    if not check_prerequisites():
        logger.error("前提条件チェックに失敗しました。終了します。")
        sys.exit(1)
    
    # 実行モード処理
    if args.mode == 'interactive':
        # インタラクティブモード
        print("\n実行モードを選択してください:")
        print("1. 小規模テスト（3人のプレイヤーから5試合ずつ）")
        print("2. 本格的なデータ収集（大量データ）")
        print("3. 単一試合テスト")
        print("4. 終了")
        
        while True:
            try:
                choice = input("\n選択してください (1-4): ").strip()
                
                if choice == '1':
                    logger.info("小規模テストモードを選択")
                    if run_small_test():
                        logger.info("小規模テスト完了")
                    else:
                        logger.error("小規模テスト失敗")
                    break
                    
                elif choice == '2':
                    logger.info("本格的なデータ収集モードを選択")
                    
                    print(f"\n設定:")
                    print(f"対象ティア: {args.tier}")
                    print(f"プレイヤー数: {args.players}")
                    print(f"プレイヤーあたり試合数: {args.matches}")
                    
                    confirm = input("続行しますか？ (y/N): ").strip().lower()
                    
                    if confirm in ['y', 'yes']:
                        if run_full_collection(args.tier, args.players, args.matches):
                            logger.info("本格的なデータ収集完了")
                        else:
                            logger.error("本格的なデータ収集失敗")
                    else:
                        logger.info("データ収集をキャンセルしました")
                    break
                    
                elif choice == '3':
                    match_id = input("試合IDを入力してください: ").strip()
                    if match_id:
                        if run_single_match_test(match_id):
                            logger.info("単一試合テスト完了")
                        else:
                            logger.error("単一試合テスト失敗")
                    break
                    
                elif choice == '4':
                    logger.info("終了します")
                    break
                    
                else:
                    print("無効な選択です。1-4を入力してください。")
                    
            except KeyboardInterrupt:
                logger.info("ユーザーによって中断されました")
                break
            except Exception as e:
                logger.error(f"入力エラー: {e}")
                continue
    
    elif args.mode == 'test':
        run_small_test()
    elif args.mode == 'small':
        run_small_test()
    elif args.mode == 'full':
        run_full_collection(args.tier, args.players, args.matches)
    elif args.mode == 'match':
        if args.match_id:
            run_single_match_test(args.match_id)
        else:
            logger.error("--match-id が必要です")
    
    logger.info(f"LOLリアルタイム勝率予測システム データ収集終了: {datetime.now()}")

if __name__ == "__main__":
    main()

