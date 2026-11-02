# -*- coding: utf-8 -*-
"""Lógica FIFO partilhada pelo ecrã (handler) e pelo PDF (carta).

Apenas apresentação: não cria, altera nem reconcilia registos contabilísticos.
"""

import datetime
from collections import defaultdict

_DATE_MAX = datetime.date.max


def fifo_sort_key(aml):
    """Mais antigo primeiro: vencimento, data da fatura, nome, id."""
    return (
        aml.date_maturity or aml.date or _DATE_MAX,
        aml.move_id.invoice_date or aml.date or _DATE_MAX,
        aml.move_id.name or "",
        aml.id,
    )


def get_open_receivable_amls(env, partner, companies, date_to=None):
    """Todos os itens em aberto da conta a receber do parceiro.

    Inclui faturas, lançamentos de diário (ex.: saldos iniciais importados),
    recibos, notas de crédito e pagamentos, sem filtrar por tipo de documento.
    """
    domain = [
        ("partner_id", "=", partner.id),
        ("account_id.account_type", "=", "asset_receivable"),
        ("parent_state", "=", "posted"),
        ("reconciled", "=", False),
        ("company_id", "in", companies.ids),
    ]
    if date_to:
        domain.append(("date", "<=", date_to))
    return env["account.move.line"].search(domain)


def allocate_fifo(amls):
    """Calcula o valor a mostrar por item.

    Regras (iguais no ecrã e no PDF):
    - Qualquer item com residual positivo é "a cobrar", seja qual for o
      tipo de documento.
    - Itens com residual negativo (pagamentos, notas de crédito, créditos
      manuais) formam um saldo que abate os itens a cobrar mais antigos.
    - Itens marcados "No Follow-Up" não entram na alocação: ficam com o seu
      próprio residual (o PDF esconde-os, como no Odoo standard).
    - Agrupado por empresa e moeda da empresa (amount_residual).
    - Se sobrar crédito, fica associado ao crédito mais recente, como valor
      negativo, para que a soma das linhas bata sempre com o total.

    Devolve {aml_id: valor_a_mostrar}. Itens ausentes do dicionário são
    escondidos (créditos totalmente usados e faturas totalmente cobertas).
    """
    display = {}
    groups = defaultdict(lambda: {"debits": [], "credits": [], "currency": None})

    for aml in amls:
        currency = aml.company_currency_id or aml.company_id.currency_id
        residual = aml.amount_residual
        if currency.is_zero(residual):
            continue

        if aml.no_followup:
            display[aml.id] = residual
            continue

        group = groups[(aml.company_id.id, currency.id)]
        group["currency"] = currency
        if residual > 0:
            group["debits"].append(aml)
        else:
            group["credits"].append(aml)

    for group in groups.values():
        currency = group["currency"]
        pool = currency.round(sum(-aml.amount_residual for aml in group["credits"]))

        for aml in sorted(group["debits"], key=fifo_sort_key):
            remaining = aml.amount_residual
            if pool > 0:
                applied = min(remaining, pool)
                remaining = currency.round(remaining - applied)
                pool = currency.round(pool - applied)
            if not currency.is_zero(remaining):
                display[aml.id] = remaining

        if group["credits"] and not currency.is_zero(pool):
            carrier = max(group["credits"], key=fifo_sort_key)
            display[carrier.id] = -pool

    return display
