from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from PIL import Image

from src.nhf_core import (
    abrir_datasets,
    calcular_climatologia_anual,
    carregar_geometrias_mg,
    extrair_serie_municipio,
    filtrar_inverno,
    localizar_municipio,
    preparar_grade_ano,
)
from src.plots import figura_historico, figura_localizacao_barras, figura_mapa_espacial

# -----------------------------------------------------------------------------
# DEFINIÇÃO DE CAMINHOS
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("NHF_DATA_DIR", BASE_DIR / "data"))
PASTA_TMAX = DATA_DIR / "Tmax"
PASTA_TMIN = DATA_DIR / "Tmin"
LOGOS_DIR = BASE_DIR / "assets" / "logos"
LOGO_SITE = LOGOS_DIR / "logo_site.png" 

LOGOS = [
    ("UNIFEI", LOGOS_DIR / "UNIFEI.png"),
    ("CAT", LOGOS_DIR / "CAT.png"),
    ("AGRO", LOGOS_DIR / "AGRO.png"),
    ("EPAMIG", LOGOS_DIR / "EPAMIG.webp"),
    ("FAPEMIG", LOGOS_DIR / "FAPEMIG.png"),
    ("CNPQ", LOGOS_DIR / "CNPq.png"),
]

# Tenta carregar o logo para a aba do navegador. Se não achar, usa o emoji padrão.
try:
    icone_pagina = Image.open(LOGO_SITE)
except Exception:
    icone_pagina = "🌡️"

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SAAF - Minas Gerais",
    page_icon=icone_pagina,
    layout="wide",
    initial_sidebar_state="expanded",
)


def renderizar_logos():
    """Exibe os seis logos institucionais no rodapé, na ordem definida."""
    st.divider()

    # Cria 6 colunas para enfileirar os logos, alinhando-os verticalmente ao centro
    colunas = st.columns(6, vertical_alignment="center")
    
    # Distribui cada logo em sua respectiva coluna, sem título e sem textos
    for coluna, (nome, caminho_logo) in zip(colunas, LOGOS):
        with coluna:
            if caminho_logo.exists():
                st.image(str(caminho_logo), use_container_width=True)
            else:
                st.info(f"Logo {nome}")


# -----------------------------------------------------------------------------
# ESTILO
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1500px;}
      
      /* Barra lateral em azul claro/azul bebê */
      [data-testid="stSidebar"] {
        background-color: #D9EEFF;
      }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #17324D;
      }

      /* =====================================================================
         SOLUÇÃO DEFINITIVA: CAIXAS/BOTÕES AO REDOR DAS ABAS
         Usando a classe oficial do Streamlit (.stTabs)
         ===================================================================== */
      
      /* Cria o visual de 'quadrado' visível para cada aba */
      .stTabs button[role="tab"] {
          border: 2px solid #dcdcdc !important; /* Borda cinza clara visível */
          border-radius: 8px !important; /* Bordas levemente arredondadas */
          padding: 12px 25px !important; /* Espaçamento interno grande */
          background-color: #ffffff !important; /* Fundo branco */
          margin-right: 12px !important; /* Separação entre os botões */
          box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Sombra super leve */
      }

      /* Estilo de quando a aba estiver ATIVA/SELECIONADA */
      .stTabs button[role="tab"][aria-selected="true"] {
          border: 3px solid #17324D !important; /* Borda grossa azul escura */
          background-color: #D9EEFF !important; /* Fundo azul bebê */
      }

      /* Força o aumento da fonte o máximo que o framework permite nas abas */
      .stTabs button[role="tab"] p {
          font-size: 24px !important; 
          font-weight: 700 !important;
          color: #333333 !important;
          margin: 0 !important;
      }
      
      /* Cor da fonte quando a aba está ativa */
      .stTabs button[role="tab"][aria-selected="true"] p {
          color: #17324D !important;
      }
      
      /* Remove aquela barrinha de seleção padrão e feia do Streamlit */
      .stTabs [data-baseweb="tab-highlight"] {
          display: none !important;
      }
      /* ===================================================================== */

    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# CACHE
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner="Carregando limites municipais...")
def get_geometrias():
    return carregar_geometrias_mg(ano=2020)


@st.cache_resource(show_spinner="Abrindo arquivos NetCDF...")
def get_datasets(pasta_tmax: str, pasta_tmin: str):
    return abrir_datasets(pasta_tmax, pasta_tmin)


