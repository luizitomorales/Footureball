@echo off
REM Criando estrutura de diretórios

mkdir futebol_predictor
cd futebol_predictor

REM Diretórios principais
mkdir data\raw
mkdir data\processed
mkdir data\models
mkdir data\cache

mkdir src
mkdir scripts
mkdir logs
mkdir reports

REM Arquivos em src
echo # Configurações e constantes > src\config.py
echo # Clientes das APIs > src\api_client.py
echo # Engenharia de features > src\features.py
echo # Modelos ML/DL > src\models.py
echo # Otimizador de apostas > src\optimizer.py
echo # Integração com LLM > src\llm_integration.py
echo # Gerador de relatórios > src\reporter.py
echo # Sistema de email > src\emailer.py
echo # Sistema de retroalimentação > src\feedback.py
echo # Agendador inteligente > src\scheduler.py

REM Arquivos em scripts
echo # Script de setup > scripts\setup_env.sh
echo # Pipeline principal > scripts\run_pipeline.py
echo # Treinamento de modelos > scripts\train_models.py
echo # Backtesting > scripts\backtest.py

REM Arquivos raiz
echo # Variáveis de ambiente > .env
echo # Dependências > requirements.txt
echo # Docker Compose > docker-compose.yml
echo # Documentação > README.md

echo Estrutura criada com sucesso!
pause
