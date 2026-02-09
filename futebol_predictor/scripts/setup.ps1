# Script de setup 
# ============================================================================
# SETUP SCRIPT - Sistema de Predição de Futebol (Windows)
# ============================================================================
Write-Host "🚀 Configurando ambiente de predição de futebol no Windows..." -ForegroundColor Green
Write-Host "===========================================================================" -ForegroundColor Cyan

# 1. Verificar se Python está instalado
Write-Host "`n🐍 Verificando instalação do Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>$null
if (-not $pythonVersion) {
    Write-Host "❌ Python não encontrado!" -ForegroundColor Red
    Write-Host "   Instale Python 3.8+ em: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "   ✅ Marque a opção: 'Add Python to PATH'" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green

# 2. Criar estrutura de diretórios
Write-Host "`n📁 Criando estrutura de diretórios..." -ForegroundColor Yellow
$directories = @(
    "data\raw",
    "data\processed", 
    "data\models",
    "data\cache",
    "src",
    "logs",
    "reports",
    "scripts"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "   Criado: $dir" -ForegroundColor Gray
    }
}

# 3. Criar e ativar ambiente virtual
Write-Host "`n🌍 Criando ambiente virtual..." -ForegroundColor Yellow
$venvPath = "venv"
if (Test-Path $venvPath) {
    Write-Host "   Ambiente virtual já existe. Recriando..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
}

python -m venv $venvPath
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "❌ Falha ao criar ambiente virtual!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Ambiente virtual criado em: $venvPath" -ForegroundColor Green

# 4. Ativar ambiente virtual e instalar dependências
Write-Host "`n📦 Ativando ambiente virtual e instalando dependências..." -ForegroundColor Yellow

# Criar script temporário para ativar venv e instalar
$installScript = @"
# Ativar ambiente virtual
& ".\$venvPath\Scripts\Activate.ps1"

# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências básicas
pip install pandas numpy scikit-learn scipy requests

# Verificar se requirements.txt existe
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
} else {
    # Instalar dependências padrão
    pip install xgboost lightgbm python-dotenv schedule
    pip install matplotlib seaborn plotly
    pip install openai langchain transformers
    pip install cvxpy pulp statsmodels
    pip install premailer jinja2 loguru
}

# Desativar ambiente virtual
deactivate
"@

$installScript | Out-File -FilePath "temp_install.ps1" -Encoding UTF8

# Executar script de instalação
try {
    & powershell -ExecutionPolicy Bypass -File "temp_install.ps1"
    Write-Host "✅ Dependências instaladas com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Algumas dependências podem ter falhado. Continuando..." -ForegroundColor Yellow
}

# Limpar script temporário
Remove-Item "temp_install.ps1" -Force

# 5. Configurar arquivo .env
Write-Host "`n⚙️  Configurando arquivo de ambiente..." -ForegroundColor Yellow
$envTemplate = @"
# ============================================================================
# API KEYS (OBRIGATÓRIAS)
# ============================================================================

# Football-Data.org (Free Tier: 10 requests/min)
FOOTBALL_DATA_API_KEY=sua_chave_aqui

# The Odds API (Free: 500 requests/month)
ODDS_API_KEY=sua_chave_aqui

# API-Football (RapidAPI - tem plano free)
API_FOOTBALL_KEY=sua_chave_aqui
API_FOOTBALL_HOST=v3.football.api-sports.io

# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Opção 1: OpenAI (Pago, mais preciso)
OPENAI_API_KEY=opcional

# Opção 2: Local Ollama (Gratuito, offline - instale separadamente)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

EMAIL_SENDER=seu_email@gmail.com
EMAIL_PASSWORD=senha_app_gerada  # Use App Password, não senha normal
EMAIL_RECIPIENT=lipsf25@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# ============================================================================
# BETTING CONFIGURATION
# ============================================================================

INITIAL_BANKROLL=10000.00
MAX_RISK_PER_BET=0.15
KELLY_FRACTION=0.25
MIN_CONFIDENCE=0.55

# ============================================================================
# SYSTEM CONFIGURATION
# ============================================================================

LOG_LEVEL=INFO
TIMEZONE=America/Sao_Paulo
DEBUG_MODE=False
"@

if (-not (Test-Path ".env")) {
    $envTemplate | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Arquivo .env criado!" -ForegroundColor Green
    Write-Host "   ⚠️  Edite o arquivo .env com suas chaves de API!" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Arquivo .env já existe. Mantendo versão atual." -ForegroundColor Yellow
}

# 6. Criar script de ativação rápido para Windows
Write-Host "`n🚀 Criando atalhos e scripts auxiliares..." -ForegroundColor Yellow

# Criar activate.bat para fácil ativação
$activateBat = @"
@echo off
echo Ativando ambiente virtual...
call .\venv\Scripts\activate.bat
echo Ambiente virtual ativado!
echo.
echo Para executar o pipeline:
echo   python run_pipeline.py
echo.
cmd /k
"@

