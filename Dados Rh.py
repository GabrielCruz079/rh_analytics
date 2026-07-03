# ============================================
# PROJETO: Análise de RH — Turnover e Gestão de Pessoas
# Script: EDA + Geração Automática de Gráficos
# Autor: Gabriel Ramos Cruz
# ============================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import pymysql
import os

# ============================================
# CONFIGURAÇÕES VISUAIS
# ============================================
plt.rcParams.update({
    'figure.facecolor': '#1e1e2e',
    'axes.facecolor':   '#1e1e2e',
    'axes.edgecolor':   '#444466',
    'axes.labelcolor':  '#ccccdd',
    'xtick.color':      '#ccccdd',
    'ytick.color':      '#ccccdd',
    'text.color':       '#ccccdd',
    'grid.color':       '#333355',
    'grid.linestyle':   '--',
    'grid.alpha':       0.4,
    'font.family':      'DejaVu Sans',
    'font.size':        11,
})

VERDE   = '#00d68f'
AZUL    = '#3b8bff'
ROXO    = '#a78bfa'
LARANJA = '#f59e0b'
VERMELHO= '#ef4444'
CORES   = [VERDE, AZUL, ROXO, LARANJA, VERMELHO, '#06b6d4', '#ec4899', '#84cc16']

# Pasta de saída
os.makedirs('graficos', exist_ok=True)
print("📁 Pasta 'graficos/' criada.")

# ============================================
# CONEXÃO E EXTRAÇÃO DE DADOS
# ============================================
print("\n🔄 Conectando ao banco...")
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',        # sua senha aqui
    database='rh_analytics',
    charset='utf8mb4'
)

# DataFrame principal
df = pd.read_sql("""
    SELECT
        f.funcionario_id,
        f.nome,
        f.genero,
        f.idade,
        f.nivel_educacao,
        f.salario,
        f.status,
        f.satisfacao,
        f.avaliacao_desempenho,
        f.horas_extras_mes,
        f.distancia_km,
        f.data_admissao,
        f.data_demissao,
        d.nome          AS departamento,
        c.nome          AS cargo,
        c.nivel         AS nivel_cargo
    FROM funcionarios f
    JOIN departamentos d ON f.departamento_id = d.departamento_id
    JOIN cargos c        ON f.cargo_id = c.cargo_id
""", conn)

# DataFrame turnover
df_turnover = pd.read_sql("""
    SELECT
        h.motivo_saida,
        h.tipo,
        h.tempo_empresa,
        h.salario,
        h.data_saida,
        d.nome AS departamento,
        c.nivel AS nivel_cargo
    FROM historico_turnover h
    JOIN departamentos d ON h.departamento_id = d.departamento_id
    JOIN cargos c        ON h.cargo_id = c.cargo_id
""", conn)

conn.close()
print(f"✅ Dados carregados — {len(df)} funcionários | {len(df_turnover)} desligamentos\n")

print("📊 Gerando gráfico 1 — Taxa de Turnover Geral...")

ativos     = (df['status'] == 'Ativo').sum()
desligados = (df['status'] == 'Desligado').sum()
taxa       = desligados / len(df) * 100

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Visão Geral — Turnover da Empresa', fontsize=15, fontweight='bold', color='white', y=1.02)

# Pizza
axes[0].pie(
    [ativos, desligados],
    labels=['Ativos', 'Desligados'],
    colors=[VERDE, VERMELHO],
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops={'edgecolor': '#1e1e2e', 'linewidth': 2},
    textprops={'color': 'white', 'fontsize': 12}
)
axes[0].set_title('Distribuição de Status', color='white', fontsize=12)