@st.cache_data(show_spinner=False)
def get_serie_municipio(_ds_tmax, _ds_tmin, lat: float, lon: float):
    return extrair_serie_municipio(_ds_tmax, _ds_tmin, lat, lon)


# -----------------------------------------------------------------------------
# CABEÇALHO
# -----------------------------------------------------------------------------
st.title("🌡️ Sistema Agroclimático de Acúmulo de Frio - SAAF")
st.caption(
    "Número de Horas de Frio (NHF) para municípios de Minas Gerais, "
    "com análise histórica e mapa espacial anual."
)

st.markdown(
    """
Frutíferas de clima temperado são plantas que possuem necessidade de acúmulo de frio. Por isso, se desenvolvem melhor em regiões que possuem outono ou inverno relativamente frio e verões amenos a quentes. O acúmulo de frio é necessário para a planta  sair do período de dormência e iniciar adequadamente um novo ciclo reprodutivo, com brotação, florescimento e frutificação normais.

O acúmulo de frio é a quantidade total, em horas, em que a temperatura do ar permanece abaixo de um limiar, denominado temperatura base. A temperatura base depende da espécie/cultivar/variedade.

Nesse contexto, o Sistema Agroclimático de Acúmulo de Frio (SAAF) exibe a climatologia do Número de Horas de Frio (NHF, em horas) para os municípios de Minas Gerais usando o limiar de temperatura informado pelo usuário. O SAAF analisa dados de maio a setembro (1981–2025) da base BR-DWGD (Xavier et al., 2022), a partir do método de Pola e Angelocci (1993) para calcular o acúmulo de frio.

**Desenvolvimento:** Felipe Henrique dos Santos.  
**Orientação:** Flávia Fernanda Azevedo Fagundes, Gabriel Koch e Fabrina Bolzan Martins.
    """
)

with st.expander("Como o sistema funciona", expanded=False):
    st.markdown(
        """
        1. O município é localizado a partir da malha oficial do **geobr**.
        2. O sistema encontra o ponto mais próximo do centro do município escolhido.
        3. Você escolhe o limiar da temperatura base (°C) e o acúmulo total e ideal de horas de frio.
        4. O NHF é calculado para o limiar escolhido e também para um range de **+/− 3°C.**
        5. É contabilizado o NHF entre os meses de **maio a setembro**.
        6. Para um ano específico, pode ser produzido o mapa espacial de NHF em Minas Gerais.
        """
    )


# -----------------------------------------------------------------------------
# CARREGAMENTO BÁSICO
# -----------------------------------------------------------------------------
try:
    mg_muni, mg_estado = get_geometrias()
except Exception as exc:
    st.error("Não foi possível carregar as geometrias de Minas Gerais.")
    st.exception(exc)
    st.stop()

nomes_municipios = sorted(mg_muni["name_muni"].dropna().astype(str).unique())

if not PASTA_TMAX.exists() or not PASTA_TMIN.exists():
    st.error(
        "As pastas de dados ainda não existem. Crie `data/Tmax` e `data/Tmin` "
        "e coloque os arquivos NetCDF correspondentes dentro delas."
    )
    st.code(f"Tmax: {PASTA_TMAX}\nTmin: {PASTA_TMIN}")
    st.stop()

try:
    ds_tmax, ds_tmin = get_datasets(str(PASTA_TMAX), str(PASTA_TMIN))
except Exception as exc:
    st.error("Não foi possível abrir os NetCDF de Tmax/Tmin.")
    st.info("Confira a organização em `data/Tmax/*.nc` e `data/Tmin/*.nc`.")
    st.exception(exc)
    st.stop()


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    # Insere a imagem do logo centralizada ocupando cerca de 85% da largura
    if LOGO_SITE.exists():
        col1, col2, col3 = st.columns([0.075, 0.85, 0.075])
        with col2:
            st.image(str(LOGO_SITE), use_container_width=True)
        st.write("") # Adiciona um espacinho extra embaixo do logo

    st.header("Parâmetros")

    default_city = "Maria da Fé" if "Maria da Fé" in nomes_municipios else nomes_municipios[0]
    cidade = st.selectbox(
        "Município",
        nomes_municipios,
        index=nomes_municipios.index(default_city),
    )

    tb_alvo = st.number_input(
        "Limiar térmico base (°C)",
        min_value=-5.0,
        max_value=30.0,
        value=8.0,
        step=0.5,
    )

    meta = st.number_input(
        "Meta de horas acumuladas (h)",
        min_value=0.0,
        max_value=5000.0,
        value=300.0,
        step=10.0,
    )

    st.divider()
    st.caption("O mapa espacial é calculado apenas para um ano específico.")


