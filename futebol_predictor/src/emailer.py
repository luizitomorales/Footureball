# emailer.py
# -*- coding: utf-8 -*-
"""
Envio de relatórios por e-mail (SMTP/TLS).
Config via variáveis de ambiente:
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
- EMAIL_FROM, EMAIL_TO (lista separada por vírgula), EMAIL_SUBJECT_PREFIX
"""
import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def send_email(subject: str, body_text: str, attachments=None) -> None:
    attachments = attachments or []
    host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    port = int(os.getenv('SMTP_PORT', '587'))
    user = os.getenv('SMTP_USER')
    pwd = os.getenv('SMTP_PASS')
    sender = os.getenv('EMAIL_FROM', user)
    to_list = [x.strip() for x in os.getenv('EMAIL_TO','').split(',') if x.strip()]
    prefix = os.getenv('EMAIL_SUBJECT_PREFIX', '[Pred-Fut] ')

    if not (user and pwd and to_list):
        print('Config SMTP/E-mail incompleta; pulando envio.')
        return

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ", ".join(to_list)
    msg['Subject'] = f"{prefix}{subject}"
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

    for path in attachments:
        if not os.path.exists(path):
            continue
        part = MIMEBase('application', 'octet-stream')
        with open(path, 'rb') as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(path)}"')
        msg.attach(part)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
        print(f'E-mail enviado para: {to_list}')

