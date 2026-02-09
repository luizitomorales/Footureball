# models.py
# -*- coding: utf-8 -*-
"""
Módulo de ML/DL para o projeto preditivo de futebol.
Alinhado à lógica definida: targets principais (resultado FT, BTTS, Over/Under 2.5,
primeiro a marcar, cartões), uso de features de momento e retrospecto (índices
ofensivo/defensivo, momentum, comparativos), calibração de probabilidades e
persistência dos modelos. (Ref.: lógica consolidada no doc do projeto)

Observações:
- Evita vazamento temporal: as features devem ser calculadas **antes** do jogo.
- Probabilidades calibradas (Platt/Isotônica) quando aplicável.
- Persistência via joblib em ./artifacts/models

Autor: Luiz + Copilot
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss, classification_report
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

try:
    import xgboost as xgb
    _HAVE_XGB = True
except Exception:
    _HAVE_XGB = False


SUPPORTED_TARGETS = {
    # multiclasse: 0 = Away, 1 = Draw, 2 = Home
    'match_result': {'type': 'multiclass'},
    # binários
    'btts': {'type': 'binary'},             # ambos marcam
    'over_2_5': {'type': 'binary'},         # total gols > 2.5
    'first_goal': {'type': 'binary'},       # 1 = home, 0 = away (jogos com gol)
    'cards_over_4_5': {'type': 'binary'}    # total de cartões > 4.5
}

DEFAULT_FEATURES_CORE = [
    # momento (normalizados 0-1)
    'home_momentum', 'away_momentum', 'momentum_balance',
    # eficiência
    'home_offensive_eff', 'away_offensive_eff',
    'home_defensive_eff', 'away_defensive_eff',
    'offensive_balance', 'defensive_balance',
    # médias recentes
    'home_avg_goals_scored', 'home_avg_goals_conceded',
    'away_avg_goals_scored', 'away_avg_goals_conceded',
    # confrontos diretos
    'direct_avg_goals_home', 'direct_avg_goals_away', 'direct_avg_points_home',
    # contexto simples
    'league_position_diff'
]

ODDS_FEATURES = ['odds_home_win', 'odds_draw', 'odds_away_win', 'odds_margin', 'home_ev', 'draw_ev', 'away_ev']

@dataclass
class ModelArtifacts:
    model: object
    scaler: Optional[StandardScaler]
    features: List[str]
    classes_: Optional[np.ndarray]


class FootballModels:
    def __init__(self, models_dir: str = 'artifacts/models'):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.registry: Dict[str, ModelArtifacts] = {}

    # ------------------------- Preparação de dados ------------------------- #
    def _split_xy(self, df: pd.DataFrame, target_name: str, feature_cols: Optional[List[str]] = None):
        if target_name not in SUPPORTED_TARGETS:
            raise ValueError(f"Target não suportado: {target_name}")
        if feature_cols is None:
            # inclui odds se existirem
            feature_cols = [c for c in (DEFAULT_FEATURES_CORE + ODDS_FEATURES) if c in df.columns]
        X = df[feature_cols].copy()
        y = self._derive_target(df, target_name)
        return X, y, feature_cols

    def _derive_target(self, df: pd.DataFrame, target_name: str) -> np.ndarray:
        if target_name == 'match_result':
            # 0 Away, 1 Draw, 2 Home
            return df.apply(lambda r: 2 if r['home_score'] > r['away_score'] else (1 if r['home_score'] == r['away_score'] else 0), axis=1).values
        elif target_name == 'btts':
            return ( (df['home_score'] > 0) & (df['away_score'] > 0) ).astype(int).values
        elif target_name == 'over_2_5':
            return ((df['home_score'] + df['away_score']) > 2.5).astype(int).values
        elif target_name == 'first_goal':
            # Espera coluna opcional first_goal_team (nome do time). Filtra jogos sem gol.
            m = df[(df['home_score'] + df['away_score']) > 0].copy()
            return (m['first_goal_team'] == m['home_team']).astype(int).values
        elif target_name == 'cards_over_4_5':
            total = df.get('home_yellow_cards', 0) + df.get('away_yellow_cards', 0) + df.get('home_red_cards', 0) + df.get('away_red_cards', 0)
            return (total > 4.5).astype(int).values
        else:
            raise ValueError(target_name)

    # ---------------------------- Treinamento ------------------------------ #
    def fit(self, df: pd.DataFrame, target_name: str, feature_cols: Optional[List[str]] = None,
            algorithm: str = 'xgb', test_size: float = 0.2, random_state: int = 42, calibrate: bool = True) -> Dict:
        X, y, feature_cols = self._split_xy(df, target_name, feature_cols)
        scaler = StandardScaler()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        model = self._make_model(algorithm, problem_type='binary' if len(np.unique(y))==2 else 'multiclass')
        model.fit(X_train_s, y_train)

        # calibração (apenas classificação)
        if calibrate:
            try:
                model = CalibratedClassifierCV(model, method='sigmoid', cv=5)
                model.fit(X_train_s, y_train)
            except Exception:
                pass

        y_pred = model.predict(X_test_s)
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred))
        }
        try:
            proba = model.predict_proba(X_test_s)
            if proba.shape[1] == 2:
                p = proba[:,1]
                metrics['logloss'] = float(log_loss(y_test, proba, labels=[0,1]))
                metrics['brier'] = float(brier_score_loss(y_test, p))
            else:
                metrics['logloss'] = float(log_loss(y_test, proba))
        except Exception:
            pass

        self.registry[target_name] = ModelArtifacts(model=model, scaler=scaler, features=feature_cols, classes_=getattr(model, 'classes_', None))
        return metrics

    def _make_model(self, algorithm: str, problem_type: str):
        if algorithm == 'xgb' and _HAVE_XGB:
            if problem_type == 'binary':
                return xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.9, colsample_bytree=0.9, random_state=42)
            else:
                return xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', num_class=3, n_estimators=400, learning_rate=0.05, max_depth=6, subsample=0.9, colsample_bytree=0.9, random_state=42)
        if algorithm == 'rf':
            return RandomForestClassifier(n_estimators=400, max_depth=None, random_state=42, n_jobs=-1)
        if algorithm == 'gbt':
            return GradientBoostingClassifier(random_state=42)
        # fallback
        return LogisticRegression(max_iter=2000, multi_class='auto')

    # ----------------------------- Inferência ------------------------------ #
    def predict(self, df_features: pd.DataFrame, target_name: str) -> pd.DataFrame:
        art = self.registry.get(target_name) or self._load_artifact(target_name)
        if art is None:
            raise FileNotFoundError(f"Modelo não encontrado para {target_name}")
        X = df_features[art.features].copy()
        Xs = art.scaler.transform(X) if art.scaler else X.values
        proba = None
        try:
            proba = art.model.predict_proba(Xs)
        except Exception:
            pass
        pred = art.model.predict(Xs)
        out = df_features.copy()
        out[f'{target_name}_pred'] = pred
        if proba is not None:
            if proba.shape[1] == 2:
                out[f'{target_name}_proba_1'] = proba[:,1]
                out[f'{target_name}_proba_0'] = proba[:,0]
            else:
                # ordem: classes_ (0,1,2) = Away, Draw, Home
                for i, cls in enumerate(art.classes_):
                    out[f'{target_name}_proba_{int(cls)}'] = proba[:, i]
        return out

    # --------------------------- Persistência ------------------------------ #
    def save(self, target_name: str):
        art = self.registry[target_name]
        joblib.dump(art, os.path.join(self.models_dir, f'{target_name}.joblib'))

    def load(self, target_name: str):
        art = self._load_artifact(target_name)
        self.registry[target_name] = art
        return art

    def _load_artifact(self, target_name: str) -> Optional[ModelArtifacts]:
        path = os.path.join(self.models_dir, f'{target_name}.joblib')
        if not os.path.exists(path):
            return None
        return joblib.load(path)


if __name__ == '__main__':
    print('Módulo de modelos carregado. Consulte a classe FootballModels.')
