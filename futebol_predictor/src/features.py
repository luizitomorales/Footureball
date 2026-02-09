# Engenharia de features 
"""
ENGENHARIA DE FEATURES AVANÇADAS PARA FUTEBOL
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import stats
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineer:
    """Gera features avançadas para modelos preditivos"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_cache = {}
        
    def create_all_features(self, match_data: Dict, 
                          historical_data: pd.DataFrame) -> Dict:
        """Cria todas as features para uma partida"""
        
        features = {}
        
        # 1. Features Básicas
        features.update(self._create_basic_features(match_data, historical_data))
        
        # 2. Features de Forma
        features.update(self._create_form_features(match_data, historical_data))
        
        # 3. Features Táticas
        features.update(self._create_tactical_features(match_data, historical_data))
        
        # 4. Features de Confronto
        features.update(self._create_h2h_features(match_data, historical_data))
        
        # 5. Features de Mercado
        features.update(self._create_market_features(match_data))
        
        # 6. Features Contextuais
        features.update(self._create_context_features(match_data))
        
        # 7. Features de Momentum
        features.update(self._create_momentum_features(match_data, historical_data))
        
        # 8. Features Sintéticas
        features.update(self._create_synthetic_features(features))
        
        return features
    
    def _create_basic_features(self, match_data: Dict, 
                             historical_data: pd.DataFrame) -> Dict:
        """Features básicas de desempenho"""
        features = {}
        
        home_team = match_data['home_team']
        away_team = match_data['away_team']
        
        # Obter últimos 10 jogos de cada time
        home_last_10 = self._get_team_matches(home_team, historical_data, 10)
        away_last_10 = self._get_team_matches(away_team, historical_data, 10)
        
        # Médias básicas
        for team_type, team_data in [('home', home_last_10), ('away', away_last_10)]:
            if not team_data.empty:
                features.update(self._calculate_basic_stats(team_data, team_type))
        
        # Diferenças entre times
        if 'home_goals_scored_avg' in features and 'away_goals_conceded_avg' in features:
            features['offensive_advantage'] = (
                features['home_goals_scored_avg'] - features['away_goals_conceded_avg']
            )
        
        return features
    
    def _create_form_features(self, match_data: Dict, 
                            historical_data: pd.DataFrame) -> Dict:
        """Features de forma recente"""
        features = {}
        
        home_team = match_data['home_team']
        away_team = match_data['away_team']
        
        # Forma dos últimos 5 jogos
        home_last_5 = self._get_team_matches(home_team, historical_data, 5)
        away_last_5 = self._get_team_matches(away_team, historical_data, 5)
        
        for team_type, team_data in [('home', home_last_5), ('away', away_last_5)]:
            if not team_data.empty:
                # Pontos por jogo (últimos 5)
                ppg = self._calculate_points_per_game(team_data)
                features[f'{team_type}_form_ppg'] = ppg
                
                # Momentum (ponderado por recência)
                features[f'{team_type}_momentum'] = self._calculate_momentum(team_data)
                
                # Consistência (desvio padrão dos resultados)
                features[f'{team_type}_consistency'] = self._calculate_consistency(team_data)
        
        return features
    
    def _create_tactical_features(self, match_data: Dict,
                                historical_data: pd.DataFrame) -> Dict:
        """Features que inferem estilo tático"""
        features = {}
        
        # Em produção, integrar com dados de:
        # - Passes por posse
        # - Pressão alta vs baixa
        # - Transições ofensivas
        # - Finalizações de fora da área
        
        # Placeholder para features táticas
        features['expected_style_clash'] = 0.5  # 0-1, quanto maior, mais estilos diferentes
        
        return features
    
    def _create_h2h_features(self, match_data: Dict,
                           historical_data: pd.DataFrame) -> Dict:
        """Features de confronto direto"""
        features = {}
        
        home_team = match_data['home_team']
        away_team = match_data['away_team']
        
        # Buscar confrontos anteriores
        h2h_matches = self._get_h2h_matches(home_team, away_team, historical_data)
        
        if not h2h_matches.empty:
            # Vitórias de cada time
            home_wins = len(h2h_matches[
                (h2h_matches['home_team'] == home_team) & 
                (h2h_matches['home_score'] > h2h_matches['away_score'])
            ])
            
            away_wins = len(h2h_matches[
                (h2h_matches['away_team'] == away_team) & 
                (h2h_matches['away_score'] > h2h_matches['home_score'])
            ])
            
            draws = len(h2h_matches[
                h2h_matches['home_score'] == h2h_matches['away_score']
            ])
            
            total_matches = len(h2h_matches)
            
            if total_matches > 0:
                features['h2h_home_win_rate'] = home_wins / total_matches
                features['h2h_away_win_rate'] = away_wins / total_matches
                features['h2h_draw_rate'] = draws / total_matches
                
                # Gols médios no confronto
                features['h2h_avg_goals'] = (
                    h2h_matches['home_score'].sum() + h2h_matches['away_score'].sum()
                ) / total_matches
        
        return features
    
    def _create_market_features(self, match_data: Dict) -> Dict:
        """Features do mercado de apostas"""
        features = {}
        
        if 'odds' in match_data and match_data['odds']:
            odds = match_data['odds']
            
            # Probabilidades implícitas
            if 'home_win' in odds and 'draw' in odds and 'away_win' in odds:
                imp_home = 1 / odds['home_win']
                imp_draw = 1 / odds['draw']
                imp_away = 1 / odds['away_win']
                
                features['implied_prob_home'] = imp_home
                features['implied_prob_draw'] = imp_draw
                features['implied_prob_away'] = imp_away
                
                # Value (edge)
                # Em produção, comparar com probabilidade do modelo
                features['market_efficiency'] = imp_home + imp_draw + imp_away - 1
        
        return features
    
    def _create_context_features(self, match_data: Dict) -> Dict:
        """Features contextuais"""
        features = {}
        
        # Dia da semana
        match_date = match_data['date']
        features['day_of_week'] = match_date.weekday()  # 0=Segunda, 6=Domingo
        
        # Hora do dia
        features['hour_of_day'] = match_date.hour
        
        # Dias de descanso
        if 'home_last_match' in match_data and 'away_last_match' in match_data:
            features['home_rest_days'] = self._calculate_rest_days(
                match_data['home_last_match'], match_date
            )
            features['away_rest_days'] = self._calculate_rest_days(
                match_data['away_last_match'], match_date
            )
        
        # Importância da partida (baseada na rodada)
        features['match_importance'] = self._calculate_match_importance(match_data)
        
        return features
    
    def _create_momentum_features(self, match_data: Dict,
                                historical_data: pd.DataFrame) -> Dict:
        """Features de momentum avançadas"""
        features = {}
        
        # Momentum exponencialmente ponderado
        for team_type in ['home', 'away']:
            team_name = match_data[f'{team_type}_team']
            team_matches = self._get_team_matches(team_name, historical_data, 15)
            
            if not team_matches.empty:
                # Peso maior para jogos recentes
                weights = np.exp(-np.arange(len(team_matches)) / 2)
                weights = weights / weights.sum()
                
                # Calcular pontos ponderados
                weighted_points = self._calculate_weighted_points(team_matches, weights)
                features[f'{team_type}_weighted_momentum'] = weighted_points / 3  # Normalizar 0-1
        
        return features
    
    def _create_synthetic_features(self, existing_features: Dict) -> Dict:
        """Cria features sintéticas baseadas em combinações"""
        features = {}
        
        # Interações entre features
        if 'home_goals_scored_avg' in existing_features and 'away_goals_conceded_avg' in existing_features:
            features['offensive_power_ratio'] = (
                existing_features['home_goals_scored_avg'] / 
                (existing_features['away_goals_conceded_avg'] + 0.001)
            )
        
        if 'home_form_ppg' in existing_features and 'away_form_ppg' in existing_features:
            features['form_difference'] = (
                existing_features['home_form_ppg'] - existing_features['away_form_ppg']
            )
        
        # Features polinomiais (para capturar não-linearidades)
        if 'home_goals_scored_avg' in existing_features:
            features['home_goals_scored_squared'] = (
                existing_features['home_goals_scored_avg'] ** 2
            )
        
        return features
    
    # ============ MÉTODOS AUXILIARES ============
    
    def _get_team_matches(self, team_name: str, 
                         historical_data: pd.DataFrame, 
                         n_matches: int) -> pd.DataFrame:
        """Retorna os últimos N jogos de um time"""
        team_matches = historical_data[
            (historical_data['home_team'] == team_name) | 
            (historical_data['away_team'] == team_name)
        ].tail(n_matches).copy()
        
        return team_matches
    
    def _get_h2h_matches(self, home_team: str, away_team: str,
                        historical_data: pd.DataFrame) -> pd.DataFrame:
        """Retorna confrontos diretos anteriores"""
        h2h = historical_data[
            ((historical_data['home_team'] == home_team) & 
             (historical_data['away_team'] == away_team)) |
            ((historical_data['home_team'] == away_team) & 
             (historical_data['away_team'] == home_team))
        ]
        
        return h2h
    
    def _calculate_basic_stats(self, team_data: pd.DataFrame, 
                             team_type: str) -> Dict:
        """Calcula estatísticas básicas para um time"""
        stats = {}
        
        # Determinar se time é mandante ou visitante em cada jogo
        is_home = team_data['home_team'] == team_type
        is_away = team_data['away_team'] == team_type
        
        # Gols marcados
        home_goals = team_data.loc[is_home, 'home_score'].sum()
        away_goals = team_data.loc[is_away, 'away_score'].sum()
        total_goals_scored = home_goals + away_goals
        
        # Gols sofridos
        home_conceded = team_data.loc[is_home, 'away_score'].sum()
        away_conceded = team_data.loc[is_away, 'home_score'].sum()
        total_goals_conceded = home_conceded + away_conceded
        
        # Médias
        total_matches = len(team_data)
        if total_matches > 0:
            stats[f'{team_type}_goals_scored_avg'] = total_goals_scored / total_matches
            stats[f'{team_type}_goals_conceded_avg'] = total_goals_conceded / total_matches
            
            # Clean sheets
            clean_sheets = len(team_data[
                (is_home & (team_data['away_score'] == 0)) |
                (is_away & (team_data['home_score'] == 0))
            ])
            stats[f'{team_type}_clean_sheet_rate'] = clean_sheets / total_matches
        
        return stats
    
    def _calculate_points_per_game(self, team_data: pd.DataFrame) -> float:
        """Calcula pontos por jogo"""
        points = 0
        
        for _, match in team_data.iterrows():
            if match['home_team'] == team_data.name:
                # Time é mandante
                if match['home_score'] > match['away_score']:
                    points += 3
                elif match['home_score'] == match['away_score']:
                    points += 1
            else:
                # Time é visitante
                if match['away_score'] > match['home_score']:
                    points += 3
                elif match['away_score'] == match['home_score']:
                    points += 1
        
        return points / len(team_data) if len(team_data) > 0 else 0
    
    def _calculate_momentum(self, team_data: pd.DataFrame) -> float:
        """Calcula momentum (ponderado por recência)"""
        if len(team_data) == 0:
            return 0.5
        
        # Peso maior para jogos recentes
        weights = np.exp(-np.arange(len(team_data)) / 2)
        weights = weights / weights.sum()
        
        points = []
        for _, match in team_data.iterrows():
            if match['home_team'] == team_data.name:
                if match['home_score'] > match['away_score']:
                    points.append(3)
                elif match['home_score'] == match['away_score']:
                    points.append(1)
                else:
                    points.append(0)
            else:
                if match['away_score'] > match['home_score']:
                    points.append(3)
                elif match['away_score'] == match['home_score']:
                    points.append(1)
                else:
                    points.append(0)
        
        weighted_points = np.average(points, weights=weights[:len(points)])
        return weighted_points / 3  # Normalizar para 0-1
    
    def _calculate_consistency(self, team_data: pd.DataFrame) -> float:
        """Calcula consistência (1 - desvio padrão normalizado)"""
        if len(team_data) < 2:
            return 0.5
        
        results = []
        for _, match in team_data.iterrows():
            if match['home_team'] == team_data.name:
                if match['home_score'] > match['away_score']:
                    results.append(1.0)  # Vitória
                elif match['home_score'] == match['away_score']:
                    results.append(0.5)  # Empate
                else:
                    results.append(0.0)  # Derrota
            else:
                if match['away_score'] > match['home_score']:
                    results.append(1.0)
                elif match['away_score'] == match['home_score']:
                    results.append(0.5)
                else:
                    results.append(0.0)
        
        std_dev = np.std(results)
        # Normalizar: quanto menor o desvio padrão, maior a consistência
        consistency = 1 - (std_dev / 0.5)  # 0.5 é o máximo desvio teórico
        return max(0, min(1, consistency))
    
    def _calculate_rest_days(self, last_match_date: datetime, 
                           current_date: datetime) -> int:
        """Calcula dias de descanso desde o último jogo"""
        if last_match_date and current_date:
            return (current_date - last_match_date).days
        return 7  # Default
    
    def _calculate_match_importance(self, match_data: Dict) -> float:
        """Calcula importância da partida (0-1)"""
        # Implementação simplificada
        # Em produção, considerar:
        # - Rodada da competição
        # - Posição na tabela
        # - Objetivos do time
        return 0.5
    
    def _calculate_weighted_points(self, team_data: pd.DataFrame, 
                                 weights: np.ndarray) -> float:
        """Calcula pontos ponderados por recência"""
        points = []
        
        for _, match in team_data.iterrows():
            if match['home_team'] == team_data.name:
                if match['home_score'] > match['away_score']:
                    points.append(3)
                elif match['home_score'] == match['away_score']:
                    points.append(1)
                else:
                    points.append(0)
            else:
                if match['away_score'] > match['home_score']:
                    points.append(3)
                elif match['away_score'] == match['home_score']:
                    points.append(1)
                else:
                    points.append(0)
        
        if points:
            return np.average(points, weights=weights[:len(points)])
        return 0

# Instância global
feature_engineer = FeatureEngineer()