# KPIs textuais
axes[1].axis('off')
kpis = [
    ('Total de Funcionários', f'{len(df)}', AZUL),
    ('Funcionários Ativos',   f'{ativos}', VERDE),
    ('Desligamentos',         f'{desligados}', VERMELHO),
    ('Taxa de Turnover',      f'{taxa:.1f}%', LARANJA),
]
for idx, (label, valor, cor) in enumerate(kpis):
    y = 0.75 - idx * 0.18
    axes[1].text(0.1, y, label, fontsize=11, color='#aaaacc', transform=axes[1].transAxes)
    axes[1].text(0.1, y - 0.07, valor, fontsize=22, fontweight='bold', color=cor, transform=axes[1].transAxes)

plt.tight_layout()
plt.savefig('graficos/01_turnover_geral.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/01_turnover_geral.png")

print("📊 Gerando gráfico 2 — Turnover por Departamento...")

turnover_dept = df.groupby('departamento').apply(
    lambda x: (x['status'] == 'Desligado').sum() / len(x) * 100
).reset_index()
turnover_dept.columns = ['departamento', 'taxa_turnover']
turnover_dept = turnover_dept.sort_values('taxa_turnover', ascending=True)

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(turnover_dept['departamento'], turnover_dept['taxa_turnover'],
               color=[VERMELHO if t > 25 else LARANJA if t > 15 else VERDE
                      for t in turnover_dept['taxa_turnover']],
               edgecolor='none', height=0.6)

ax.axvline(x=25, color='white', linestyle='--', alpha=0.5, linewidth=1.2, label='Alerta (25%)')
for bar, val in zip(bars, turnover_dept['taxa_turnover']):
    ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
            f'{val:.1f}%', va='center', fontsize=10, color='white')