# -----------------------------------------------------------------------------
# PRÉ-PROCESSAMENTO DO MUNICÍPIO
# -----------------------------------------------------------------------------
try:
    muni_alvo, lat_alvo, lon_alvo, nome_oficial = localizar_municipio(mg_muni, cidade)
    (
        df_temp,
        lat_real,
        lon_real,
        lat_coord,
        lon_coord,
        var_tmax,
        var_tmin,
    ) = get_serie_municipio(ds_tmax, ds_tmin, lat_alvo, lon_alvo)
    df_inverno = filtrar_inverno(df_temp)
    df_clima, df_hist, medias = calcular_climatologia_anual(df_inverno, tb_alvo)
except Exception as exc:
    st.error("Falha durante a preparação dos dados do município selecionado.")
    st.exception(exc)
    st.stop()

anos_disponiveis = df_clima["Ano"].astype(int).tolist()

with st.sidebar:
    opcao_ano = st.selectbox(
        "Período",
        ["Climatologia (todos os anos)"] + [str(a) for a in sorted(anos_disponiveis, reverse=True)],
    )
    gerar_mapa = st.checkbox(
        "Gerar mapa espacial",
        value=False,
        disabled=opcao_ano.startswith("Climatologia"),
        help="O cálculo espacial é mais pesado do que a análise pontual do município.",
    )
    executar = st.button("Calcular NHF", type="primary", width="stretch")

if not executar:
    st.info("Defina os parâmetros na barra lateral e clique em **Calcular NHF**.")
    renderizar_logos()
    st.stop()


# -----------------------------------------------------------------------------
# RESULTADOS
# -----------------------------------------------------------------------------
tb_minus = tb_alvo - 3.0
tb_plus = tb_alvo + 3.0
is_todos = opcao_ano.startswith("Climatologia")

if is_todos:
    valores_plot = [medias["minus"], medias["base"], medias["plus"]]
    titulo_barras = f"Climatologia de horas de frio - {nome_oficial}"
    ano_escolhido = None
else:
    ano_escolhido = int(opcao_ano)
    linha = df_clima.loc[df_clima["Ano"] == ano_escolhido].iloc[0]
    valores_plot = [
        float(linha[f"NHF < {tb_minus}°C"]),
        float(linha[f"NHF < {tb_alvo}°C"]),
        float(linha[f"NHF < {tb_plus}°C"]),
    ]
    titulo_barras = f"Acúmulo de frio - {nome_oficial} ({ano_escolhido})"

st.subheader(f"Resultados — {nome_oficial}, MG")


# --------- CONSTRUÇÃO DOS QUADRADINHOS DE MÉTRICA (TAMANHOS AJUSTADOS) ---------
# Cores para os resultados calculados normais
cor_azul_fundo = "#D9EEFF"
cor_azul_borda = "#17324D"
cor_azul_label = "#333333"
cor_azul_valor = "#111111"

# Validação da meta
diff = valores_plot[1] - meta
if diff >= 0:
    cor_meta_fundo = "#AAF99B"
    cor_meta_borda = "#AAF99B" 
    cor_meta_texto = "#32860E" 
    delta_text = f"↑ {abs(diff):.1f} h"
else:
    cor_meta_fundo = "#F8705E"
    cor_meta_borda = "#F8705E" 
    cor_meta_texto = "#BB0E22" 
    delta_text = f"↓ {abs(diff):.1f} h"

def render_metric(label, value_str, bg_color, border_color, text_color, label_color, delta_text="", delta_color=""):
    delta_html = f'<div style="color: {delta_color}; font-size: 22px; font-weight: bold; margin-top: 5px;">{delta_text}</div>' if delta_text else '<div style="visibility: hidden; font-size: 22px; margin-top: 5px;">-</div>'
    return f"""
    <div style="background-color: {bg_color}; border-left: 10px solid {border_color}; padding: 15px 10px; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">
        <div style="color: {label_color}; font-size: 20px; font-weight: 600; margin-bottom: 5px;">{label}</div>
        <div style="color: {text_color}; font-size: 30px; font-weight: 900; line-height: 1.1;">{value_str}</div>
        {delta_html}
    </div>
    """

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(render_metric(f"NHF < {tb_minus:g}°C", f"{valores_plot[0]:.1f} h", cor_azul_fundo, cor_azul_borda, cor_azul_valor, cor_azul_label), unsafe_allow_html=True)
with c2:
    st.markdown(render_metric(f"NHF < {tb_alvo:g}°C", f"{valores_plot[1]:.1f} h", cor_azul_fundo, cor_azul_borda, cor_azul_valor, cor_azul_label), unsafe_allow_html=True)
