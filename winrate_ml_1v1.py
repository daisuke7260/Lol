"""ランダムフォレストで1v1勝率予測モデルを学習する簡易スクリプト

使い方:
  1. 仮想環境を作成し依存をインストール: `pip install -r requirements.txt`
  2. `config.py` に正しい `MYSQL_CONFIG` を設定
  3. このスクリプトを実行: `python winrate_ml_1v1.py`

- データは `RealtimeDatabaseManager.select_training_data` を使って取得します。
- 最小の前処理（欠損処理・カテゴリ変換）を行い、RandomForestClassifier を学習します。
- 学習済みモデルは `models/rf_1v1.joblib` に保存されます。
"""

import os
import logging
from typing import Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from imblearn.over_sampling import SMOTE
from database_manager_realtime import RealtimeDatabaseManager
from config import MYSQL_CONFIG

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


class WinrateML1v1Trainer:
    def __init__(self, mysql_config: Dict):
        self.db = RealtimeDatabaseManager(**mysql_config)

    def load_data(self, limit: int = 100, mychampion: int = 30, enemyChampion: int = 143) -> pd.DataFrame:
        """DB から学習データを取得して DataFrame に変換する。"""
        rows = self.db.select_training_data(limit=limit, mychampion=mychampion, enemyChampion=enemyChampion)
        if not rows:
            logger.warning("学習データが見つかりませんでした。")
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        logger.info(f"読み込んだ行数: {len(df)}")

        return df

    def preprocess(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """最小限の前処理: 欠損を埋め、必要な特徴量を選択する

        期待される列（サンプル）:
          - P1_killer_champion_id, P2_victim_champion_id, P1_total_gold_value, P2_total_gold_value, Win_Judgment
        Win_Judgment は 'P1'/'P2' でどちらが勝ったかを示すため、ターゲットを作る。
        """
        if df.empty:
            return df, pd.Series([], dtype=int), []

        # ターゲット: P1 が勝ったら 1, そうでなければ 0
        df['target'] = (df.get('Win_Judgment') == 'P1').astype(int)

        # 代表的な数値特徴量を抽出（存在しない列は無視）
        numeric_cols = []
        candidates = [
            'P1_total_gold_value', 'P2_total_gold_value',
            'P1_killer_level', 'P2_killer_level',
            'P1_item0', 'P1_item1', 'P1_item2', 'P1_item3', 'P1_item4', 'P1_item5', 'P1_item6',
            'P2_item0', 'P2_item1', 'P2_item2', 'P2_item3', 'P2_item4', 'P2_item5', 'P2_item6'
        ]
        for c in candidates:
            if c in df.columns:
                numeric_cols.append(c)

        if not numeric_cols:
            logger.error('数値特徴量が見つかりません。データのカラムを確認してください。')
            return df, pd.Series([], dtype=int), []

        X = df[numeric_cols].copy()
        print("★★")
        print(X.columns)
        print("★★")
        # 列ごとに確実に数値化してから欠損を埋める
        for c in X.columns:
            X[c] = pd.to_numeric(X[c], errors='coerce').fillna(0)

        y = df['target']
        # 学習に渡す最終的なカラム順を明示的に保存
        feature_names = list(X.columns)
        return X, y, feature_names

    def train(self, X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
        """ランダムフォレストを学習し、モデルを返す"""
        if X.empty or y.size == 0:
            raise ValueError('学習データが不十分です')

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )
        logger.info(f"SMOTE適用前の学習データ数: {len(y_train)}, クラス比率: {np.bincount(y_train)}")
        smote = SMOTE(random_state=42)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
        logger.info(f"SMOTE適用後の学習データ数: {len(y_train_resampled)}, クラス比率: {np.bincount(y_train_resampled)}")
        logger.info("不均衡データ対策として class_weight='balanced' を設定します。")
        clf = RandomForestClassifier(
            n_estimators=100,
            n_jobs=-1,
            random_state=42,
            #class_weight='balanced'
        )
        clf.fit(X_train, y_train)
        clf.fit(X_train_resampled, y_train_resampled) # <- 修正後の行

        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        logger.info(f'検証 Accuracy: {acc:.4f}')

        # 可能なら AUC も計算
        try:
            if hasattr(clf, 'predict_proba'):
                auc = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])
                logger.info(f'検証 AUC: {auc:.4f}')
        except Exception:
            logger.debug('AUC の計算に失敗しました（恐らく単一クラスなど）')

        logger.info('分類レポート:\n' + classification_report(y_test, y_pred))
        return clf

    def save_model(self, clf: RandomForestClassifier, feature_names: List[str], path: str = None):
        path = path or os.path.join(MODEL_DIR, 'rf_1v1.joblib')
        meta = {'model': clf, 'features': feature_names}
        joblib.dump(meta, path)
        logger.info(f'モデルを保存しました: {path}')

def main():
    trainer = WinrateML1v1Trainer(MYSQL_CONFIG)

    # データを取得（必要に応じて mychampion/enemyChampion を指定）
    df = trainer.load_data(limit=10000, mychampion=126, enemyChampion=157)
    if df.empty:
        logger.error('学習データが空です。終了します。')
        return

    X, y, features = trainer.preprocess(df)
    if y.size == 0 or X.empty:
        logger.error('前処理後のデータが不十分です。終了します。')
        return

    clf = trainer.train(X, y)
    trainer.save_model(clf, features)
if __name__ == '__main__':
    main()
