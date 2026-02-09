# run_pipeline.py
# -*- coding: utf-8 -*-
"""
Pipeline principal:
1) Carrega features do dia (pré-calculadas pelo seu ETL)
2) Carrega/treina modelos conforme necessário
3) Gera previsões e compara com odds de mercado
4) Seleciona value bets e aloca banca (optimizer)
5) Gera relatório (MD/PDF) e envia e-mail

Variáveis de ambiente úteis:
- BANKROLL (float)
- MIN_EDGE (ex.: 0.02)
- KELLY_FACTOR (0-1)
"""
import os
from datetime import datetime
import pandas as pd

from models import FootballModels
from optimizer import select_value_bets, allocate_bankroll
from reporter import save_markdown_report, save_pdf_report
from emailer import send_email


def load_today_features(path_csv: str = 'data/features_today.csv') -> pd.DataFrame:
    if not os.path.exists(path_csv):
        raise FileNotFoundError(f'Arquivo de features do dia não encontrado: {path_csv}')
    df = pd.read_csv(path_csv)
    # garantir alguns tipos
    if 'utcDate' in df.columns:
        df['utcDate'] = pd.to_datetime(df['utcDate'])
    return df


def ensure_models(df_hist: pd.DataFrame) -> FootballModels:
    fm = FootballModels()
    for target in ['match_result','btts','over_2_5']:
        # tenta carregar
        if fm._load_artifact(target) is None:
            print(f'Treinando modelo para {target}...')
            metrics = fm.fit(df_hist.dropna(subset=['home_score','away_score']), target_name=target)
            print(f"{target}: {metrics}")
            fm.save(target)
        else:
            fm.load(target)
    return fm


def run(path_hist: str = 'data/historical_features.csv', path_today: str = 'data/features_today.csv'):
    df_hist = pd.read_csv(path_hist)
    fm = ensure_models(df_hist)

    df_today = load_today_features(path_today)

    # previsões por target principal (resultado FT)
    out = fm.predict(df_today, 'match_result')
    # opcionais
    if set(['btts']).issubset(SUPPORTED_TARGETS):
        try:
            out = fm.predict(out, 'btts')
        except Exception:
            pass
    if set(['over_2_5']).issubset(SUPPORTED_TARGETS):
        try:
            out = fm.predict(out, 'over_2_5')
        except Exception:
            pass

    # selecionar value bets 1X2
    min_edge = float(os.getenv('MIN_EDGE', '0.02'))
    bankroll = float(os.getenv('BANKROLL', '1000'))
    kelly_factor = float(os.getenv('KELLY_FACTOR', '0.5'))

    vb = select_value_bets(out, min_edge=min_edge)
    alloc = allocate_bankroll(vb, bankroll=bankroll, kelly_factor=kelly_factor)

    # relatórios
    md_path = save_markdown_report(out, alloc, notes=f"edge≥{min_edge}, banca={bankroll}, kelly_factor={kelly_factor}")
    try:
        pdf_path = save_pdf_report(out, alloc)
    except Exception:
        pdf_path = None

    # e-mail
    send_email(subject=f"Previsões {datetime.now():%d/%m} ", body_text="Segue relatório das previsões e value bets.",
               attachments=[p for p in [md_path, pdf_path] if p])

    print('Pipeline finalizado.')


if __name__ == '__main__':
    run()
