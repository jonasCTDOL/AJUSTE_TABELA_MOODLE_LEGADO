
# Tutorial: Construindo um Gerador de CSV para Moodle com Streamlit e Google Sheets

Este tutorial detalha o processo de construção de uma aplicação web com Python e Streamlit para automatizar a criação de arquivos CSV para a carga de usuários e matrículas na plataforma Moodle. A aplicação se conecta a uma Planilha Google, processa os dados e os formata corretamente, ficando prontos para a importação.

Este documento é otimizado para visualização no Obsidian.

## 🏛️ Arquitetura da Solução

A aplicação utiliza as seguintes tecnologias:

*   **Python:** Linguagem de programação principal.
*   **Streamlit:** Framework para a criação da interface web de forma rápida e interativa.
*   **Pandas:** Biblioteca para manipulação e análise de dados, fundamental para o processamento das informações da planilha.
*   **gspread:** Biblioteca para interagir com a API do Google Sheets, permitindo a leitura e escrita de dados.
*   **Google Cloud Platform (GCP):** Para a criação de uma conta de serviço que permite o acesso seguro à planilha sem expor credenciais.

O fluxo de trabalho da aplicação é o seguinte:

1.  **Autenticação Segura:** A aplicação se autentica na API do Google Sheets usando credenciais de uma conta de serviço armazenadas nos "Secrets" do Streamlit.
2.  **Entrada do Usuário:** O usuário fornece o nome da Planilha Google, o nome da página (aba) específica, o identificador do curso e o identificador do grupo/turma no Moodle.
3.  **Processamento de Dados:** A aplicação lê os dados da planilha, seleciona as colunas necessárias (`CPF`, `Nome`, `Cargo`, `E-mail`), as renomeia para o padrão do Moodle, formata o CPF como `username` e adiciona as colunas fixas (`password`, `role1`, `course1`, `group1`).
4.  **Saída (Opcional):** Se o usuário desejar, os dados processados podem ser salvos em uma nova aba na mesma Planilha Google.
5.  **Geração de CSV:** A aplicação gera um arquivo CSV com os dados formatados, pronto para download e importação no Moodle.

---

## 🛠️ Pré-requisitos

Antes de começar, você precisará ter o seguinte instalado em sua máquina:

*   **Python 3.8+:** [Link para download do Python](https://www.python.org/downloads/)
*   **Git:** [Link para download do Git](https://git-scm.com/downloads)
*   **Conta Google:** Para criar e acessar a Planilha Google.
*   **Conta no GitHub:** Para clonar o repositório e, opcionalmente, hospedar seu próprio projeto.

---

## 🚀 Passo a Passo da Construção

### 1. Configuração do Ambiente Local

**1.1. Clone o Repositório**

Abra seu terminal e clone o repositório do projeto para a sua máquina local.

```bash
git clone <URL_DO_SEU_REPOSITORIO_NO_GITHUB>
cd NOME_DO_DIRETORIO
```

**1.2. Crie um Ambiente Virtual**

É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.

```bash
python -m venv venv
source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
```

**1.3. Instale as Dependências**

Crie um arquivo `requirements.txt` com o seguinte conteúdo:

```
streamlit
pandas
gspread
gspread-dataframe
```

Em seguida, instale as bibliotecas:

```bash
pip install -r requirements.txt
```

### 2. Configuração da API do Google Sheets

Para que a aplicação possa acessar sua planilha, você precisa criar uma **Conta de Serviço** no Google Cloud Platform (GCP) e compartilhar a planilha com ela.

**2.1. Crie um Projeto no GCP**

*   Acesse o [Console do Google Cloud](https://console.cloud.google.com/).
*   Crie um novo projeto (ex: "Automacao Moodle").

**2.2. Ative as APIs Necessárias**

*   No menu de navegação, vá para **APIs e Serviços > Biblioteca**.
*   Procure e ative a **Google Drive API** e a **Google Sheets API**.

**2.3. Crie uma Conta de Serviço**

*   Vá para **APIs e Serviços > Credenciais**.
*   Clique em **Criar Credenciais > Conta de Serviço**.
*   Dê um nome à conta (ex: "leitor-planilha-moodle"), um ID e uma descrição.
*   Conceda a ela o papel de **Visualizador** (ou Editor, se precisar escrever na planilha).
*   Clique em **Concluído**.

**2.4. Gere uma Chave JSON**

*   Na lista de contas de serviço, clique na que você acabou de criar.
*   Vá para a aba **CHAVES**.
*   Clique em **ADICIONAR CHAVE > Criar nova chave**.
*   Selecione **JSON** e clique em **CRIAR**. O download de um arquivo `.json` será iniciado. **Guarde este arquivo em um local seguro!**

**2.5. Compartilhe a Planilha Google**

*   Abra o arquivo JSON que você baixou. Dentro dele, você encontrará um campo `"client_email"`. Copie o valor desse e-mail (algo como `leitor-planilha-moodle@seu-projeto.iam.gserviceaccount.com`).
*   Abra a sua Planilha Google.
*   Clique em **Compartilhar**.
*   Cole o e-mail da conta de serviço no campo de compartilhamento e conceda a permissão de **Editor**.

> **Importante:** Nunca exponha o conteúdo do seu arquivo JSON em código público (como no GitHub).

### 3. O Código: `app.py`

Abaixo, uma explicação detalhada de cada parte do arquivo `app.py`.

**3.1. Importações e Configuração da Página**

```python
import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gerador de CSV para Moodle",
    page_icon="📄",
    layout="centered"
)
```

*   Importamos as bibliotecas necessárias.
*   `st.set_page_config()` define o título, o ícone e o layout da página da aplicação Streamlit.

**3.2. Título e Autenticação**

```python
# --- TÍTULO E DESCRIÇÃO ---
st.title('Gerador de Arquivo CSV para Carga no Moodle')
st.markdown("""
Este aplicativo se conecta a uma Planilha Google, processa os dados dos usuários e gera um arquivo CSV pronto para ser usado na carga de usuários e matrículas no Moodle.
""")

# --- AUTENTICAÇÃO COM GOOGLE SHEETS ---
try:
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    st.success("✅ Autenticação com o Google Sheets bem-sucedida!")
except Exception as e:
    st.error("🚨 **Erro de autenticação com o Google Sheets.**")
    st.error("Por favor, verifique se as credenciais da conta de serviço (gcp_service_account) estão configuradas corretamente nos 'Secrets' do seu aplicativo Streamlit.")
    st.stop()
```

*   `st.title` e `st.markdown` exibem o cabeçalho e a descrição.
*   O bloco `try...except` é a parte mais crucial para a segurança. Ele tenta carregar as credenciais do Google a partir do `st.secrets`. Quando você for hospedar a aplicação no Streamlit Cloud, você não colocará o arquivo JSON no repositório. Em vez disso, você copiará o conteúdo do arquivo JSON e o colará em uma seção de "Secrets" nas configurações do seu app no Streamlit Cloud com o nome `gcp_service_account`.
*   Se a autenticação falhar, uma mensagem de erro clara é exibida e a execução do app é interrompida com `st.stop()`.

**3.3. Entradas do Usuário**

```python
# --- ENTRADAS DO USUÁRIO ---
st.header("1. Insira os dados da Planilha")
sheet_name = st.text_input("Nome da Planilha Google Sheets:", 'CARGAS_MOODLE_LEGADO')
worksheet_name = st.text_input("Nome da Página (Aba) de Origem na Planilha:")

st.header("2. Insira os dados do Curso")
course1_value = st.text_input("Identificador do Curso no Moodle (ex: NOME_CURSO_2024):")
group1_value = st.text_input("Identificador do Grupo/Turma no Moodle (ex: TURMA_A):")

st.header("3. Opções de Saída")
new_worksheet_name = st.text_input("Nome da Nova Página para Salvar os Dados Ajustados (deixe em branco para não salvar na planilha)")
```

*   Usamos `st.header` para criar seções e `st.text_input` para coletar as informações do usuário. Os valores inseridos são armazenados em variáveis para uso posterior.

**3.4. Lógica Principal e Processamento**

```python
# --- LÓGICA DE PROCESSAMENTO ---
if st.button('🚀 Processar e Gerar CSV'):
    # ... (validação das entradas) ...
    try:
        with st.spinner('Aguarde... Carregando e processando os dados...'):
            # 1. Conectar e carregar dados
            spreadsheet = gc.open(sheet_name)
            worksheet = spreadsheet.worksheet(worksheet_name)
            data = worksheet.get_all_records()
            df_gsheet = pd.DataFrame(data)

            # 2. Transformação dos dados
            columns_to_keep = ['CPF', 'Nome', 'Cargo', 'E-mail']
            df_cleaned = df_gsheet[columns_to_keep].copy()

            column_mapping = {
                'CPF': 'username', 'Nome': 'firstname',
                'Cargo': 'lastname', 'E-mail': 'email',
            }
            df_moodle = df_cleaned.rename(columns=column_mapping)

            # 3. Formatação e adição de colunas
            df_moodle['username'] = df_moodle['username'].astype(str).str.replace(r'[.-]', '', regex=True).str.zfill(11)
            df_moodle['password'] = 'Ead#1234'
            df_moodle['role1'] = 'student'
            df_moodle['course1'] = course1_value
            df_moodle['group1'] = group1_value

            # 4. Reordenar colunas
            output_columns = ['username', 'password', 'firstname', 'lastname', 'email', 'course1', 'role1', 'group1']
            df_output = df_moodle[output_columns]

        st.subheader("📊 Pré-visualização dos Dados Transformados:")
        st.dataframe(df_output.head())
        
        # ... (lógica para salvar na planilha e gerar CSV) ...

    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
```

*   `st.button` cria o botão que inicia o processo. O código dentro do `if` só é executado quando o botão é clicado.
*   `st.spinner` mostra uma mensagem de "carregando" enquanto o processamento pesado acontece.
*   **Pandas em Ação:**
    *   `pd.DataFrame(data)`: Converte os dados lidos da planilha em um DataFrame do Pandas.
    *   `df_cleaned = df_gsheet[columns_to_keep].copy()`: Seleciona apenas as colunas que nos interessam.
    *   `.rename()`: Renomeia as colunas para o padrão exigido pelo Moodle.
    *   `.astype(str).str.replace().str.zfill(11)`: Uma cadeia de métodos poderosa para limpar o CPF, removendo pontos e traços, e garantindo que ele tenha 11 dígitos (preenchendo com zeros à esquerda se necessário).
    *   Adicionamos as colunas estáticas e dinâmicas (`password`, `course1`, etc.).
    *   `df_output = df_moodle[output_columns]`: Reorganizamos as colunas para a ordem final correta.
*   `st.dataframe(df_output.head())` exibe as 5 primeiras linhas do resultado para que o usuário possa verificar.

**3.5. Salvar na Planilha e Gerar o CSV**

```python
# --- SALVAR EM NOVA PÁGINA NA PLANILHA ---
if new_worksheet_name:
    try:
        # ... (lógica para verificar se a aba já existe e criar/limpar) ...
        set_with_dataframe(new_worksheet, df_output, resize=True)
        st.success(f"✅ Dados salvos com sucesso na nova página '{new_worksheet_name}'.")
    except Exception as e:
        st.error(f"🚨 Falha ao salvar na planilha: {e}")

# --- GERAÇÃO E DOWNLOAD DO CSV ---
csv_data = df_output.to_csv(index=False).encode('utf-8')
output_filename = f"{course1_value}_{group1_value}.csv"

st.download_button(
    label="📥 Baixar Arquivo CSV",
    data=csv_data,
    file_name=output_filename,
    mime="text/csv"
)
```

*   Se o usuário forneceu um nome para uma nova aba, o código tenta criar essa aba (ou limpar uma existente com o mesmo nome) e usa `set_with_dataframe` da biblioteca `gspread-dataframe` para colar os dados do DataFrame na planilha.
*   `df_output.to_csv(index=False).encode('utf-8')`: Converte o DataFrame final em uma string no formato CSV, sem o índice do Pandas e com codificação UTF-8 para garantir a compatibilidade.
*   `st.download_button` cria o botão de download, que oferece o `csv_data` ao usuário com um nome de arquivo dinâmico.

### 4. Executando a Aplicação

Para rodar a aplicação localmente, certifique-se de que seu ambiente virtual está ativado e execute o seguinte comando no terminal:

```bash
streamlit run app.py
```

Seu navegador abrirá automaticamente com a aplicação em execução.

---

## 🖼️ Imagens e Visualização

Para uma melhor experiência no Obsidian, você pode adicionar screenshots em cada etapa do processo. Aqui estão algumas sugestões de imagens:

*   `[Image: Screenshot da aplicação Streamlit em execução no navegador.]`
*   `[Image: Screenshot do Console do Google Cloud mostrando as APIs ativadas.]`
*   `[Image: Screenshot da tela de criação da conta de serviço.]`
*   `[Image: Screenshot da Planilha Google com a janela de compartilhamento aberta, mostrando o e-mail da conta de serviço adicionado como Editor.]`
*   `[Image: Screenshot da pré-visualização dos dados na interface do Streamlit após o processamento.]`

---

## 📦 Hospedagem no Streamlit Cloud

1.  **Envie seu código para o GitHub:** Crie um repositório no GitHub e envie os arquivos `app.py` e `requirements.txt`. **NÃO ENVIE O ARQUIVO JSON.**
2.  **Crie uma conta no Streamlit Cloud:** Acesse [share.streamlit.io](https://share.streamlit.io/).
3.  **Implante o App:**
    *   Clique em "New app".
    *   Conecte sua conta do GitHub e selecione o repositório.
    *   No campo "Advanced settings", vá para a seção "Secrets".
    *   Copie **todo o conteúdo** do seu arquivo JSON de credenciais e cole no campo de texto. Salve o segredo com o nome `gcp_service_account`.
    *   Clique em "Deploy!".

O Streamlit irá instalar as dependências e iniciar sua aplicação, que agora estará acessível publicamente.

