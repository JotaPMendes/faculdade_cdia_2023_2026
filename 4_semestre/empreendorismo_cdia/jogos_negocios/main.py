import streamlit as st
import pandas as pd
import numpy as np
import random

# Configuração inicial de estado
if "empresas" not in st.session_state:
    st.session_state.empresas = []

if "pagina" not in st.session_state:
    st.session_state.pagina = "cadastro"

if "eventos" not in st.session_state:
    st.session_state.eventos = [
        {"evento": "Alta demanda sazonal", "impacto": 1.2, "descricao": "A demanda pelo produto aumentou, resultando em um aumento de 20% no faturamento."},
        {"evento": "Queda no consumo", "impacto": 0.8, "descricao": "O consumo caiu, resultando em uma redução de 20% no faturamento."},
        {"evento": "Nova tecnologia reduz custos", "impacto": 0.9, "descricao": "Uma nova tecnologia reduziu os custos de produção em 10%."},
        {"evento": "Concorrente agressivo aumenta propaganda", "impacto": 0.7, "descricao": "Um concorrente agressivo aumentou a propaganda, reduzindo seu faturamento em 30%."},
    ]

if "rodada_atual" not in st.session_state:
    st.session_state.rodada_atual = 1

if "saldo" not in st.session_state:
    st.session_state.saldo = {}

if "decisoes" not in st.session_state:
    st.session_state.decisoes = {}

# Função para trocar de página
def mudar_pagina(pagina):
    st.session_state.pagina = pagina

# Função para calcular métricas financeiras
def calcular_custos_e_faturamento(df, evento):
    df["salario_vendedores"] = df["vendedores"] * 1500
    df["hora_extra"] = np.where(df["quantidade"] > 100, (df["quantidade"] - 100) * 10, 0)  # Hora extra se produção > 100
    df["estocagem"] = np.where(df["quantidade"] < 100, (100 - df["quantidade"]) * 5, 0)  # Estocagem se produção < 100
    df["cmv"] = df["quantidade"] * 0.20  # Custo da mercadoria vendida
    df["salarios_gerais"] = df["quantidade"] * 0.08  # Salários gerais
    df["aluguel"] = 1000  # Aluguel fixo para cada rodada
    df["total_despesas"] = (
        df["propaganda"] + df["salario_vendedores"] + df["hora_extra"] + 
        df["estocagem"] + df["cmv"] + df["salarios_gerais"] + df["aluguel"]
    )
    if "reduz_custos" in evento:
        df["total_despesas"] *= evento["impacto"]
    df["faturamento"] = df['quantidade'] * df['preco']
    if "aumenta_faturamento" in evento:
        df["faturamento"] *= evento["impacto"]
    df["lucro"] = df["faturamento"] - df["total_despesas"]
    df["classificacao"] = np.where(df['lucro'] > 0, 'Lucrativa', 'Prejuízo')
    return df

# Adicionar CSS para estilização
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .header {
        text-align: center;
        color: #4CAF50;
        margin-bottom: 20px;
    }
    .subheader {
        color: #FF5733;
        margin-top: 20px;
    }
    .form-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 10px;
    }
    .button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

# Página de cadastro
if st.session_state.pagina == "cadastro":
    st.markdown("<h1 class='header'>Cadastro de Empresas 🏢</h1>", unsafe_allow_html=True)
    if st.button("Ir para Rodadas 🎮", key="go_to_game"):
        mudar_pagina("jogo")
    st.markdown("<h3>Adicione as empresas participantes do jogo abaixo:</h3>", unsafe_allow_html=True)
    st.write("Preencha as informações de cada empresa e clique em **Adicionar Empresa** para cadastrar.")

    # Formulário
    with st.form(key="cadastro_empresa", clear_on_submit=True):
        st.markdown("<div class='form-container'><h4>Informações da Empresa</h4>", unsafe_allow_html=True)
        empresa_nome = st.text_input("Nome da Empresa *", placeholder="Insira o nome da empresa")
        preco = st.number_input("Preço do Produto *", min_value=1.0, help="Informe o preço unitário do produto.")
        quantidade = st.number_input("Quantidade Produzida *", min_value=1, help="Quantos produtos serão produzidos?")
        propaganda = st.number_input("Gasto com Propaganda (R$) *", min_value=0, help="Quanto será investido em propaganda?")
        vendedores = st.number_input("Número de Vendedores *", min_value=0, help="Quantos vendedores trabalharão na empresa?")

        # Botão de submissão
        submit_button = st.form_submit_button("Adicionar Empresa ➕")

    # Validar campos após a submissão
    if submit_button:
        if not empresa_nome.strip():
            st.error("O nome da empresa é obrigatório. Por favor, preencha corretamente.")
        elif preco <= 0:
            st.error("O preço do produto deve ser maior que zero.")
        elif quantidade <= 0:
            st.error("A quantidade produzida deve ser maior que zero.")
        elif propaganda < 0:
            st.error("O gasto com propaganda não pode ser negativo.")
        elif vendedores < 0:
            st.error("O número de vendedores não pode ser negativo.")
        else:
            # Adicionar a empresa se todos os campos forem válidos
            st.session_state.empresas.append({
                "empresa": empresa_nome,
                "preco": preco,
                "quantidade": quantidade,
                "propaganda": propaganda,
                "vendedores": vendedores,
            })
            st.success(f"Empresa '{empresa_nome}' adicionada com sucesso!")

    # Mostrando empresas cadastradas
    st.markdown("<h3>Empresas Cadastradas:</h3>", unsafe_allow_html=True)
    if len(st.session_state.empresas) == 0:
        st.info("Nenhuma empresa cadastrada ainda. Adicione uma empresa no formulário acima.")
    else:
        for empresa in st.session_state.empresas:
            with st.expander(f"📋 {empresa['empresa']}"):
                st.write(f"**Preço do Produto:** R$ {empresa['preco']:.2f}")
                st.write(f"**Quantidade Produzida:** {empresa['quantidade']}")
                st.write(f"**Gasto com Propaganda:** R$ {empresa['propaganda']:.2f}")
                st.write(f"**Número de Vendedores:** {empresa['vendedores']}")

        st.success(f"Total de empresas cadastradas: {len(st.session_state.empresas)}")

