# Follow-up Customer Residual

Módulo personalizado para Odoo 19 Enterprise.

## Funcionalidades

- Personaliza a apresentação dos valores em dívida dos clientes.
- Apresenta todos os valores por cobrar, incluindo faturas, saldos iniciais, recibos e lançamentos manuais.
- Aplica automaticamente os pagamentos e créditos disponíveis às dívidas mais antigas (FIFO).
- Oculta os valores totalmente cobertos por pagamentos ou créditos.
- Apresenta os créditos excedentes como valores negativos.
- Mantém os valores e totais consistentes entre o ecrã e o PDF.
- Converte os valores em moeda estrangeira para a moeda da empresa.

## Apresentação

**Cliente → Em dívida**

`Faturas | No Follow-Up | Data da Fatura | Data de Vencimento | Valor`

**PDF — Relatório de Acompanhamento**

`Faturas | Data da Fatura | Data de Vencimento | Valor`

Inclui uma linha final **Total**, correspondente à soma dos valores apresentados.

## Versão 7

- Corrige a apresentação de documentos que não são faturas.
- Adiciona a visualização de créditos excedentes.
- Corrige o cálculo FIFO quando é utilizada a opção "Carregar mais".
- Uniformiza as regras de cálculo entre o ecrã e o PDF.
- Respeita a opção "No Follow-Up", excluindo esses valores do cálculo FIFO.

## Segurança dos dados

O módulo altera apenas a apresentação dos valores. Não cria, modifica ou reconcilia pagamentos, faturas, notas de crédito ou lançamentos contabilísticos.

## Atualização

1. Substituir a pasta `followup_customer_residual`.
2. Reiniciar o Odoo.
3. Atualizar o módulo.
4. Atualizar o navegador (`Ctrl + F5`).
5. Testar o funcionamento em pré-produção antes de instalar em produção.
