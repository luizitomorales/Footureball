# llm_integration.py
# -*- coding: utf-8 -*-
"""
Integração com LLM para:
- Rotular estilo de jogo (propositivo/reativo/pressão alta/bloco baixo/transições rápidas etc.)
- Gerar explicações textuais das previsões (racionalidade interpretável para o relatório)

Implementa um fallback *rule-based* quando não houver chave de API.
"""
from typing import Dict, Optional
import os

PLAYSTYLE_TAGS = ['propositivo', 'reativo', 'pressao_alta', 'bloco_baixo', 'transicoes_rapidas']

class LLMClient:
    def __init__(self, provider: str = 'none'):
        self.provider = provider
        # Ex.: AZURE_OPENAI_API_KEY / OPENAI_API_KEY etc.
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')

    def tag_playstyle(self, team_row: Dict) -> Dict[str, float]:
        """Retorna distribuição de tags (0-1). Usa heurística se não houver LLM."""
        if not self.api_key:
            return self._heuristic_tags(team_row)
        # Placeholder: aqui você chamaria o provedor de LLM
        # Para manter offline, retornamos heurística calibrada
        return self._heuristic_tags(team_row)

    def explain_prediction(self, match_row: Dict) -> str:
        if not self.api_key:
            return self._heuristic_explanation(match_row)
        return self._heuristic_explanation(match_row)

    # ------------------------ Heurísticas de fallback --------------------- #
    def _heuristic_tags(self, team_row: Dict) -> Dict[str, float]:
        g = float(team_row.get('avg_goals_scored', 0) or 0)
        x = float(team_row.get('avg_xg', 0) or 0)
        sot = float(team_row.get('avg_shots_on_target', 0) or 0)
        poss = float(team_row.get('avg_possession', 50) or 50)
        gc = float(team_row.get('avg_goals_conceded', 0) or 0)
        tags = {
            'propositivo': min(1.0, 0.02*sot + 0.01*poss + 0.5*x),
            'reativo': min(1.0, 0.6 - 0.01*poss + 0.3*(g>1.6)),
            'pressao_alta': min(1.0, 0.015*sot + 0.2*(poss>55)),
            'bloco_baixo': min(1.0, 0.6 - 0.01*sot + 0.2*(gc<1.0)),
            'transicoes_rapidas': min(1.0, 0.4 + 0.01*(sot>4) + 0.2*(poss<48))
        }
        # normalização simples
        s = sum(tags.values()) or 1.0
        return {k: v/s for k,v in tags.items()}

    def _heuristic_explanation(self, match_row: Dict) -> str:
        hm = match_row.get('home_team'); aw = match_row.get('away_team')
        parts = []
        parts.append(f"Momentum casa {match_row.get('home_momentum',0):.2f} vs fora {match_row.get('away_momentum',0):.2f}.")
        parts.append(f"Eficiência ofensiva Δ {match_row.get('offensive_balance',0):+.2f}, defensiva Δ {match_row.get('defensive_balance',0):+.2f}.")
        if 'odds_home_win' in match_row:
            parts.append(f"Odds mercado H/D/A: {match_row.get('odds_home_win','-')}/{match_row.get('odds_draw','-')}/{match_row.get('odds_away_win','-')}.")
        return f"{hm} vs {aw}: " + " ".join(parts)

