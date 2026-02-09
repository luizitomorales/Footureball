# Clientes das APIs 
"""
CLIENTE UNIFICADO PARA TODAS AS APIS DE FUTEBOL
"""
import requests
import aiohttp
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
from loguru import logger
from functools import lru_cache

from config import api_config, Competition

@dataclass
class MatchData:
    """Estrutura padronizada para dados de partida"""
    match_id: str
    home_team: str
    away_team: str
    competition: str
    date: datetime
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    odds: Optional[Dict] = None
    statistics: Optional[Dict] = None
    lineups: Optional[Dict] = None

class FootballAPIClient:
    """Cliente unificado para APIs de futebol"""
    
    def __init__(self, use_cache: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Football Predictor/1.0)'
        })
        
        self.cache = {}
        self.use_cache = use_cache
        
    def get_upcoming_matches(self, days_ahead: int = 3) -> List[MatchData]:
        """Busca todos os jogos das próximas N dias"""
        all_matches = []
        
        for competition in Competition:
            try:
                logger.info(f"Buscando jogos da {competition.value['name']}")
                matches = self._get_competition_matches(
                    competition.value['id'],
                    days_ahead
                )
                all_matches.extend(matches)
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Erro na competição {competition.name}: {e}")
                continue
        
        return all_matches
    
    def _get_competition_matches(self, competition_id: str, 
                               days_ahead: int) -> List[MatchData]:
        """Busca jogos de uma competição específica"""
        cache_key = f"{competition_id}_{days_ahead}"
        
        # Verificar cache
        if self.use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Buscar da API
        url = f"{api_config.FOOTBALL_DATA_BASE_URL}/competitions/{competition_id}/matches"
        
        params = {
            'dateFrom': datetime.now().strftime('%Y-%m-%d'),
            'dateTo': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        }
        
        try:
            response = self.session.get(
                url,
                headers=api_config.FOOTBALL_DATA_HEADERS,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                matches = self._parse_matches(data.get('matches', []), competition_id)
                
                # Atualizar cache
                if self.use_cache:
                    self.cache[cache_key] = matches
                
                return matches
                
        except Exception as e:
            logger.error(f"Erro ao buscar jogos: {e}")
        
        return []
    
    def get_match_odds(self, match_id: str, markets: List[str] = None) -> Dict:
        """Busca odds para uma partida específica"""
        if markets is None:
            markets = ["h2h", "totals", "btts"]
        
        odds_data = {}
        
        for market in markets:
            try:
                # The Odds API
                url = f"{api_config.ODDS_API_BASE_URL}/sports/soccer_france_ligue_one/odds"
                params = {
                    'apiKey': api_config.ODDS_API_KEY,
                    'regions': api_config.ODDS_REGIONS,
                    'markets': market,
                    'eventIds': match_id,
                    'oddsFormat': 'decimal'
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    market_data = response.json()
                    if market_data:
                        odds_data[market] = market_data[0]['bookmakers'][0]['markets'][0]
                        
            except Exception as e:
                logger.error(f"Erro ao buscar odds {market}: {e}")
                continue
        
        return odds_data
    
    def get_match_statistics(self, match_id: str) -> Dict:
        """Busca estatísticas detalhadas de uma partida"""
        try:
            url = f"{api_config.FOOTBALL_DATA_BASE_URL}/matches/{match_id}"
            
            response = self.session.get(
                url,
                headers=api_config.FOOTBALL_DATA_HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'possession': self._extract_stat(data, 'possession'),
                    'shots': self._extract_stat(data, 'shots'),
                    'passes': self._extract_stat(data, 'passes'),
                    'fouls': self._extract_stat(data, 'fouls'),
                    'cards': self._extract_stat(data, 'cards')
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
        
        return {}
    
    async def get_live_data(self, match_id: str) -> Dict:
        """Busca dados em tempo real (WebSocket/SSE)"""
        async with aiohttp.ClientSession() as session:
            try:
                # Exemplo com API-Football (tem dados em tempo real)
                url = f"{api_config.API_FOOTBALL_URL}/fixtures"
                headers = {
                    'x-rapidapi-key': api_config.API_FOOTBALL_KEY,
                    'x-rapidapi-host': api_config.API_FOOTBALL_HOST
                }
                
                params = {'id': match_id, 'live': 'all'}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_live_data(data)
                        
            except Exception as e:
                logger.error(f"Erro dados em tempo real: {e}")
        
        return {}
    
    def get_historical_data(self, team_id: str, matches: int = 10) -> pd.DataFrame:
        """Busca dados históricos de um time"""
        try:
            url = f"{api_config.FOOTBALL_DATA_BASE_URL}/teams/{team_id}/matches"
            
            params = {
                'limit': matches,
                'status': 'FINISHED'
            }
            
            response = self.session.get(
                url,
                headers=api_config.FOOTBALL_DATA_HEADERS,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return pd.DataFrame(data.get('matches', []))
                
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
        
        return pd.DataFrame()
    
    def _parse_matches(self, raw_matches: List[Dict], competition_id: str) -> List[MatchData]:
        """Converte dados brutos para estrutura padronizada"""
        matches = []
        
        for match in raw_matches:
            try:
                match_data = MatchData(
                    match_id=str(match['id']),
                    home_team=match['homeTeam']['name'],
                    away_team=match['awayTeam']['name'],
                    competition=competition_id,
                    date=datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00')),
                    status=match['status'],
                    home_score=match['score']['fullTime']['home'] if match['score']['fullTime']['home'] is not None else None,
                    away_score=match['score']['fullTime']['away'] if match['score']['fullTime']['away'] is not None else None
                )
                matches.append(match_data)
                
            except Exception as e:
                logger.warning(f"Erro ao parsear partida: {e}")
                continue
        
        return matches
    
    def _extract_stat(self, data: Dict, stat_name: str) -> Dict:
        """Extrai estatística específica dos dados"""
        # Implementação simplificada
        return {}
    
    def _parse_live_data(self, data: Dict) -> Dict:
        """Parseia dados em tempo real"""
        # Implementação simplificada
        return {}

# Cliente singleton
api_client = FootballAPIClient()