import numpy as np
import pandas as pd
from datetime import datetime

np.random.seed(42)

# 1) Parâmetros e dimensões base
inicio = pd.Timestamp("2020-01-01")
fim = pd.Timestamp("2024-12-31")
datas_diarias = pd.date_range(inicio, fim, freq="D")
meses = pd.date_range(inicio, fim, freq="ME")

categorias_fluxo = ["Vendas", "Salários", "Fornecedores", "Marketing", "Impostos"]
centros = ["RH", "Comercial", "Operacional", "Administrativo"]
pagamentos = ["Cartão", "Pix", "Transferência", "Boleto"]

clientes = ["Cliente A", "Cliente B", "Cliente C", "Cliente D", "Cliente E"]
produtos = ["Consultoria", "Projeto", "Licença", "Suporte"]
recebimentos = ["Pix", "Transferência", "Cartão", "Boleto"]

categorias_despesas = ["Infraestrutura", "Pessoal", "Aluguel", "Serviços", "Marketing"]
tipo_despesa = ["Fixa", "Variável"]

# 2) Funções auxiliares
def sazonalidade_mensal(dt):
    # Sazonalidade: picos em mar/jun/set/dez
    m = dt.month
    base = 1.0
    if m in [3, 6, 9, 12]:
        base += 0.15
    if m in [1, 7]:
        base -= 0.05
    return base

def gerar_valor(categoria, entrada=True):
    # Faixas por categoria
    if entrada:
        if categoria == "Vendas":  # receitas operacionais
            return np.random.normal(4200, 900)
        if categoria == "Fornecedores":  # ajustes/estornos/adiantamentos
            return np.random.normal(1800, 600)
        if categoria == "Impostos":
            return np.random.normal(1500, 500)
        if categoria == "Marketing":
            return np.random.normal(1200, 400)
        if categoria == "Salários":
            return np.random.normal(800, 300)  # raro, ex: reembolsos
    else:
        if categoria == "Salários":
            return np.random.normal(3200, 700)
        if categoria == "Fornecedores":
            return np.random.normal(2400, 800)
        if categoria == "Marketing":
            return np.random.normal(1400, 500)
        if categoria == "Impostos":
            return np.random.normal(1700, 600)
        if categoria == "Vendas":
            return np.random.normal(900, 300)  # estornos/descontos

    return np.random.normal(1500, 500)

def clip_positivo(x):
    return float(max(x, 150))  # evita valores muito pequenos ou negativos

def clip_negativo(x):
    return float(max(x, 150))  # magnitude minima; sinal será aplicado depois

# 3) Fluxo de caixa diário
registros_fluxo = []
saldo = 0.0

for dt in datas_diarias:
    # Sazonalidade sugere mais entradas em determinados meses
    fator = sazonalidade_mensal(dt)

    # Definir número de movimentos por dia
    n_mov = np.random.choice([2,3,4,5], p=[0.15, 0.35, 0.35, 0.15])

    for _ in range(n_mov):
        cat = np.random.choice(categorias_fluxo)
        cc = np.random.choice(centros)
        fp = np.random.choice(pagamentos)

        # Probabilidade de ser entrada x saída por categoria
        if cat == "Vendas":
            prob_entrada = 0.75
        elif cat == "Salários":
            prob_entrada = 0.08
        elif cat == "Fornecedores":
            prob_entrada = 0.30
        elif cat == "Marketing":
            prob_entrada = 0.20
        elif cat == "Impostos":
            prob_entrada = 0.25
        else:
            prob_entrada = 0.5

        entrada = np.random.rand() < prob_entrada

        val = gerar_valor(cat, entrada=entrada) * fator
        if entrada:
            val = clip_positivo(val)
            saldo += val
            registros_fluxo.append([dt.date(), "Entrada", cat, cc, fp, round(val,2), round(saldo,2)])
        else:
            val = clip_negativo(val)
            val = -val
            saldo += val
            registros_fluxo.append([dt.date(), "Saída", cat, cc, fp, round(val,2), round(saldo,2)])

fluxo_caixa = pd.DataFrame(registros_fluxo, columns=[
    "data","tipo","categoria","centro_custo","forma_pagamento","valor","saldo_acumulado"
])