$activateBat | Out-File -FilePath "activate.bat" -Encoding ASCII
Write-Host "✅ Script de ativação criado: activate.bat" -ForegroundColor Green

# Criar run.bat para executar pipeline
$runBat = @"
@echo off
echo ========================================
echo  Sistema de Predição de Futebol
echo ========================================
echo.

REM Ativar ambiente virtual
call .\venv\Scripts\activate.bat

REM Executar pipeline
python run_pipeline.py

REM Manter terminal aberto
pause
"@

$runBat | Out-File -FilePath "run.bat" -Encoding ASCII
Write-Host "✅ Script de execução criado: run.bat" -ForegroundColor Green

# 7. Criar requirements.txt se não existir
if (-not (Test-Path "requirements.txt")) {
    $requirements = @"
# Core
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
scipy>=1.10.0

# ML
xgboost>=1.7.0
lightgbm>=4.0.0

# APIs
requests>=2.31.0
python-dotenv>=1.0.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0

# Utils
schedule>=1.2.0
loguru>=0.7.0
premailer>=3.10.0
jinja2>=3.1.0

# LLM (opcional)
openai>=1.0.0
langchain>=0.0.200
"@
    
    $requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
    Write-Host "✅ Arquivo requirements.txt criado!" -ForegroundColor Green
}

# 8. Baixar dados de exemplo (opcional)
Write-Host "`n📥 Baixando dados de exemplo para treinamento..." -ForegroundColor Yellow
$sampleDataScript = @"
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Criar dados de exemplo
np.random.seed(42)
n_matches = 1000

data = {
    'match_id': [f'match_{i}' for i in range(n_matches)],
    'home_team': [f'Team_{np.random.randint(1, 21)}' for _ in range(n_matches)],
    'away_team': [f'Team_{np.random.randint(1, 21)}' for _ in range(n_matches)],
    'competition': np.random.choice(['PL', 'PD', 'SA', 'BL1'], n_matches),
    'date': [datetime.now() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_matches)],
    'home_score': np.random.poisson(1.5, n_matches),
    'away_score': np.random.poisson(1.2, n_matches),
    'home_possession': np.random.uniform(40, 65, n_matches),
    'away_possession': np.random.uniform(35, 60, n_matches),
    'home_shots': np.random.poisson(12, n_matches),
    'away_shots': np.random.poisson(10, n_matches)
}

df = pd.DataFrame(data)

# Calcular resultado
df['result'] = df.apply(lambda x: 'H' if x['home_score'] > x['away_score'] else ('D' if x['home_score'] == x['away_score'] else 'A'), axis=1)
df['total_goals'] = df['home_score'] + df['away_score']
df['over_2_5'] = (df['total_goals'] > 2.5).astype(int)
df['btts'] = ((df['home_score'] > 0) & (df['away_score'] > 0)).astype(int)

# Salvar
os.makedirs('data/raw', exist_ok=True)
df.to_csv('data/raw/sample_matches.csv', index=False)
print(f"Dados de exemplo criados: {len(df)} partidas")
"@

$sampleDataScript | Out-File -FilePath "scripts/create_sample_data.py" -Encoding UTF8

# Executar script de criação de dados
try {
    & ".\venv\Scripts\python.exe" "scripts/create_sample_data.py"
    Write-Host "✅ Dados de exemplo criados em data/raw/sample_matches.csv" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Não foi possível criar dados de exemplo. Continuando..." -ForegroundColor Yellow
}

# 9. Criar script de teste
Write-Host "`n🧪 Criando script de teste..." -ForegroundColor Yellow
$testScript = @"
import sys
import pandas as pd
import numpy as np
from datetime import datetime

print("🧪 Testando configuração do sistema...")
print("=" * 50)

# Testar imports básicos
try:
    import pandas as pd
    print(f"✅ pandas {pd.__version__}")
except ImportError as e:
    print(f"❌ pandas: {e}")

try:
    import numpy as np
    print(f"✅ numpy {np.__version__}")
except ImportError as e:
    print(f"❌ numpy: {e}")

try:
    import sklearn
    print(f"✅ scikit-learn {sklearn.__version__}")
except ImportError as e:
    print(f"❌ scikit-learn: {e}")

# Testar dados
try:
    df = pd.read_csv('data/raw/sample_matches.csv')
    print(f"✅ Dados carregados: {len(df)} partidas")
except Exception as e:
    print(f"⚠️  Dados: {e}")

# Testar estrutura de diretórios
import os
dirs = ['data/raw', 'data/processed', 'src', 'logs']
for d in dirs:
    if os.path.exists(d):
        print(f"✅ Diretório {d} existe")
    else:
        print(f"❌ Diretório {d} não encontrado")

print("=" * 50)
print("Teste concluído!")
if os.path.exists('.env'):
    print("⚠️  Lembre-se de configurar o arquivo .env com suas chaves de API!")
"@

$testScript | Out-File -FilePath "test_configuration.py" -Encoding UTF8

