@echo off
setlocal enabledelayedexpansion

REM ============================================
REM futebol_predictor - Setup DB Pipeline (Windows .bat) - COPY version
REM ============================================

REM 1) Ir para a pasta do projeto (este .bat deve estar na raiz do projeto)
pushd %~dp0

echo === 1) Criando estrutura de diretorios...
if not exist src mkdir src
if not exist db mkdir db
if not exist sql mkdir sql
if not exist artifacts mkdir artifacts
if not exist artifacts\models mkdir artifacts\models
if not exist artifacts\reports mkdir artifacts\reports
if not exist data mkdir data

echo === 2) Copiando arquivos de db_integration\ para as pastas finais...
IF EXIST db_integration\db.py              copy /Y db_integration\db.py              db\db.py
IF EXIST db_integration\etl_to_db.py       copy /Y db_integration\etl_to_db.py       db\etl_to_db.py
IF EXIST db_integration\db_readers.py      copy /Y db_integration\db_readers.py      db\db_readers.py
IF EXIST db_integration\db_writers.py      copy /Y db_integration\db_writers.py      db\db_writers.py
IF EXIST db_integration\run_pipeline_db.py copy /Y db_integration\run_pipeline_db.py db\run_pipeline_db.py
IF EXIST db_integration\feedback_to_db.py  copy /Y db_integration\feedback_to_db.py  db\feedback_to_db.py
IF EXIST db_integration\schema.sql         copy /Y db_integration\schema.sql         sql\schema.sql
IF EXIST db_integration\schema_oracle.sql  copy /Y db_integration\schema_oracle.sql  sql\schema_oracle.sql
IF EXIST db_integration\README_DB.md       copy /Y db_integration\README_DB.md       db\README_DB.md

echo === 3) Gerando .env exemplo (so cria se nao existir)...
IF NOT EXIST .env (
    echo DATABASE_URL=postgresql+psycopg2://postgresql:123@host:5432/footureball>.env
    echo REM DATABASE_URL=oracle+cx_oracle://user:senha@host:1521/?service_name=ORCLCDB>>.env
    echo BANKROLL=1000>>.env
    echo MIN_EDGE=0.02>>.env
    echo KELLY_FACTOR=0.5>>.env
    echo MOMENTUM_N=5>>.env
    echo HORIZON_DAYS=7>>.env
    echo SMTP_HOST=smtp.gmail.com>>.env
    echo SMTP_PORT=587>>.env
    echo SMTP_USER=>>.env
    echo SMTP_PASS=>>.env
    echo EMAIL_FROM=>>.env
    echo EMAIL_TO=>>.env
    echo EMAIL_SUBJECT_PREFIX=[Pred-Fut] >>.env
)

echo === 4) (Opcional) Aplicar DDL postgresql com psql
echo.
echo Para aplicar manualmente:
echo   postgresql: postgresql -f sql\schema.sql
echo   Oracle    : sqlplus user/pass@TNS @sql\schema_oracle.sql
echo.
choice /C YN /M "Deseja tentar aplicar o DDL postgresql automaticamente via psql? (Y/N)"
if errorlevel 2 goto SKIP_PSQL
if errorlevel 1 (
    where postgresql >nul 2>nul
    if %errorlevel%==0 (
        echo Rodando psql com sql\schema.sql ...
        postgresql -f sql\schema.sql
    ) else (
        echo postgresql nao encontrado no PATH. Pulei esta etapa.
    )
)
:SKIP_PSQL

echo === 5) Criando venv e instalando dependencias...
where python >nul 2>nul
if NOT %errorlevel%==0 (
    echo Python nao encontrado no PATH. Instale o Python e rode novamente.
    goto END
)

if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate

echo Instalando pacotes basicos...
python -m pip install --upgrade pip
pip install pandas numpy scikit-learn xgboost reportlab joblib python-dateutil SQLAlchemy psycopg2-binary oracledb

echo === 6) Teste rapido de imports dos modulos DB...
python - <<PY
import importlib
for m in ["db.db","db.etl_to_db","db.db_readers","db.db_writers"]:
    importlib.import_module(m)
print("Imports OK")
PY

echo === 7) Rodar pipeline com DB (le do DB e grava previsoes/value bets)...
echo (Se o DB estiver vazio, a execucao nao vai gerar picks uteis ate voce popular matches/features.)
python db\run_pipeline_db.py

echo === 8) Comando de feedback (pos-jogos):
echo     python -c "from db.feedback_to_db import update_feedback_for_match_result; update_feedback_for_match_result()"

echo.
echo === SETUP CONCLUIDO ===
echo Pastas criadas, arquivos copiados e ambiente pronto.
echo Verifique o arquivo .env e a conexao (DATABASE_URL) antes da proxima execucao.
echo.

:END
popd
endlocal