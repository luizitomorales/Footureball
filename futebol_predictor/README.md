# Documentação 
# Pred-Fut – Pipeline

## Estrutura
- `etl.py`: gera `data/historical_features.csv` e `data/features_today.csv`.
- `models.py`, `optimizer.py`, `llm_integration.py`, `reporter.py`, `emailer.py`, `feedback.py`, `scheduler.py`, `run_pipeline.py`.
- `data/raw/`: coloque aqui seus arquivos brutos (json/csv).
- `artifacts/`: modelos, relatórios e feedback.

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt