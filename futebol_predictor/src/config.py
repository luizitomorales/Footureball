# Configurações e constantes 
"""
CONFIGURAÇÕES CENTRALIZADAS DO SISTEMA
"""
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json

class MarketType(Enum):
    """Tipos de mercados de apostas disponíveis"""
    MATCH_RESULT = "1X2"           # Home Win, Draw, Away Win
    OVER_UNDER = "over_under"      # Over/Under 2.5
    BTTS = "btts"                  # Both Teams to Score
    DOUBLE_CHANCE = "double_chance" # 1X, 12, X2
    ASIAN_HANDICAP = "asian_handicap"
    CORRECT_SCORE = "correct_score"
    FIRST_GOAL = "first_goal"
    CARDS_TOTAL = "cards_total"

class Competition(Enum):
    """Competições monitoradas"""
    PREMIER_LEAGUE = {"id": "PL", "name": "Premier League", "priority": 1.0}
    LA_LIGA = {"id": "PD", "name": "La Liga", "priority": 0.95}
    SERIE_A = {"id": "SA", "name": "Serie A", "priority": 0.90}
    BUNDESLIGA = {"id": "BL1", "name": "Bundesliga", "priority": 0.90}
    LIGUE_1 = {"id": "FL1", "name": "Ligue 1", "priority": 0.85}
    BRASILEIRAO = {"id": "BSA", "name": "Brasileirão", "priority": 0.80}
    PRIMEIRA_LIGA = {"id": "PPL", "name": "Primeira Liga", "priority": 0.75}
    EREDIVISIE = {"id": "DED", "name": "Eredivisie", "priority": 0.70}

@dataclass
class APIConfig:
    """Configurações de APIs"""
    # Football-Data.org
    FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
    FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
    FOOTBALL_DATA_HEADERS = {"X-Auth-Token": FOOTBALL_DATA_KEY}
    
    # The Odds API
    ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
    ODDS_API_KEY = os.getenv("ODDS_API_KEY")
    ODDS_REGIONS = "eu,us,uk"
    ODDS_MARKETS = "h2h,totals,btts,double_chance"
    
    # API-Football (RapidAPI)
    API_FOOTBALL_URL = "https://v3.football.api-sports.io"
    API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
    API_FOOTBALL_HOST = "v3.football.api-sports.io"
    
    # LLM APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_API_KEY")
    
    OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

@dataclass
class BettingConfig:
    """Configurações de apostas"""
    INITIAL_BANKROLL = float(os.getenv("INITIAL_BANKROLL", 10000.0))
    MAX_RISK_PER_BET = float(os.getenv("MAX_RISK_PER_BET", 0.15))
    KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", 0.25))
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", 0.55))
    
    # Mercados prioritários
    PRIMARY_MARKETS = [
        MarketType.MATCH_RESULT,
        MarketType.OVER_UNDER,
        MarketType.BTTS
    ]
    
    # Competições ativas
    ACTIVE_COMPETITIONS = [
        Competition.PREMIER_LEAGUE,
        Competition.LA_LIGA,
        Competition.SERIE_A,
        Competition.BUNDESLIGA,
        Competition.LIGUE_1
    ]

@dataclass
class ModelConfig:
    """Configurações de modelos ML"""
    # Random Forest
    RF_N_ESTIMATORS = 200
    RF_MAX_DEPTH = 15
    RF_MIN_SAMPLES_SPLIT = 10
    
    # XGBoost
    XGB_LEARNING_RATE = 0.05
    XGB_MAX_DEPTH = 8
    XGB_N_ESTIMATORS = 300
    
    # LightGBM
    LGBM_N_ESTIMATORS = 250
    LGBM_LEARNING_RATE = 0.07
    LGBM_NUM_LEAVES = 31
    
    # Deep Learning
    DL_HIDDEN_LAYERS = [128, 64, 32]
    DL_DROPOUT_RATE = 0.3
    DL_LEARNING_RATE = 0.001

@dataclass
class ScheduleConfig:
    """Configurações de agendamento"""
    NIGHT_REPORT_TIME = "22:00"  # 10 PM
    MORNING_UPDATE_TIME = "08:00"  # 8 AM
    PRE_MATCH_UPDATE_MINUTES = 60  # 1 hora antes
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")
    
    # Dias para buscar jogos
    DAYS_AHEAD = 3
    DAYS_BEHIND = 30  # Para histórico

@dataclass
class EmailConfig:
    """Configurações de email"""
    SENDER = os.getenv("EMAIL_SENDER")
    PASSWORD = os.getenv("EMAIL_PASSWORD")
    RECIPIENT = os.getenv("EMAIL_RECIPIENT", "lipsf25@gmail.com")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    
    # Templates
    REPORT_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #2c3e50; color: white; padding: 20px; }
            .bet { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
            .profit { color: green; }
            .loss { color: red; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Relatório de Apostas - {date}</h1>
        </div>
        {content}
    </body>
    </html>
    """

@dataclass 
class SystemConfig:
    """Configurações do sistema"""
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    CACHE_TTL = 3600  # 1 hora em segundos
    
    # Paths
    DATA_DIR = "data"
    MODELS_DIR = "data/models"
    LOGS_DIR = "logs"
    REPORTS_DIR = "reports"

# Instâncias de configuração
api_config = APIConfig()
betting_config = BettingConfig()
model_config = ModelConfig()
schedule_config = ScheduleConfig()
email_config = EmailConfig()
system_config = SystemConfig()

# Exportar tudo
__all__ = [
    'MarketType',
    'Competition',
    'api_config',
    'betting_config', 
    'model_config',
    'schedule_config',
    'email_config',
    'system_config'
]