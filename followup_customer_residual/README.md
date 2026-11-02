# Follow-up Customer Residual — Odoo 19 Enterprise — v7

## Novidades da v7

1. **Itens que não são faturas deixam de desaparecer.**
   Qualquer item em aberto com residual positivo na conta a receber é tratado
   como "a cobrar", seja qual for o tipo de documento: faturas, saldos
   iniciais importados como lançamentos de diário (ex.: série FT A/), recibos
   de venda ou débitos manuais. Na v6 só entravam faturas de cliente
   (`out_invoice`) e os restantes eram descartados, embora contassem no total.

2. **Crédito excedente visível.**
   Se os pagamentos/créditos ultrapassarem a dívida, o valor que sobra aparece
   como linha negativa (no PDF com a indicação "crédito disponível"), para que
   a soma das linhas seja sempre igual ao total.

3. **FIFO correto com "Carregar mais".**
   A alocação é calculada sobre todos os itens em aberto do parceiro, e não
   só sobre o bloco de linhas carregado. As linhas a esconder são retiradas
   depois de o Odoo montar o bloco, sem mexer na paginação nativa.

4. **Ecrã e PDF com as mesmas regras.**
   A lógica está num único sítio (`models/fifo_allocation.py`):
   - agrupado por empresa e moeda da empresa;
   - itens "No Follow-Up" não entram na alocação (no ecrã aparecem com o seu
     próprio valor para poderem ser reativados; no PDF ficam escondidos, como
     no Odoo standard).

## Ecrã Cliente → Em dívida

**Faturas | No Follow-Up | Data da Fatura | Data de Vencimento | Valor**

## PDF (Relatório de acompanhamento)

**Faturas | Data da Fatura | Data de Vencimento | Valor**, com linha final
**Total** igual à soma das linhas mostradas.

## Abatimentos (FIFO)

Pagamentos e créditos não reconciliados não aparecem como linhas próprias e
abatem visualmente os itens mais antigos (vencimento, data da fatura, número,
id). Itens totalmente cobertos deixam de aparecer.

Valores em moeda estrangeira são apresentados na moeda da empresa.

## Importante

Apenas apresentação. Não cria, altera nem reconcilia pagamentos, lançamentos,
notas de crédito ou itens de diário.

## Atualização

1. Substituir completamente a pasta `followup_customer_residual`.
2. Reiniciar o Odoo.
3. Atualizar o módulo.
4. Fazer Ctrl+F5.
5. Testar primeiro em PRE.
