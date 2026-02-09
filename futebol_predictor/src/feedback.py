# feedback.py
# -*- coding: utf-8 -*-
"""
Feedback loop:
- Consolida resultados reais pós-jogo
- Mede calibração (Brier), logloss e acurácia por faixa/competição
- Gera dataset de re-treinamento incremental
"""
from typing import Dict
from datetime import datetime
import os
import pandas as pd
import numpy as np


def update_feedback_logs(preds_with_outcomes: pd.DataFrame, out_dir: str = 'artifacts') -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'feedback_log.csv')
    append = preds_with_outcomes.copy()
    append['ts_logged'] = datetime.utcnow().isoformat()
    if os.path.exists(path):
        prev = pd.read_csv(path)
        all_ = pd.concat([prev, append], ignore_index=True)
    else:
        all_ = append
    all_.to_csv(path, index=False)

    # métricas simples
    metrics = {}
    if {'match_result_proba_2','match_result_proba_1','match_result_proba_0','home_score','away_score'} <= set(all_.columns):
        true = all_.apply(lambda r: 2 if r['home_score']>r['away_score'] else (1 if r['home_score']==r['away_score'] else 0), axis=1)
        proba = all_[['match_result_proba_0','match_result_proba_1','match_result_proba_2']].values
        # logloss
        eps=1e-12
        idx = (np.arange(len(true)), true.values)
        p_true = proba[idx]
        metrics['logloss'] = float(-np.mean(np.log(np.clip(p_true, eps, 1.0))))
        metrics['accuracy'] = float(np.mean(np.argmax(proba, axis=1)==true.values))
    return metrics


def build_retraining_dataset(feedback_csv: str = 'artifacts/feedback_log.csv', out_path: str = 'data/retrain_dataset.csv') -> str:
    if not os.path.exists(feedback_csv):
        raise FileNotFoundError('feedback_log.csv não encontrado')
    df = pd.read_csv(feedback_csv)
    # selecionar colunas de features utilizadas + alvo reconstruído
    feature_cols = [c for c in df.columns if any(k in c for k in ['momentum','eff','avg_goals','direct','league_position_diff','odds_','_ev'])]
    df['target_match_result'] = df.apply(lambda r: 2 if r['home_score']>r['away_score'] else (1 if r['home_score']==r['away_score'] else 0), axis=1)
    out = df[feature_cols + ['target_match_result']].dropna()
    out.to_csv(out_path, index=False)
    return out_path

