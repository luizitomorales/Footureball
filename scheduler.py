# scheduler.py
# -*- coding: utf-8 -*-
"""
Agendador simples:
- Duas opções: (1) loop local com horários fixos; (2) instruções para crontab.
Use `run_pipeline.py` como entrypoint.
"""
import time
from datetime import datetime
from typing import Callable, List


def run_daily(hours: List[int], job: Callable, *args, **kwargs):
    """Executa `job` diariamente nos horários (0-23) informados."""
    print(f"Agendador iniciando. Horários: {hours}")
    while True:
        now = datetime.now()
        if now.minute == 0 and now.hour in hours:
            try:
                print(f"[{now:%Y-%m-%d %H:%M}] Executando job...")
                job(*args, **kwargs)
                print(f"[{datetime.now():%Y-%m-%d %H:%M}] Job concluído.")
                time.sleep(60)  # evitar múltiplas execuções no mesmo minuto
            except Exception as e:
                print(f"Erro no job: {e}")
        time.sleep(5)

# Instrução para cron (Linux):
# $ crontab -e
# 0 7,11,16 * * * /usr/bin/python3 /caminho/para/run_pipeline.py >> /var/log/pred_fut.log 2>&1

