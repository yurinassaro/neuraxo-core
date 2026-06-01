# -*- coding: utf-8 -*-
"""Notificacao de falha por email (SMTP)."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

logger = logging.getLogger(__name__)


def notificar_resultado(relatorio: dict) -> bool:
    """Envia email se houver falhas (e config.NOTIFY_EMAIL_TO setado).

    relatorio: {data, total, sucessos, falhas, cenarios: [{id, nome, sucesso, motivo, duracao_s}]}
    Retorna True se enviou.
    """
    if not config.NOTIFY_EMAIL_TO:
        logger.info("NOTIFY_EMAIL_TO vazio - pulando email")
        return False

    qtd_falhas = relatorio.get('falhas', 0)
    if config.NOTIFY_ON_FAILURE_ONLY and qtd_falhas == 0:
        logger.info("Tudo OK e NOTIFY_ON_FAILURE_ONLY=True - pulando email")
        return False

    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        logger.warning("SMTP nao configurado - nao consigo enviar")
        return False

    assunto = f"[Neuraxo E2E] {qtd_falhas} cenario(s) falhou — {relatorio.get('data', 'sem data')}"
    if qtd_falhas == 0:
        assunto = f"[Neuraxo E2E] OK — todos os {relatorio.get('total')} passaram"

    corpo_html = _montar_html(relatorio)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = assunto
    msg['From'] = config.SMTP_FROM
    msg['To'] = config.NOTIFY_EMAIL_TO
    msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("Email enviado para %s", config.NOTIFY_EMAIL_TO)
        return True
    except Exception:
        logger.exception("Erro ao enviar email")
        return False


def _montar_html(rel: dict) -> str:
    linhas = []
    for c in rel.get('cenarios', []):
        cor = '#16a34a' if c['sucesso'] else '#dc2626'
        emoji = '✓' if c['sucesso'] else '✗'
        linhas.append(
            f"<tr style='border-bottom:1px solid #eee;'>"
            f"<td style='padding:6px 12px;color:{cor};font-weight:bold;'>{emoji}</td>"
            f"<td style='padding:6px 12px;'>{c['id']} - {c['nome']}</td>"
            f"<td style='padding:6px 12px;color:#6b7280;'>{c.get('duracao_s', '?')}s</td>"
            f"<td style='padding:6px 12px;font-size:.9em;'>{c.get('motivo', '')[:200]}</td>"
            f"</tr>"
        )
    return f"""
    <h2>Relatório E2E NeuraxoCheck — {rel.get('data')}</h2>
    <p>
      <strong>Total:</strong> {rel.get('total', 0)} •
      <span style="color:#16a34a;">Sucessos: {rel.get('sucessos', 0)}</span> •
      <span style="color:#dc2626;">Falhas: {rel.get('falhas', 0)}</span>
    </p>
    <table style="border-collapse:collapse;font-family:sans-serif;font-size:.95em;">
      <thead><tr style="background:#f3f4f6;">
        <th style="padding:8px 12px;text-align:left;">St</th>
        <th style="padding:8px 12px;text-align:left;">Cenário</th>
        <th style="padding:8px 12px;text-align:left;">Tempo</th>
        <th style="padding:8px 12px;text-align:left;">Motivo</th>
      </tr></thead>
      <tbody>{''.join(linhas)}</tbody>
    </table>
    """
