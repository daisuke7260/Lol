-- League of Legends リアルタイム勝率予測システム
-- ソロキル情報を含む詳細データベーススキーマ

-- ゲームバージョン管理テーブル
CREATE TABLE game_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    release_date DATE,
    is_active TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- チャンピオン情報テーブル
CREATE TABLE champions (
    id INT PRIMARY KEY,
    key_name VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    title VARCHAR(200),
    tags JSON,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_champions_version (version),
    INDEX idx_champions_name (name),
    FOREIGN KEY (version) REFERENCES game_versions(version) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- アイテム情報テーブル
CREATE TABLE items (
    id INT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    gold_base INT DEFAULT 0,
    gold_total INT DEFAULT 0,
    gold_sell INT DEFAULT 0,
    tags JSON,
    stats JSON,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_items_version (version),
    FOREIGN KEY (version) REFERENCES game_versions(version) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 試合情報テーブル
CREATE TABLE matches (
    match_id VARCHAR(100) PRIMARY KEY,
    game_creation BIGINT NOT NULL,
    game_duration INT NOT NULL,
    game_end_timestamp BIGINT,
    game_mode VARCHAR(50),
    game_type VARCHAR(50),
    game_version VARCHAR(50) NOT NULL,
    map_id INT,
    platform_id VARCHAR(20),
    queue_id INT,
    tournament_code VARCHAR(100),
    has_timeline TINYINT(1) DEFAULT 0, -- タイムラインデータの有無
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_matches_game_version (game_version),
    INDEX idx_matches_queue_id (queue_id),
    INDEX idx_matches_game_creation (game_creation),
    INDEX idx_matches_has_timeline (has_timeline),
    FOREIGN KEY (game_version) REFERENCES game_versions(version) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 参加者情報テーブル
CREATE TABLE participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id VARCHAR(100) NOT NULL,
    puuid VARCHAR(100) NOT NULL,
    participant_id INT NOT NULL,
    champion_id INT NOT NULL,
    champion_name VARCHAR(100) NOT NULL,
    champion_level INT NOT NULL,
    lane VARCHAR(20),
    team_position VARCHAR(20),
    team_id INT NOT NULL,
    
    -- アイテム情報（最終）
    item0 INT DEFAULT 0,
    item1 INT DEFAULT 0,
    item2 INT DEFAULT 0,
    item3 INT DEFAULT 0,
    item4 INT DEFAULT 0,
    item5 INT DEFAULT 0,
    item6 INT DEFAULT 0,
    
    -- 経済情報
    gold_earned INT DEFAULT 0,
    gold_spent INT DEFAULT 0,
    
    -- 戦績情報
    kills INT DEFAULT 0,
    deaths INT DEFAULT 0,
    assists INT DEFAULT 0,
    win TINYINT(1) NOT NULL,
    
    -- ダメージ情報
    total_damage_dealt INT DEFAULT 0,
    total_damage_dealt_to_champions INT DEFAULT 0,
    total_damage_taken INT DEFAULT 0,
    magic_damage_dealt INT DEFAULT 0,
    physical_damage_dealt INT DEFAULT 0,
    true_damage_dealt INT DEFAULT 0,
    
    -- CS情報
    total_minions_killed INT DEFAULT 0,
    neutral_minions_killed INT DEFAULT 0,
    
    -- ビジョン情報
    vision_score INT DEFAULT 0,
    wards_placed INT DEFAULT 0,
    wards_killed INT DEFAULT 0,
    
    -- その他の統計
    largest_killing_spree INT DEFAULT 0,
    largest_multi_kill INT DEFAULT 0,
    longest_time_spent_living INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_participants_match_id (match_id),
    INDEX idx_participants_puuid (puuid),
    INDEX idx_participants_champion_id (champion_id),
    INDEX idx_participants_lane (lane),
    UNIQUE KEY unique_match_participant (match_id, participant_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (champion_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 対面データテーブル（基本情報）
CREATE TABLE matchups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id VARCHAR(100) NOT NULL,
    lane VARCHAR(20) NOT NULL,
    
    -- プレイヤー1情報
    player1_puuid VARCHAR(100) NOT NULL,
    player1_participant_id INT NOT NULL,
    player1_champion_id INT NOT NULL,
    player1_champion_name VARCHAR(100) NOT NULL,
    player1_level INT NOT NULL,
    player1_team_id INT NOT NULL,
    
    -- プレイヤー2情報
    player2_puuid VARCHAR(100) NOT NULL,
    player2_participant_id INT NOT NULL,
    player2_champion_id INT NOT NULL,
    player2_champion_name VARCHAR(100) NOT NULL,
    player2_level INT NOT NULL,
    player2_team_id INT NOT NULL,
    
    -- BOTレーン用追加プレイヤー情報
    player3_puuid VARCHAR(100) NULL, -- BOTレーンのサポート1
    player3_participant_id INT NULL,
    player3_champion_id INT NULL,
    player3_champion_name VARCHAR(100) NULL,
    player3_level INT NULL,
    player3_team_id INT NULL,
    
    player4_puuid VARCHAR(100) NULL, -- BOTレーンのサポート2
    player4_participant_id INT NULL,
    player4_champion_id INT NULL,
    player4_champion_name VARCHAR(100) NULL,
    player4_level INT NULL,
    player4_team_id INT NULL,
    
    -- 計算済み特徴量
    level_diff INT,
    gold_diff INT,
    item_gold_diff INT,
    cs_diff INT,
    kda_diff DECIMAL(10,3),
    
    -- 勝敗情報
    player1_win TINYINT(1) NOT NULL,
    player2_win TINYINT(1) NOT NULL,
    
    -- 試合情報
    game_duration INT NOT NULL,
    game_version VARCHAR(50) NOT NULL,
    game_creation BIGINT NOT NULL,
    
    -- ソロキル統計
    total_solo_kills INT DEFAULT 0,
    first_blood_time INT DEFAULT 0, -- ファーストブラッド時間（ミリ秒）
    first_blood_killer_participant_id INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_matchups_champions (player1_champion_id, player2_champion_id),
    INDEX idx_matchups_lane (lane),
    INDEX idx_matchups_game_version (game_version),
    INDEX idx_matchups_level_diff (level_diff),
    INDEX idx_matchups_gold_diff (gold_diff),
    INDEX idx_matchups_solo_kills (total_solo_kills),
    UNIQUE KEY unique_match_lane (match_id, lane),
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (player1_champion_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (player2_champion_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ソロキル詳細テーブル（新規）
CREATE TABLE solo_kills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id VARCHAR(100) NOT NULL,
    matchup_id INT NOT NULL,
    
    -- キル基本情報
    timestamp_ms BIGINT NOT NULL, -- キル発生時間（ミリ秒）
    game_time_seconds INT NOT NULL, -- ゲーム内時間（秒）
    
    -- キラー情報
    killer_participant_id INT NOT NULL,
    killer_champion_id INT NOT NULL,
    killer_champion_name VARCHAR(100) NOT NULL,
    killer_level INT NOT NULL,
    killer_gold INT NOT NULL,
    killer_position_x INT,
    killer_position_y INT,
    
    -- 被キル者情報
    victim_participant_id INT NOT NULL,
    victim_champion_id INT NOT NULL,
    victim_champion_name VARCHAR(100) NOT NULL,
    victim_level INT NOT NULL,
    victim_gold INT NOT NULL,
    victim_position_x INT,
    victim_position_y INT,
    
    -- レベル・ゴールド差
    level_diff INT, -- killer - victim
    gold_diff INT,  -- killer - victim
    
    -- キル種別
    is_first_blood TINYINT(1) DEFAULT 0,
    is_shutdown TINYINT(1) DEFAULT 0,
    bounty_gold INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_solo_kills_match_id (match_id),
    INDEX idx_solo_kills_matchup_id (matchup_id),
    INDEX idx_solo_kills_timestamp (timestamp_ms),
    INDEX idx_solo_kills_game_time (game_time_seconds),
    INDEX idx_solo_kills_killer (killer_participant_id),
    INDEX idx_solo_kills_victim (victim_participant_id),
    INDEX idx_solo_kills_level_diff (level_diff),
    INDEX idx_solo_kills_gold_diff (gold_diff),
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (matchup_id) REFERENCES matchups(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (killer_champion_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (victim_champion_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- キル時アイテム情報テーブル（新規）
CREATE TABLE kill_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    solo_kill_id INT NOT NULL,
    participant_id INT NOT NULL,
    participant_type ENUM('killer', 'victim') NOT NULL,
    
    -- アイテム情報
    item0 INT DEFAULT 0,
    item1 INT DEFAULT 0,
    item2 INT DEFAULT 0,
    item3 INT DEFAULT 0,
    item4 INT DEFAULT 0,
    item5 INT DEFAULT 0,
    item6 INT DEFAULT 0,
    
    -- アイテム価値
    total_item_value INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_kill_items_solo_kill_id (solo_kill_id),
    INDEX idx_kill_items_participant (participant_id),
    INDEX idx_kill_items_type (participant_type),
    FOREIGN KEY (solo_kill_id) REFERENCES solo_kills(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- タイムライン詳細テーブル（新規）
CREATE TABLE timeline_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    match_id VARCHAR(100) NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    
    -- 参加者情報
    participant_id INT,
    killer_id INT,
    victim_id INT,
    assisting_participant_ids JSON,
    
    -- 位置情報
    position_x INT,
    position_y INT,
    
    -- イベント詳細（JSON形式）
    event_data JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_timeline_match_id (match_id),
    INDEX idx_timeline_timestamp (timestamp_ms),
    INDEX idx_timeline_event_type (event_type),
    INDEX idx_timeline_participant (participant_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- リアルタイム勝率統計テーブル（新規）
CREATE TABLE realtime_winrate_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    champion1_id INT NOT NULL,
    champion2_id INT NOT NULL,
    lane VARCHAR(20) NOT NULL,
    game_version VARCHAR(50) NOT NULL,
    
    -- 基本統計
    total_matchups INT DEFAULT 0,
    champion1_wins INT DEFAULT 0,
    champion2_wins INT DEFAULT 0,
    champion1_winrate DECIMAL(5,2) DEFAULT 0.0,
    champion2_winrate DECIMAL(5,2) DEFAULT 0.0,
    
    -- ソロキル統計
    total_solo_kills INT DEFAULT 0,
    champion1_solo_kills INT DEFAULT 0,
    champion2_solo_kills INT DEFAULT 0,
    champion1_solo_kill_rate DECIMAL(5,2) DEFAULT 0.0,
    champion2_solo_kill_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- 時間別統計
    avg_first_kill_time INT DEFAULT 0, -- 平均ファーストキル時間
    early_game_kills INT DEFAULT 0,    -- 序盤キル数（0-15分）
    mid_game_kills INT DEFAULT 0,      -- 中盤キル数（15-25分）
    late_game_kills INT DEFAULT 0,     -- 終盤キル数（25分以降）
    
    -- レベル・ゴールド差統計
    avg_level_diff_at_first_kill DECIMAL(5,2) DEFAULT 0.0,
    avg_gold_diff_at_first_kill DECIMAL(10,2) DEFAULT 0.0,
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_realtime_stats_champions (champion1_id, champion2_id),
    INDEX idx_realtime_stats_lane (lane),
    INDEX idx_realtime_stats_version (game_version),
    INDEX idx_realtime_stats_updated (last_updated),
    UNIQUE KEY unique_realtime_matchup (champion1_id, champion2_id, lane, game_version),
    FOREIGN KEY (champion1_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (champion2_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (game_version) REFERENCES game_versions(version) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 機械学習モデル情報テーブル（拡張）
CREATE TABLE ml_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    game_version VARCHAR(50) NOT NULL,
    
    -- モデル性能指標
    accuracy DECIMAL(10,6),
    precision_score DECIMAL(10,6),
    recall_score DECIMAL(10,6),
    f1_score DECIMAL(10,6),
    auc_score DECIMAL(10,6),
    
    -- 学習データ情報
    training_samples INT,
    validation_samples INT,
    test_samples INT,
    solo_kill_samples INT, -- ソロキルデータ数
    
    -- 特徴量情報
    uses_solo_kills TINYINT(1) DEFAULT 0,
    uses_timeline_data TINYINT(1) DEFAULT 0,
    feature_importance JSON,
    
    -- モデルファイルパス
    model_file_path VARCHAR(500),
    
    is_active TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ml_models_active (is_active),
    INDEX idx_ml_models_type_version (model_type, game_version),
    FOREIGN KEY (game_version) REFERENCES game_versions(version) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- リアルタイム予測結果テーブル（新規）
CREATE TABLE realtime_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT NOT NULL,
    
    -- 入力特徴量
    champion1_id INT NOT NULL,
    champion2_id INT NOT NULL,
    lane VARCHAR(20) NOT NULL,
    
    -- ゲーム状況
    game_time_seconds INT NOT NULL,
    level_diff INT,
    gold_diff INT,
    cs_diff INT,
    
    -- ソロキル情報
    solo_kills_champion1 INT DEFAULT 0,
    solo_kills_champion2 INT DEFAULT 0,
    last_kill_time INT DEFAULT 0,
    
    -- 予測結果
    predicted_winrate DECIMAL(5,2) NOT NULL,
    confidence_score DECIMAL(5,2),
    prediction_factors JSON, -- 予測に影響した要因
    
    -- 実際の結果（後で更新）
    actual_result TINYINT(1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_realtime_predictions_model_id (model_id),
    INDEX idx_realtime_predictions_champions (champion1_id, champion2_id),
    INDEX idx_realtime_predictions_game_time (game_time_seconds),
    INDEX idx_realtime_predictions_created_at (created_at),
    FOREIGN KEY (model_id) REFERENCES ml_models(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (champion1_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (champion2_id) REFERENCES champions(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- トリガー作成
-- ゲームバージョンが挿入された時に自動的にis_activeを更新
DELIMITER $$

CREATE TRIGGER update_active_version
AFTER INSERT ON game_versions
FOR EACH ROW
BEGIN
    UPDATE game_versions SET is_active = 0 WHERE version != NEW.version;
    UPDATE game_versions SET is_active = 1 WHERE version = NEW.version;
END$$

-- ソロキルが挿入された時にmatchupsテーブルの統計を更新
CREATE TRIGGER update_matchup_solo_kill_stats
AFTER INSERT ON solo_kills
FOR EACH ROW
BEGIN
    UPDATE matchups 
    SET total_solo_kills = total_solo_kills + 1,
        first_blood_time = CASE 
            WHEN first_blood_time = 0 OR NEW.timestamp_ms < first_blood_time 
            THEN NEW.timestamp_ms 
            ELSE first_blood_time 
        END,
        first_blood_killer_participant_id = CASE 
            WHEN first_blood_time = 0 OR NEW.timestamp_ms < first_blood_time 
            THEN NEW.killer_participant_id 
            ELSE first_blood_killer_participant_id 
        END
    WHERE id = NEW.matchup_id;
END$$

-- リアルタイム統計の自動更新トリガー
CREATE TRIGGER update_realtime_stats_timestamp
BEFORE UPDATE ON realtime_winrate_stats
FOR EACH ROW
BEGIN
    SET NEW.last_updated = CURRENT_TIMESTAMP;
END$$

DELIMITER ;

-- 初期設定
SET FOREIGN_KEY_CHECKS = 1;
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

