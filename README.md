# NHF Minas Gerais — Streamlit

Aplicação web para cálculo e visualização do Número de Horas de Frio (NHF) em municípios de Minas Gerais.

## 1. Estrutura

```text
nhf_streamlit/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── README.md
│   ├── Tmax/
│   └── Tmin/
└── src/
    ├── __init__.py
    ├── nhf_core.py
    └── plots.py
```

## 2. O que foi adaptado do código do Colab

O código original usava:

- `google.colab.drive.mount(...)`
- `input(...)`
- `print(...)`
- `IPython.display.display(...)`
- `plt.show()`

No site, isso foi substituído por:

- caminhos do próprio servidor ou variável `NHF_DATA_DIR`;
- widgets do Streamlit (`selectbox`, `number_input`, `checkbox`, `button`);
- mensagens do Streamlit (`st.info`, `st.error`, `st.success`);
- tabelas com `st.dataframe`;
- figuras com `st.pyplot`.

A lógica central dos cálculos 1D e 3D de NHF foi preservada.

## 3. Preparar o ambiente no Ubuntu/Linux

Entre na pasta do projeto:

```bash
cd nhf_streamlit
```

Crie o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Atualize o pip e instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Colocar os dados

Copie os NetCDF de Tmax para:

```text
data/Tmax/
```

Copie os NetCDF de Tmin para:

```text
data/Tmin/
```

Se os dados já estiverem em outra pasta, você não precisa copiá-los. Use:

```bash
export NHF_DATA_DIR="/seu/caminho/Xavier - Recortes GITHUB"
```

Essa pasta precisa conter:

```text
Tmax/
Tmin/
```

## 5. Rodar localmente

```bash
streamlit run app.py
```

O terminal mostrará um endereço local, normalmente:

```text
http://localhost:8501
```

## 6. Como usar

Na barra lateral:

1. escolha o município;
2. informe o limiar térmico base;
3. informe a meta de horas;
4. escolha climatologia ou um ano específico;
5. se desejar, habilite o mapa espacial para um ano específico;
6. clique em **Calcular NHF**.

O site mostra:

- NHF para `Tb - 3°C`, `Tb` e `Tb + 3°C`;
- comparação com a meta;
- mapa de localização do município;
- gráfico climatológico anual;
- mapa espacial anual de Minas Gerais;
- tabela anual para download em CSV;
- série diária de Tmax/Tmin do ponto de grade.

## 7. Testar antes do deploy

Verifique se os arquivos compilam:

```bash
python -m compileall app.py src
```

Depois rode:

```bash
streamlit run app.py
```

Teste pelo menos:

- Maria da Fé;
- `Tb = 8°C`;
- `meta = 300 h`;
- climatologia;
- um ano específico;
- mapa espacial;
- download do CSV.

## 8. Publicar no GitHub

Crie um repositório e execute:

```bash
git init
git add .
git commit -m "Versão inicial do sistema NHF em Streamlit"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

### Atenção aos NetCDF

O `.gitignore` deste projeto ignora os arquivos `.nc`, porque conjuntos climáticos frequentemente são grandes demais para um repositório Git comum.

Para produção, prefira uma destas opções:

1. armazenar os NetCDF em uma máquina/servidor onde o Streamlit será executado;
2. usar armazenamento de objetos ou servidor HTTP/OPeNDAP;
3. preparar arquivos menores especificamente para o site;
4. usar Git LFS somente se o volume e o serviço escolhido forem compatíveis.

## 9. Streamlit Community Cloud

Para Community Cloud, o repositório precisa conter pelo menos:

- `app.py`;
- `requirements.txt`;
- demais módulos Python usados pelo app.

No painel de deploy, escolha `app.py` como arquivo principal.

O servidor remoto não enxerga o Google Drive montado no Colab nem os arquivos do seu computador. Portanto, os NetCDF precisam estar disponíveis para o ambiente remoto.

## 10. Desempenho

O projeto já usa cache em pontos importantes:

- geometrias: `st.cache_data`;
- datasets NetCDF abertos: `st.cache_resource`;
- série municipal extraída: `st.cache_data`.

O mapa espacial anual é opcional porque exige o cálculo 3D para toda a grade.

Para uma aplicação pública com muitos usuários, uma melhoria futura importante é pré-calcular os mapas anuais de NHF por limiar de interesse e salvar os resultados em NetCDF/Zarr. Isso reduz drasticamente o tempo de resposta do site.

## 11. Problemas comuns

### `Nenhum .nc encontrado`
Confira se existem arquivos em `data/Tmax` e `data/Tmin` ou se `NHF_DATA_DIR` aponta para a pasta correta.

### Erro do `open_mfdataset`
Confira se os arquivos possuem coordenadas temporais compatíveis. O `open_mfdataset` também requer Dask, já incluído em `requirements.txt`.

### Erro de variável
O app escolhe automaticamente a primeira variável que não seja metadado espacial. Se seus arquivos tiverem várias variáveis meteorológicas, o ideal é definir explicitamente os nomes de Tmax/Tmin em `src/nhf_core.py`.

### Site lento no mapa espacial
É esperado que o mapa leve mais tempo do que a análise municipal. Pré-cálculo é a melhor solução para produção.

## 12. Opção Docker

Também foi incluído um `Dockerfile`. Isso é útil se os NetCDF permanecerem em um servidor próprio.

Build:

```bash
docker build -t nhf-streamlit .
```

Executar usando os dados que estão dentro do projeto:

```bash
docker run --rm -p 8501:8501 nhf-streamlit
```

Executar montando uma pasta externa de dados:

```bash
docker run --rm \
  -p 8501:8501 \
  -e NHF_DATA_DIR=/dados \
  -v "/caminho/no/servidor/Xavier - Recortes GITHUB:/dados:ro" \
  nhf-streamlit
```

## 13. Versão de Python

Para reproduzir o ambiente usado no `Dockerfile`, use Python 3.13. O Streamlit 1.61.1 e o geobr 1.0.0 suportam Python 3.13.