with c3:
    st.markdown(render_metric(f"NHF < {tb_plus:g}°C", f"{valores_plot[2]:.1f} h", cor_azul_fundo, cor_azul_borda, cor_azul_valor, cor_azul_label), unsafe_allow_html=True)
with c4:
    st.markdown(render_metric("Meta", f"{meta:.0f} h", cor_meta_fundo, cor_meta_borda, cor_meta_texto, cor_meta_texto, delta_text, cor_meta_texto), unsafe_allow_html=True)
# ---------------------------------------------------------


st.caption(
    f"Ponto de grade utilizado: {lat_real:.3f}, {lon_real:.3f} | "
    f"Variáveis detectadas: Tmax=`{var_tmax}` e Tmin=`{var_tmin}`"
)

resumo = pd.DataFrame(
    [
        {
            "Contexto": "Média climatológica",
            f"< {tb_minus:g}°C": round(medias["minus"], 1),
            f"< {tb_alvo:g}°C (base)": round(medias["base"], 1),
            f"< {tb_plus:g}°C": round(medias["plus"], 1),
        }
    ]
)
if not is_todos:
    resumo.loc[len(resumo)] = [
        f"Ano específico ({ano_escolhido})",
        round(valores_plot[0], 1),
        round(valores_plot[1], 1),
        round(valores_plot[2], 1),
    ]

aba_resumo, aba_historico, aba_mapa, aba_dados = st.tabs(
    ["**Resumo**", "**Histórico**", "**Mapa espacial**", "**Dados**"]
)

with aba_resumo:
    st.dataframe(resumo, width="stretch", hide_index=True)
    fig = figura_localizacao_barras(
        mg_muni=mg_muni,
        muni_alvo=muni_alvo,
        nome_oficial=nome_oficial,
        lat_real=lat_real,
        lon_real=lon_real,
        tb_alvo=tb_alvo,
        meta=meta,
        valores_plot=valores_plot,
        titulo_barras=titulo_barras,
    )
    st.pyplot(fig, width="stretch")
    plt.close(fig)

with aba_historico:
    fig_hist = figura_historico(
        df_hist=df_hist,
        tb_alvo=tb_alvo,
        meta=meta,
        media_base=medias["base"],
        nome_oficial=nome_oficial,
    )
    st.pyplot(fig_hist, width="stretch")
    plt.close(fig_hist)

with aba_mapa:
    if is_todos:
        st.info("Selecione um ano específico para habilitar o mapa espacial.")
    elif not gerar_mapa:
        st.info("Marque **Gerar mapa espacial** na barra lateral e execute novamente.")
    else:
        with st.spinner(f"Calculando o mapa espacial de {ano_escolhido}..."):
            try:
                da_espacial, lat_coord_map, lon_coord_map = preparar_grade_ano(
                    ds_tmax,
                    ds_tmin,
                    ano=ano_escolhido,
                    tb_alvo=tb_alvo,
                )
                fig_map = figura_mapa_espacial(
                    da_espacial=da_espacial,
                    lat_coord=lat_coord_map,
                    lon_coord=lon_coord_map,
                    mg_muni=mg_muni,
                    mg_estado=mg_estado,
                    muni_alvo=muni_alvo,
                    nome_oficial=nome_oficial,
                    lon_alvo=lon_alvo,
                    lat_alvo=lat_alvo,
                    tb_alvo=tb_alvo,
                    meta=meta,
                    ano=ano_escolhido,
                )
                st.pyplot(fig_map, width="stretch")
                plt.close(fig_map)
            except Exception as exc:
                st.error("Não foi possível calcular o mapa espacial.")
                st.exception(exc)

with aba_dados:
    st.markdown("#### Série anual de NHF")
    st.dataframe(df_clima.round(1), width="stretch", hide_index=True)

    csv_clima = df_clima.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar tabela anual em CSV",
        data=csv_clima,
        file_name=f"nhf_{nome_oficial.replace(' ', '_')}_{tb_alvo:g}C.csv",
        mime="text/csv",
    )

    with st.expander("Ver temperaturas diárias do ponto de grade"):
        st.dataframe(df_temp.round(2), width="stretch")

st.success("Processamento concluído.")

renderizar_logos()