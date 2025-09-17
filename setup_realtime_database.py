"""
Database Setup Script for LOL Realtime Winrate System
リアルタイム勝率予測システムのデータベースセットアップスクリプト
"""

import mysql.connector
from mysql.connector import Error
import logging
import sys
from pathlib import Path
from config import MYSQL_CONFIG

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database_if_not_exists(config: dict) -> bool:
    """データベースが存在しない場合は作成"""
    try:
        # データベース名を一時的に除去
        temp_config = config.copy()
        database_name = temp_config.pop('database')
        
        # MySQL接続（データベース指定なし）
        connection = mysql.connector.connect(**temp_config)
        cursor = connection.cursor()
        
        # データベースの存在確認
        cursor.execute(f"SHOW DATABASES LIKE '{database_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            # データベース作成
            cursor.execute(f"""
                CREATE DATABASE {database_name} 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
            logger.info(f"データベースを作成しました: {database_name}")
        else:
            logger.info(f"データベースは既に存在します: {database_name}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        logger.error(f"データベース作成エラー: {e}")
        return False

def execute_sql_file(config: dict, sql_file_path: str) -> bool:
    """SQLファイルを実行"""
    try:
        # SQLファイルの存在確認
        sql_path = Path(sql_file_path)
        if not sql_path.exists():
            logger.error(f"SQLファイルが見つかりません: {sql_file_path}")
            return False
        
        # SQLファイルを読み込み
        with open(sql_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # MySQL接続
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # SQLを実行（複数のステートメントに分割）
        statements = []
        current_statement = ""
        in_delimiter = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # コメント行をスキップ
            if line.startswith('--') or not line:
                continue
            
            # DELIMITER処理
            if line.startswith('DELIMITER'):
                in_delimiter = True
                continue
            elif line == '$$' and in_delimiter:
                in_delimiter = False
                if current_statement.strip():
                    statements.append(current_statement.strip())
                    current_statement = ""
                continue
            
            current_statement += line + "\n"
            
            # セミコロンで終わる場合（DELIMITER外）
            if line.endswith(';') and not in_delimiter:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                    current_statement = ""
        
        # 残りのステートメントを追加
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # ステートメントを実行
        executed_count = 0
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                # 複数のクエリを含む場合は分割実行
                if statement.count(';') > 1:
                    for sub_statement in statement.split(';'):
                        sub_statement = sub_statement.strip()
                        if sub_statement:
                            cursor.execute(sub_statement)
                else:
                    cursor.execute(statement)
                
                executed_count += 1
                logger.debug(f"ステートメント実行完了: {i+1}/{len(statements)}")
                
            except Error as e:
                logger.warning(f"ステートメント実行エラー (継続): {e}")
                logger.debug(f"問題のあるステートメント: {statement[:100]}...")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f"SQLファイル実行完了: {executed_count}/{len(statements)}ステートメント成功")
        return True
        
    except Error as e:
        logger.error(f"SQLファイル実行エラー: {e}")
        return False
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return False

def verify_database_setup(config: dict) -> bool:
    """データベースセットアップの検証"""
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 主要テーブルの存在確認
        required_tables = [
            'game_versions', 'champions', 'items', 'matches', 
            'participants', 'matchups', 'solo_kills', 'kill_items',
            'timeline_events', 'realtime_winrate_stats', 'ml_models',
            'realtime_predictions'
        ]
        
        existing_tables = []
        for table in required_tables:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if cursor.fetchone():
                existing_tables.append(table)
        
        cursor.close()
        connection.close()
        
        logger.info(f"テーブル確認: {len(existing_tables)}/{len(required_tables)}個存在")
        
        if len(existing_tables) == len(required_tables):
            logger.info("データベースセットアップ検証成功")
            return True
        else:
            missing_tables = set(required_tables) - set(existing_tables)
            logger.warning(f"不足しているテーブル: {missing_tables}")
            return False
        
    except Error as e:
        logger.error(f"データベース検証エラー: {e}")
        return False

def setup_realtime_database() -> bool:
    """リアルタイムデータベースの完全セットアップ"""
    logger.info("リアルタイムデータベースのセットアップを開始...")
    
    try:
        # 1. データベース作成
        if not create_database_if_not_exists(MYSQL_CONFIG):
            logger.error("データベース作成に失敗")
            return False
        
        # 2. スキーマ適用
        schema_file = "database_schema_realtime.sql"
        if not execute_sql_file(MYSQL_CONFIG, schema_file):
            logger.error("スキーマ適用に失敗")
            return False
        
        # 3. セットアップ検証
        if not verify_database_setup(MYSQL_CONFIG):
            logger.error("データベース検証に失敗")
            return False
        
        logger.info("リアルタイムデータベースのセットアップが完了しました")
        return True
        
    except Exception as e:
        logger.error(f"データベースセットアップエラー: {e}")
        return False

def reset_database() -> bool:
    """データベースをリセット（全データ削除）"""
    logger.warning("データベースリセットを開始...")
    
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # 外部キー制約を無効化
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 全テーブルを削除
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            logger.info(f"テーブル削除: {table_name}")
        
        # 外部キー制約を有効化
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("データベースリセット完了")
        return True
        
    except Error as e:
        logger.error(f"データベースリセットエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("LOL リアルタイム勝率予測システム - データベースセットアップ")
    print("=" * 60)
    
    # 設定確認
    print(f"データベース: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}")
    print(f"ユーザー: {MYSQL_CONFIG['user']}")
    
    # 実行モード選択
    print("\n実行モードを選択してください:")
    print("1. 新規セットアップ（推奨）")
    print("2. スキーマのみ再適用")
    print("3. データベースリセット（全データ削除）")
    print("4. セットアップ検証のみ")
    print("5. 終了")
    
    while True:
        try:
            choice = input("\n選択してください (1-5): ").strip()
            
            if choice == '1':
                logger.info("新規セットアップを開始...")
                if setup_realtime_database():
                    print("\n✅ データベースセットアップが完了しました！")
                    print("次のステップ: python realtime_data_collector.py を実行してデータ収集を開始")
                else:
                    print("\n❌ データベースセットアップに失敗しました")
                break
                
            elif choice == '2':
                logger.info("スキーマ再適用を開始...")
                if execute_sql_file(MYSQL_CONFIG, "database_schema_realtime.sql"):
                    print("\n✅ スキーマ適用が完了しました！")
                else:
                    print("\n❌ スキーマ適用に失敗しました")
                break
                
            elif choice == '3':
                confirm = input("⚠️  全データが削除されます。続行しますか？ (y/N): ").strip().lower()
                if confirm in ['y', 'yes']:
                    if reset_database():
                        print("\n✅ データベースリセットが完了しました")
                        # リセット後に新規セットアップ
                        if setup_realtime_database():
                            print("✅ 新規セットアップも完了しました！")
                    else:
                        print("\n❌ データベースリセットに失敗しました")
                else:
                    print("リセットをキャンセルしました")
                break
                
            elif choice == '4':
                logger.info("セットアップ検証を開始...")
                if verify_database_setup(MYSQL_CONFIG):
                    print("\n✅ データベース検証成功！")
                else:
                    print("\n❌ データベース検証に失敗しました")
                break
                
            elif choice == '5':
                print("終了します")
                break
                
            else:
                print("無効な選択です。1-5を入力してください。")
                
        except KeyboardInterrupt:
            print("\n\n中断されました")
            break
        except Exception as e:
            logger.error(f"入力エラー: {e}")
            continue

if __name__ == "__main__":
    main()