ax.set_title('Taxa de Turnover por Departamento', fontsize=14, fontweight='bold', color='white', pad=15)
ax.set_xlabel('Taxa de Turnover (%)', color='#aaaacc')
ax.legend(facecolor='#2a2a3e', edgecolor='#444466', labelcolor='white')
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('graficos/02_turnover_departamento.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/02_turnover_departamento.png")

print("📊 Gerando gráfico 3 — Motivos de Saída...")

motivos = df_turnover['motivo_saida'].value_counts()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Análise dos Motivos de Desligamento', fontsize=14, fontweight='bold', color='white')

axes[0].pie(motivos.values, labels=motivos.index, colors=CORES,
            autopct='%1.1f%%', startangle=90,
            wedgeprops={'edgecolor': '#1e1e2e', 'linewidth': 2},
            textprops={'color': 'white', 'fontsize': 9})
axes[0].set_title('Distribuição por Motivo', color='white')

tipo = df_turnover['tipo'].value_counts()
axes[1].bar(tipo.index, tipo.values, color=[VERDE, VERMELHO], edgecolor='none', width=0.5)
for i, (idx, val) in enumerate(zip(tipo.index, tipo.values)):
    axes[1].text(i, val + 1, str(val), ha='center', fontsize=12, color='white', fontweight='bold')
axes[1].set_title('Voluntário vs Involuntário', color='white')
axes[1].set_ylabel('Quantidade', color='#aaaacc')
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('graficos/03_motivos_saida.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/03_motivos_saida.png")

print("📊 Gerando gráfico 4 — Satisfação vs Turnover...")

sat_turnover = df.groupby('satisfacao').apply(
    lambda x: (x['status'] == 'Desligado').sum() / len(x) * 100
).reset_index()
sat_turnover.columns = ['satisfacao', 'taxa_turnover']

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Satisfação dos Colaboradores × Turnover', fontsize=14, fontweight='bold', color='white')

cores_sat = [VERMELHO, LARANJA, '#facc15', AZUL, VERDE]
axes[0].bar(sat_turnover['satisfacao'], sat_turnover['taxa_turnover'],
            color=cores_sat, edgecolor='none', width=0.6)
for _, row in sat_turnover.iterrows():
    axes[0].text(row['satisfacao'], row['taxa_turnover'] + 0.5,
                 f"{row['taxa_turnover']:.1f}%", ha='center', fontsize=10, color='white')
axes[0].set_title('Taxa de Turnover por Nível de Satisfação', color='white')
axes[0].set_xlabel('Satisfação (1=Muito Insatisfeito | 5=Muito Satisfeito)', color='#aaaacc')
axes[0].set_ylabel('Taxa de Turnover (%)', color='#aaaacc')
axes[0].grid(axis='y', alpha=0.3)

sat_dist = df['satisfacao'].value_counts().sort_index()
axes[1].bar(sat_dist.index, sat_dist.values, color=cores_sat, edgecolor='none', width=0.6)
for i, val in enumerate(sat_dist.values):
    axes[1].text(i + 1, val + 2, str(val), ha='center', fontsize=10, color='white')
axes[1].set_title('Distribuição de Satisfação (todos)', color='white')
axes[1].set_xlabel('Nível de Satisfação', color='#aaaacc')
axes[1].set_ylabel('Nº de Funcionários', color='#aaaacc')
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('graficos/04_satisfacao_turnover.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/04_satisfacao_turnover.png")

print("📊 Gerando gráfico 5 — Perfil do Colaborador que Sai...")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Perfil do Colaborador Desligado', fontsize=14, fontweight='bold', color='white')

# Por gênero
genero_turn = df.groupby('genero').apply(
    lambda x: (x['status'] == 'Desligado').sum() / len(x) * 100
).reset_index()
genero_turn.columns = ['genero', 'taxa']
axes[0].bar(genero_turn['genero'], genero_turn['taxa'], color=[AZUL, ROXO], edgecolor='none', width=0.5)
for _, row in genero_turn.iterrows():
    axes[0].text(row['genero'], row['taxa'] + 0.5, f"{row['taxa']:.1f}%", ha='center', color='white', fontsize=11)
axes[0].set_title('Por Gênero', color='white')
axes[0].set_ylabel('Taxa de Turnover (%)', color='#aaaacc')
axes[0].grid(axis='y', alpha=0.3)

# Por faixa etária
df['faixa_etaria'] = pd.cut(df['idade'], bins=[17, 25, 35, 45, 55, 65],
                             labels=['18-25', '26-35', '36-45', '46-55', '56+'])
faixa_turn = df.groupby('faixa_etaria', observed=True).apply(
    lambda x: (x['status'] == 'Desligado').sum() / len(x) * 100
).reset_index()
faixa_turn.columns = ['faixa', 'taxa']
axes[1].bar(faixa_turn['faixa'].astype(str), faixa_turn['taxa'],
            color=CORES[:5], edgecolor='none', width=0.6)
for _, row in faixa_turn.iterrows():
    axes[1].text(str(row['faixa']), row['taxa'] + 0.5,
                 f"{row['taxa']:.1f}%", ha='center', color='white', fontsize=10)
axes[1].set_title('Por Faixa Etária', color='white')
axes[1].set_ylabel('Taxa de Turnover (%)', color='#aaaacc')
axes[1].grid(axis='y', alpha=0.3)

# Por nível de cargo
nivel_turn = df.groupby('nivel_cargo').apply(
    lambda x: (x['status'] == 'Desligado').sum() / len(x) * 100
).reset_index()
nivel_turn.columns = ['nivel', 'taxa']
nivel_ordem = ['Júnior', 'Pleno', 'Sênior', 'Gerente', 'Diretor']
nivel_turn['nivel'] = pd.Categorical(nivel_turn['nivel'], categories=nivel_ordem, ordered=True)
nivel_turn = nivel_turn.sort_values('nivel')
axes[2].bar(nivel_turn['nivel'].astype(str), nivel_turn['taxa'],
            color=CORES[:5], edgecolor='none', width=0.6)
for _, row in nivel_turn.iterrows():
    axes[2].text(str(row['nivel']), row['taxa'] + 0.5,
                 f"{row['taxa']:.1f}%", ha='center', color='white', fontsize=10)
axes[2].set_title('Por Nível de Cargo', color='white')
axes[2].set_ylabel('Taxa de Turnover (%)', color='#aaaacc')
axes[2].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('graficos/05_perfil_desligado.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/05_perfil_desligado.png")

print("📊 Gerando gráfico 6 — Custo do Turnover por Departamento...")

custo_dept = df_turnover.groupby('departamento').agg(
    total_desligamentos=('salario', 'count'),
    salario_medio=('salario', 'mean')
).reset_index()
custo_dept['custo_estimado'] = custo_dept['total_desligamentos'] * custo_dept['salario_medio'] * 1.5
custo_dept = custo_dept.sort_values('custo_estimado', ascending=True)

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(custo_dept['departamento'], custo_dept['custo_estimado'] / 1000,
               color=AZUL, edgecolor='none', height=0.6)
for bar, val in zip(bars, custo_dept['custo_estimado']):
    ax.text(val/1000 + 0.5, bar.get_y() + bar.get_height()/2,
            f'R$ {val/1000:.0f}K', va='center', fontsize=10, color='white')

ax.set_title('Custo Estimado do Turnover por Departamento\n(1.5x salário médio por desligamento)',
             fontsize=13, fontweight='bold', color='white', pad=15)
ax.set_xlabel('Custo Estimado (R$ mil)', color='#aaaacc')
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('graficos/06_custo_turnover.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/06_custo_turnover.png")

print("📊 Gerando gráfico 7 — Tempo de Empresa vs Saída...")

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Tempo de Empresa dos Colaboradores Desligados', fontsize=14, fontweight='bold', color='white')

axes[0].hist(df_turnover['tempo_empresa'], bins=20, color=ROXO, edgecolor='#1e1e2e', linewidth=0.5)
axes[0].set_title('Distribuição do Tempo de Empresa', color='white')
axes[0].set_xlabel('Tempo (meses)', color='#aaaacc')
axes[0].set_ylabel('Quantidade', color='#aaaacc')
axes[0].grid(axis='y', alpha=0.3)
axes[0].axvline(df_turnover['tempo_empresa'].mean(), color=LARANJA,
                linestyle='--', linewidth=1.5, label=f"Média: {df_turnover['tempo_empresa'].mean():.0f} meses")
axes[0].legend(facecolor='#2a2a3e', edgecolor='#444466', labelcolor='white')

tempo_dept = df_turnover.groupby('departamento')['tempo_empresa'].mean().sort_values()
axes[1].barh(tempo_dept.index, tempo_dept.values, color=VERDE, edgecolor='none', height=0.6)
for dept, val in zip(tempo_dept.index, tempo_dept.values):
    axes[1].text(val + 0.3, dept, f'{val:.0f} meses', va='center', fontsize=10, color='white')
axes[1].set_title('Tempo Médio de Empresa por Departamento', color='white')
axes[1].set_xlabel('Meses', color='#aaaacc')
axes[1].grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('graficos/07_tempo_empresa.png', dpi=150, bbox_inches='tight', facecolor='#1e1e2e')
plt.close()
print("   ✅ Salvo: graficos/07_tempo_empresa.png")
 
print("\n" + "="*50)
print("✅ ANÁLISE CONCLUÍDA — 7 GRÁFICOS GERADOS")
print("="*50)
print(f"\n📊 RESUMO EXECUTIVO:")
print(f"   Total de funcionários  : {len(df)}")
print(f"   Ativos                 : {(df['status']=='Ativo').sum()}")
print(f"   Desligados             : {(df['status']=='Desligado').sum()}")
print(f"   Taxa de turnover       : {(df['status']=='Desligado').sum()/len(df)*100:.1f}%")
print(f"   Salário médio geral    : R$ {df['salario'].mean():,.2f}")
print(f"   Satisfação média       : {df['satisfacao'].mean():.1f}/5")
print(f"   Desempenho médio       : {df['avaliacao_desempenho'].mean():.1f}/5")
print(f"\n📁 Gráficos salvos em: ./graficos/")
print("="*50)