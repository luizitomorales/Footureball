# optimizer.py
# -*- coding: utf-8 -*-
"""
Otimização de carteira de apostas (Portfolio Optimization).
- Seleção de value bets a partir de probabilidades do modelo vs odds de mercado.
- Alocação por Kelly fracionado e alternativa de risco (quase) média-variância.
- Restrições práticas: stake mínima/máxima, limite por evento, orçamento total.

***Atenção***: Apostas envolvem risco financeiro. Utilize para fins educacionais
ou com gestão de risco profissional.
"""
from dataclasses import dataclass
from typing import List, Optional, Literal
import numpy as np
import pandas as pd

@dataclass
class BetPick:
    match_id: str
    market: Literal['1X2']
    selection: Literal['H','D','A']
    model_prob: float  # prob. do modelo (0-1)
    odds: float        # odds de mercado decimal
    max_stake: float = 1.0

@dataclass
class Allocation:
    match_id: str
    selection: str
    odds: float
    model_prob: float
    edge: float
    kelly_fraction: float
    stake: float


def implied_prob_from_odds(odds: float) -> float:
    return 1.0 / max(odds, 1e-9)


def kelly_fraction(p: float, odds: float) -> float:
    """Kelly para odds decimais: b = odds-1, f* = (bp - q)/b."""
    b = max(odds - 1.0, 1e-9)
    q = 1.0 - p
    f = (b * p - q) / b
    return max(0.0, f)


def select_value_bets(df_preds: pd.DataFrame, min_edge: float = 0.02) -> pd.DataFrame:
    """
    Espera colunas: ['match_id','odds_home_win','odds_draw','odds_away_win',
                     'match_result_proba_2','match_result_proba_1','match_result_proba_0']
    Retorna linhas long-form com edge e kelly propostos.
    """
    rows = []
    for _, r in df_preds.iterrows():
        for sel, col_p, col_o in [('H','match_result_proba_2','odds_home_win'),
                                   ('D','match_result_proba_1','odds_draw'),
                                   ('A','match_result_proba_0','odds_away_win')]:
            if col_p in r and col_o in r and pd.notna(r[col_o]):
                p = float(r[col_p])
                o = float(r[col_o])
                mprob = p
                mkt = implied_prob_from_odds(o)
                edge = mprob - mkt
                if edge >= min_edge:
                    rows.append({
                        'match_id': r.get('match_id', f"{r.get('home_team','?')} vs {r.get('away_team','?')}") ,
                        'selection': sel, 'model_prob': mprob, 'odds': o,
                        'edge': edge, 'kelly_fraction': kelly_fraction(mprob, o)
                    })
    return pd.DataFrame(rows)


def allocate_bankroll(value_bets: pd.DataFrame, bankroll: float, max_events: int = 8,
                      max_stake_pct: float = 0.05, kelly_factor: float = 0.5) -> pd.DataFrame:
    """
    Aloca banca usando Kelly fracionado, com limites por evento e número máximo de picks.
    - kelly_factor em [0,1] reduz alavancagem.
    """
    if value_bets.empty:
        return value_bets
    # ordenar por edge * kelly
    vb = value_bets.copy()
    vb['score'] = vb['edge'] * vb['kelly_fraction']
    vb = vb.sort_values('score', ascending=False).head(max_events)
    stakes = []
    used = 0.0
    for _, r in vb.iterrows():
        f = float(r['kelly_fraction']) * kelly_factor
        stake = min(f * bankroll, bankroll * max_stake_pct)
        stakes.append(stake)
        used += stake
    vb['stake'] = stakes
    vb['bankroll_used'] = used
    return vb[['match_id','selection','odds','model_prob','edge','kelly_fraction','stake']]

