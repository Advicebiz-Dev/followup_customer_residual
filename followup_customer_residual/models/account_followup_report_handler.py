# -*- coding: utf-8 -*-

from odoo import _, fields, models

from .fifo_allocation import allocate_fifo, get_open_receivable_amls


class AccountFollowupReportHandler(models.AbstractModel):
    _inherit = "account.followup.report.handler"

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options)

        # Mantém o cabeçalho nativo (incluindo "No Follow-Up") e reduz apenas
        # as colunas de dados.
        wanted = {
            "invoice_date": _("Data da Fatura"),
            "date_maturity": _("Data de Vencimento"),
            "amount": _("Valor"),
        }

        current = {
            col.get("expression_label"): col
            for col in options.get("columns", [])
        }

        options["columns"] = [
            {**current[label], "name": wanted[label]}
            for label in ("invoice_date", "date_maturity", "amount")
            if label in current
        ]

        # Não definir column_headers aqui: o PartnerLedgerFollowupHeader
        # standard trata do cabeçalho e evita a duplicação.

    # ------------------------------------------------------------------
    # FIFO
    # ------------------------------------------------------------------

    def _fifo_companies(self, options):
        company_ids = [c.get("id") for c in options.get("companies", []) if c.get("id")]
        companies = self.env["res.company"].browse(company_ids)
        return companies or self.env.companies

    def _fifo_display_amounts(self, options, aml_results):
        """Alocação FIFO calculada sobre TODOS os itens em aberto do parceiro,
        e não só sobre o bloco de linhas recebido. Assim o resultado é o mesmo
        quando o relatório carrega as linhas em vários blocos ("Carregar mais").
        """
        aml_ids = [row.get("id") for row in aml_results if row.get("id")]
        amls = self.env["account.move.line"].browse(aml_ids).exists()
        partner = amls[:1].partner_id
        if not partner:
            return {}

        date_to = (options.get("date") or {}).get("date_to")
        all_open = get_open_receivable_amls(
            self.env,
            partner,
            self._fifo_companies(options),
            date_to=fields.Date.to_date(date_to) if date_to else None,
        )
        return allocate_fifo(all_open)

    def _fifo_line_aml_id(self, report, line):
        try:
            return report._get_res_id_from_line_id(line.get("id"), "account.move.line")
        except Exception:
            return None

    def _get_partner_aml_report_lines(
        self,
        report,
        options,
        partner_line_id,
        aml_results,
        progress,
        offset=0,
        level_shift=0,
    ):
        display = self._fifo_display_amounts(options, aml_results)

        # Passa ao Odoo TODAS as linhas do bloco (só com o valor ajustado),
        # para não mexer na paginação nativa (offset, contagem e "Carregar
        # mais"). As linhas a esconder são retiradas depois.
        rows = []
        hidden_ids = set()
        for raw in aml_results:
            aml_id = raw.get("id")
            if aml_id in display:
                values = dict(raw)
                amount = display[aml_id]
                values["amount"] = amount
                values["balance"] = amount
                values["amount_currency"] = amount
                rows.append(values)
            else:
                hidden_ids.add(aml_id)
                rows.append(raw)

        # Odoo 19 devolve um tuplo de 4 elementos:
        # (lines, next_progress, treated_results_count, has_more).
        lines, next_progress, treated_results_count, has_more = super()._get_partner_aml_report_lines(
            report,
            options,
            partner_line_id,
            rows,
            progress,
            offset=offset,
            level_shift=level_shift,
        )

        if hidden_ids:
            lines = [
                line for line in lines
                if self._fifo_line_aml_id(report, line) not in hidden_ids
            ]

        return lines, next_progress, treated_results_count, has_more
