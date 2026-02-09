# reporter.py
# -*- coding: utf-8 -*-
"""
Geração de relatórios (Markdown e PDF) com previsões, value bets e alocação de banca.
- Markdown simples em ./artifacts/reports
- PDF opcional via reportlab
"""
from typing import Optional
import os
from datetime import datetime

import pandas as pd

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm


def _md_section(title: str) -> str:
    return f"\n\n## {title}\n\n"


def save_markdown_report(preds: pd.DataFrame, portfolio: Optional[pd.DataFrame] = None,
                         notes: str = "", out_path: Optional[str] = None) -> str:
    os.makedirs('artifacts/reports', exist_ok=True)
    if out_path is None:
        out_path = os.path.join('artifacts/reports', f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
    lines = [f"# Relatório de Previsões – {datetime.now():%d/%m/%Y %H:%M}"]
    lines.append(_md_section('Jogos e Previsões'))
    cols = [c for c in preds.columns if c in ['match_id','home_team','away_team','utcDate','match_result_proba_2','match_result_proba_1','match_result_proba_0','btts_proba_1','over_2_5_proba_1','odds_home_win','odds_draw','odds_away_win']]
    lines.append(preds[cols].to_markdown(index=False))
    if portfolio is not None and not portfolio.empty:
        lines.append(_md_section('Value Bets / Alocação'))
        lines.append(portfolio.to_markdown(index=False))
    if notes:
        lines.append(_md_section('Notas'))
        lines.append(notes)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return out_path


def save_pdf_report(preds: pd.DataFrame, portfolio: Optional[pd.DataFrame] = None,
                    out_path: Optional[str] = None) -> str:
    os.makedirs('artifacts/reports', exist_ok=True)
    if out_path is None:
        out_path = os.path.join('artifacts/reports', f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    y = height - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, f"Relatório de Previsões – {datetime.now():%d/%m/%Y %H:%M}")
    y -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Jogos e Previsões")
    y -= 0.6*cm
    c.setFont("Helvetica", 9)

    def draw_table(df: pd.DataFrame, y: float, max_rows: int = 25) -> float:
        cols = list(df.columns)
        col_w = (width - 4*cm) / len(cols)
        # header
        c.setFillColor(colors.lightgrey)
        c.rect(2*cm, y-0.5*cm, (width-4*cm), 0.5*cm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        for i, col in enumerate(cols):
            c.drawString(2*cm + i*col_w + 2, y-0.35*cm, str(col)[:18])
        y -= 0.6*cm
        # rows
        for _, row in df.head(max_rows).iterrows():
            for i, col in enumerate(cols):
                c.drawString(2*cm + i*col_w + 2, y, str(row[col])[:18])
            y -= 0.45*cm
            if y < 3*cm:
                c.showPage(); y = height - 2*cm
        return y

    preds_cols = [c for c in preds.columns if c in ['match_id','home_team','away_team','utcDate','match_result_proba_2','match_result_proba_1','match_result_proba_0','odds_home_win','odds_draw','odds_away_win']]
    y = draw_table(preds[preds_cols], y)

    if portfolio is not None and not portfolio.empty:
        c.setFont("Helvetica-Bold", 12)
        y -= 0.5*cm
        c.drawString(2*cm, y, "Value Bets / Alocação")
        y -= 0.6*cm
        y = draw_table(portfolio, y)

    c.save()
    return out_path