# Página de rodadas do jogo
elif st.session_state.pagina == "jogo":
    st.markdown(f"<h1 class='header'>Rodadas do Jogo - Rodada {st.session_state.rodada_atual}</h1>", unsafe_allow_html=True)
    if st.button("Voltar para Cadastro", key="back_to_cadastro"):
        mudar_pagina("cadastro")

    if len(st.session_state.empresas) == 0:
        st.warning("Nenhuma empresa cadastrada. Volte para a página de cadastro e adicione empresas.")
    else:
        # Seleção do evento aleatório para a rodada atual
        if f"evento_rodada_{st.session_state.rodada_atual}" not in st.session_state:
            st.session_state[f"evento_rodada_{st.session_state.rodada_atual}"] = random.choice(st.session_state.eventos)

        evento_atual = st.session_state[f"evento_rodada_{st.session_state.rodada_atual}"]
        st.markdown(f"<h2 class='subheader'>Evento Atual: {evento_atual['evento']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p>{evento_atual['descricao']}</p>", unsafe_allow_html=True)

        # Primeira rodada usa valores iniciais
        if st.session_state.rodada_atual == 1:
            st.write("### Primeira Rodada: Usando valores iniciais configurados na página de cadastro.")
            df = pd.DataFrame(st.session_state.empresas)
            df = calcular_custos_e_faturamento(df, evento_atual)
            
            if st.button("Calcular Resultados da Primeira Rodada"):
                st.session_state.rodada_atual += 1
                st.rerun()
        else:
            # Formulário para decisões da rodada
            st.markdown("### Decisões da Rodada")
            for empresa in st.session_state.empresas:
                with st.form(key=f"decisoes_{empresa['empresa']}", clear_on_submit=False):
                    st.markdown(f"#### {empresa['empresa']}")
                    preco = st.number_input(f"Preço do Produto ({empresa['empresa']})", min_value=1.0, value=empresa['preco'])
                    quantidade = st.number_input(f"Quantidade Produzida ({empresa['empresa']})", min_value=1, value=empresa['quantidade'])
                    propaganda = st.number_input(f"Gasto com Propaganda ({empresa['empresa']})", min_value=0, value=empresa['propaganda'])
                    vendedores = st.number_input(f"Número de Vendedores ({empresa['empresa']})", min_value=0, value=empresa['vendedores'])

                    # Botão de submissão
                    submit_button = st.form_submit_button("Aplicar Decisões")

                    if submit_button:
                        st.session_state.decisoes[empresa['empresa']] = {
                            "preco": preco,
                            "quantidade": quantidade,
                            "propaganda": propaganda,
                            "vendedores": vendedores,
                        }
                        st.success(f"Decisões para '{empresa['empresa']}' aplicadas com sucesso!")

            # Aplicar decisões e calcular resultados
            if st.button("Calcular Resultados da Rodada"):
                for empresa in st.session_state.empresas:
                    if empresa['empresa'] in st.session_state.decisoes:
                        decisoes = st.session_state.decisoes[empresa['empresa']]
                        empresa['preco'] = decisoes['preco']
                        empresa['quantidade'] = decisoes['quantidade']
                        empresa['propaganda'] = decisoes['propaganda']
                        empresa['vendedores'] = decisoes['vendedores']

                # Dados das empresas para esta rodada
                df = pd.DataFrame(st.session_state.empresas)
                
                # Cálculo dos custos e faturamento para esta rodada
                df = calcular_custos_e_faturamento(df, evento_atual)

                # Atualização do saldo acumulado de cada empresa
                for idx, row in df.iterrows():
                    empresa = row["empresa"]
                    lucro = row["lucro"]
                    if empresa not in st.session_state.saldo:
                        st.session_state.saldo[empresa] = 0
                    st.session_state.saldo[empresa] += lucro

                # Exibição dos resultados da rodada
                st.write("### Resultados da Rodada")
                st.dataframe(df[["empresa", "faturamento", "lucro", "classificacao"]])

                # Exibição do saldo acumulado de cada empresa
                saldo_acumulado = pd.DataFrame({
                    "empresa": list(st.session_state.saldo.keys()),
                    "saldo_acumulado": list(st.session_state.saldo.values())
                })
                st.write("### Saldo Acumulado")
                st.dataframe(saldo_acumulado)

                # Gráficos de desempenho
                st.subheader("Análise Gráfica")
                st.bar_chart(df.set_index("empresa")[["lucro", "faturamento"]])

                # Histórico de rodadas
                if 'historico' not in st.session_state:
                    st.session_state['historico'] = []
                st.session_state['historico'].append(df)
                st.write("### Histórico de Rodadas")
                for i, rodada in enumerate(st.session_state['historico']):
                    st.markdown(f"#### Rodada {i + 1}")
                    st.dataframe(rodada)

                # Botão para avançar para a próxima rodada
                if st.button("Próxima Rodada"):
                    st.session_state.rodada_atual += 1
                    st.rerun()