# 4) Despesas diárias (negativas, fixas/variáveis)
registros_desp = []
for dt in datas_diarias:
    n = np.random.choice([1,2,3], p=[0.4, 0.45, 0.15])
    fator = sazonalidade_mensal(dt)
    for _ in range(n):
        cat = np.random.choice(categorias_despesas)
        cc = np.random.choice(centros)
        td = np.random.choice(tipo_despesa)
        base = {
            "Infraestrutura": np.random.normal(2800, 900),
            "Pessoal": np.random.normal(2000, 700),
            "Aluguel": np.random.normal(2400, 500),
            "Serviços": np.random.normal(2200, 800),
            "Marketing": np.random.normal(1800, 700),
        }[cat] * fator

        valor = -clip_negativo(base)
        registros_desp.append([dt.date(), cat, cc, td, round(valor,2)])

despesas = pd.DataFrame(registros_desp, columns=[
    "data","categoria","centro_custo","tipo_despesa","valor"
])

# 5) Receitas mensais (positivas) por cliente/produto
registros_rec = []
for m in meses:
    fator = sazonalidade_mensal(m)
    n = np.random.choice([3,4,5,6], p=[0.2,0.35,0.3,0.15])  # número de lançamentos mensais
    for _ in range(n):
        cli = np.random.choice(clientes)
        prod = np.random.choice(produtos)
        fr = np.random.choice(recebimentos)
        base = {
            "Consultoria": np.random.normal(18000, 4500),
            "Projeto": np.random.normal(14000, 4000),
            "Licença": np.random.normal(16000, 5000),
            "Suporte": np.random.normal(12000, 3500),
        }[prod] * fator

        valor = clip_positivo(base)
        registros_rec.append([m.date(), cli, prod, fr, round(valor,2)])

receitas = pd.DataFrame(registros_rec, columns=[
    "data","cliente","produto_servico","forma_recebimento","valor"
])

# 6) Orçado vs Realizado mensal
registros_orcado = []
for m in meses:
    # Define categoria do mês alternando Receita/Despesa e/ou usando ambos
    # Para simplicidade: criamos sempre uma linha de Receita e uma de Despesa por mês
    for categoria in ["Receita","Despesa"]:
        fator = sazonalidade_mensal(m)
        if categoria == "Receita":
            orcado = np.random.normal(28000, 5000) * fator
            realizado = orcado * np.random.normal(1.0, 0.12)  # variação
        else:
            orcado = np.random.normal(24000, 4000) * fator
            realizado = orcado * np.random.normal(1.03, 0.10)

        orcado = max(orcado, 8000)
        realizado = max(realizado, 6000)
        desvio = ((realizado - orcado) / orcado) * 100.0

        registros_orcado.append([m.date(), categoria, round(orcado,2), round(realizado,2), round(desvio,2)])

orcado_vs_realizado = pd.DataFrame(registros_orcado, columns=[
    "mes","categoria","valor_orcado","valor_realizado","desvio_percentual"
])

# 7) Padronizações finais
# Fluxo de caixa: entradas positivas, saídas negativas já foram aplicadas; saldo já acumulado
# Despesas: garantir negativas
despesas["valor"] = -abs(despesas["valor"])
# Receitas: garantir positivas
receitas["valor"] = abs(receitas["valor"])

# 8) Exportar para Excel e CSV
fluxo_caixa.to_csv("fluxo_caixa.csv", index=False)
despesas.to_csv("despesas.csv", index=False)
receitas.to_csv("receitas.csv", index=False)
orcado_vs_realizado.to_csv("orcado_vs_realizado.csv", index=False)

with pd.ExcelWriter("fluxo_caixa.xlsx", engine="xlsxwriter") as w:
    fluxo_caixa.to_excel(w, index=False)

with pd.ExcelWriter("despesas.xlsx", engine="xlsxwriter") as w:
    despesas.to_excel(w, index=False)

with pd.ExcelWriter("receitas.xlsx", engine="xlsxwriter") as w:
    receitas.to_excel(w, index=False)

with pd.ExcelWriter("orcado_vs_realizado.xlsx", engine="xlsxwriter") as w:
    orcado_vs_realizado.to_excel(w, index=False)

print("Arquivos gerados: fluxo_caixa.csv/.xlsx, despesas.csv/.xlsx, receitas.csv/.xlsx, orcado_vs_realizado.csv/.xlsx")