# 10. Configurar agendador do Windows (opcional)
Write-Host "`n⏰ Configurando agendamento automático (opcional)..." -ForegroundColor Yellow
$schedulerScript = @"
# Script para configurar tarefas agendadas no Windows
# Execute como Administrador para configurar

param([switch]$AsAdmin)

if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "⚠️  Execute este script como Administrador para configurar tarefas agendadas" -ForegroundColor Yellow
    exit 1
}

# Caminho completo para o Python no venv
$pythonPath = Join-Path (Get-Location) "venv\Scripts\python.exe"
$scriptPath = Join-Path (Get-Location) "run_pipeline.py"

# Criar tarefa para executar às 22:00 (noite anterior)
$nightTask = @{
    TaskName = "FootballPredictor_NightReport"
    Action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath
    Trigger = New-ScheduledTaskTrigger -Daily -At "22:00"
    Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
}

Register-ScheduledTask @nightTask -Description "Relatório noturno de apostas em futebol" -Force
Write-Host "✅ Tarefa agendada criada: Relatório às 22:00" -ForegroundColor Green

# Criar tarefa para executar a cada hora
$hourlyTask = @{
    TaskName = "FootballPredictor_HourlyCheck"
    Action = New-ScheduledTaskAction -Execute $pythonPath -Argument "$scriptPath --hourly"
    Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
    Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
}

Register-ScheduledTask @hourlyTask -Description "Verificação horária para relatório 1h antes" -Force
Write-Host "✅ Tarefa agendada criada: Verificação a cada hora" -ForegroundColor Green

Write-Host "`n🎉 Tarefas agendadas configuradas com sucesso!" -ForegroundColor Green
Write-Host "   Para visualizar: Abra 'Agendador de Tarefas' do Windows" -ForegroundColor Yellow
"@

$schedulerScript | Out-File -FilePath "scripts/setup_windows_scheduler.ps1" -Encoding UTF8

# 11. Finalização
Write-Host "`n🎉 SETUP COMPLETO COM SUCESSO!" -ForegroundColor Green
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Edite o arquivo .env com suas chaves de API:" -ForegroundColor White
Write-Host "   - FOOTBALL_DATA_API_KEY (obtenha em: https://www.football-data.org/)" -ForegroundColor Gray
Write-Host "   - ODDS_API_KEY (obtenha em: https://the-odds-api.com/)" -ForegroundColor Gray
Write-Host "   - Configurações de email (Gmail)" -ForegroundColor Gray

Write-Host "`n2. Para ATIVAR o ambiente virtual:" -ForegroundColor White
Write-Host "   Execute: .\activate.bat" -ForegroundColor Cyan

Write-Host "`n3. Para TESTAR a configuração:" -ForegroundColor White
Write-Host "   Execute: .\venv\Scripts\python.exe test_configuration.py" -ForegroundColor Cyan

Write-Host "`n4. Para EXECUTAR o pipeline:" -ForegroundColor White
Write-Host "   Execute: .\run.bat" -ForegroundColor Cyan
Write-Host "   Ou manualmente:" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\activate.bat" -ForegroundColor Gray
Write-Host "     python run_pipeline.py" -ForegroundColor Gray

Write-Host "`n5. Para AGENDAR execução automática (Admin):" -ForegroundColor White
Write-Host "   Execute como Administrador: powershell -ExecutionPolicy Bypass -File scripts\setup_windows_scheduler.ps1" -ForegroundColor Cyan

Write-Host "`n6. CONFIGURAÇÃO DO EMAIL (Gmail):" -ForegroundColor White
Write-Host "   - Ative 'Acesso a app menos seguro' OU" -ForegroundColor Gray
Write-Host "   - Crie uma 'App Password': https://myaccount.google.com/apppasswords" -ForegroundColor Gray

Write-Host "`n⚠️  TROUBLESHOOTING:" -ForegroundColor Yellow
Write-Host "   - Se scripts não executarem, execute: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Gray
Write-Host "   - Para problemas de SSL: pip install certifi" -ForegroundColor Gray
Write-Host "   - Para atualizar: .\venv\Scripts\python.exe -m pip install --upgrade pip" -ForegroundColor Gray

Write-Host "`n===========================================================================" -ForegroundColor Cyan
Write-Host "📧 Dúvidas: lipsf25@gmail.com" -ForegroundColor White
Write-Host "===========================================================================" -ForegroundColor Cyan

# 12. Perguntar se deseja configurar .env agora
$configureNow = Read-Host "`nDeseja abrir o arquivo .env para configuração agora? (S/N)"
if ($configureNow -eq 'S' -or $configureNow -eq 's') {
    notepad.exe ".env"
}

# 13. Perguntar se deseja ativar o ambiente virtual
$activateNow = Read-Host "`nDeseja ativar o ambiente virtual agora? (S/N)"
if ($activateNow -eq 'S' -or $activateNow -eq 's') {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "`n✅ Ambiente virtual ativado!" -ForegroundColor Green
    Write-Host "   Execute 'deactivate' para sair" -ForegroundColor Gray
}