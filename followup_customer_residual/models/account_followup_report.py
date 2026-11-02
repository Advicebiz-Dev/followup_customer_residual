# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import _, models
from odoo.tools.misc import formatLang, format_date, get_lang

from .fifo_allocation import allocate_fifo, fifo_sort_key, get_open_receivable_amls


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_followup_report_columns_name(self):
        return [
            {
                "name": _("Faturas"),
                "style": "text-align:left; white-space:nowrap;",
            },
            {
                "name": _("Data da Fatura"),
                "class": "date",
                "style": "text-align:center; white-space:nowrap;",
            },
            {
                "name": _("Data de Vencimento"),
                "class": "date",
                "style": "text-align:center; white-space:nowrap;",
            },
            {
                "name": _("Valor"),
                "class": "number o_price_total",
                "style": "text-align:right; white-space:nowrap;",
            },
        ]

    def _get_followup_report_lines(self, options):
        """Tabela do PDF/carta com a mesma alocação FIFO do ecrã.

        Faturas | Data da Fatura | Data de Vencimento | Valor
        e uma linha final "Total" igual à soma das linhas mostradas.

        Apenas apresentação; nenhum registo contabilístico é alterado.
        """
        partner = options.get("partner_id") and self.env["res.partner"].browse(options["partner_id"])
        if not partner:
            return []

        lang_code = partner.lang or get_lang(self.env).code
        companies = self.env["res.company"].search([
            ("id", "child_of", self.env.context.get("allowed_company_ids", self.env.company.id))
        ])

        all_open = get_open_receivable_amls(self.env, partner, companies)
        display = allocate_fifo(all_open)

        # Como no Odoo standard, a carta não mostra itens "No Follow-Up".
        shown = all_open.filtered(lambda aml: aml.id in display and not aml.no_followup)

        grouped = defaultdict(list)
        for aml in shown:
            currency = aml.company_currency_id or aml.company_id.currency_id
            grouped[currency].append(aml)

        lines = []
        line_num = 0

        for currency, amls in grouped.items():
            currency_total = 0.0

            for aml in sorted(amls, key=fifo_sort_key):
                amount = display[aml.id]
                currency_total += amount
                line_num += 1

                name = aml.move_id.name
                if amount < 0:
                    name = _("%s (crédito disponível)", name)

                invoice_date = {
                    "name": format_date(
                        self.env,
                        aml.move_id.invoice_date or aml.date,
                        lang_code=lang_code,
                    ),
                    "class": "date",
                    "style": "white-space:nowrap;text-align:left;",
                    "template": "account_followup.line_template",
                }

                due_date = {
                    "name": format_date(
                        self.env,
                        aml.date_maturity,
                        lang_code=lang_code,
                    ),
                    "class": "date",
                    "style": "white-space:nowrap;text-align:left;",
                    "template": "account_followup.line_template",
                }

                amount_col = {
                    "name": formatLang(self.env, amount, currency_obj=currency),
                    "style": "text-align:right; white-space:normal;",
                    "template": "account_followup.line_template",
                }

                lines.append({
                    "id": aml.id,
                    "account_move": aml.move_id,
                    "name": name,
                    "move_id": aml.move_id.id,
                    "type": "unreconciled_aml",
                    "unfoldable": False,
                    "columns": [invoice_date, due_date, amount_col],
                })

            currency_total = currency.round(currency_total)
            if not currency.is_zero(currency_total):
                line_num += 1
                lines.append({
                    "id": line_num,
                    "name": _("Total"),
                    "class": "total",
                    "style": "border-top-style: double",
                    "unfoldable": False,
                    "level": 3,
                    "columns": [
                        {"name": "", "template": "account_followup.line_template"},
                        {"name": "", "template": "account_followup.line_template"},
                        {
                            "name": formatLang(self.env, currency_total, currency_obj=currency),
                            "style": "text-align:right; white-space:normal; font-weight:bold;",
                            "template": "account_followup.line_template",
                        },
                    ],
                })

        return lines
