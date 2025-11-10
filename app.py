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

# --- TÍTULO E DESCRIÇÃO ---
st.title('Gerador de Arquivo CSV para Carga no Moodle')
st.markdown("""
Este aplicativo se conecta a uma Planilha Google, processa os dados dos usuários e gera um arquivo CSV pronto para ser usado na carga de usuários e matrículas no Moodle.
""")

# --- AUTENTICAÇÃO COM GOOGLE SHEETS (MÉTODO SEGURO PARA STREAMLIT CLOUD) ---
try:
    # Carrega as credenciais a partir dos "Secrets" do Streamlit
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    st.success("✅ Autenticação com o Google Sheets bem-sucedida!")
except Exception as e:
    st.error("🚨 **Erro de autenticação com o Google Sheets.**")
    st.error("Por favor, verifique se as credenciais da conta de serviço (gcp_service_account) estão configuradas corretamente nos 'Secrets' do seu aplicativo Streamlit.")
    st.stop() # Interrompe a execução se a autenticação falhar

# --- ENTRADAS DO USUÁRIO ---
st.header("1. Insira os dados da Planilha")
sheet_name = st.text_input("Nome da Planilha Google Sheets:", 'CARGAS_MOODLE_LEGADO')
worksheet_name = st.text_input("Nome da Página (Aba) de Origem na Planilha:")

st.header("2. Insira os dados do Curso")
course1_value = st.text_input("Identificador do Curso no Moodle (ex: NOME_CURSO_2024):")
group1_value = st.text_input("Identificador do Grupo/Turma no Moodle (ex: TURMA_A):")

st.header("3. Opções de Saída")
new_worksheet_name = st.text_input("Nome da Nova Página para Salvar os Dados Ajustados (deixe em branco para não salvar na planilha)")


# --- LÓGICA DE PROCESSAMENTO ---
if st.button('🚀 Processar e Gerar CSV'):
    # Validação das entradas
    if not all([sheet_name, worksheet_name, course1_value, group1_value]):
        st.warning("⚠️ Por favor, preencha todos os campos de entrada antes de processar.")
    else:
        try:
            with st.spinner('Aguarde... Carregando e processando os dados...'):
                # Abrir a planilha e a página específica
                spreadsheet = gc.open(sheet_name)
                worksheet = spreadsheet.worksheet(worksheet_name)

                # Obter todos os valores e converter para DataFrame
                data = worksheet.get_all_records()
                df_gsheet = pd.DataFrame(data)

                st.success(f"Dados carregados com sucesso da planilha '{sheet_name}', página '{worksheet_name}'.")

                # --- TRANSFORMAÇÃO DOS DADOS ---
                columns_to_keep = ['CPF', 'Nome', 'E-mail']
                if not all(col in df_gsheet.columns for col in columns_to_keep):
                    st.error(f"Erro: A planilha de origem deve conter as colunas: {', '.join(columns_to_keep)}")
                    st.stop()
                
                df_cleaned = df_gsheet[columns_to_keep].copy()

                column_mapping = {
                    'CPF': 'username',
                    'Nome': 'firstname',
                    'E-mail': 'email',
                }
                df_moodle = df_cleaned.rename(columns=column_mapping)

                # O campo 'lastname' (sobrenome) é obrigatório no Moodle. Usamos '.' como padrão.
                df_moodle['lastname'] = '.'

                # Limpeza e formatação do CPF para ser o 'username'
                df_moodle['username'] = df_moodle['username'].astype(str).str.replace(r'[.-]', '', regex=True)
                df_moodle['username'] = df_moodle['username'].str.zfill(11)

                # Adicionar colunas fixas e dinâmicas
                df_moodle['password'] = 'Ead#1234'
                df_moodle['role1'] = 'student'
                df_moodle['course1'] = course1_value
                df_moodle['group1'] = group1_value

                # Reordenar colunas para o formato final
                output_columns = ['username', 'password', 'firstname', 'lastname', 'email', 'course1', 'role1', 'group1']
                df_output = df_moodle[output_columns]

            st.subheader("📊 Pré-visualização dos Dados Transformados:")
            st.dataframe(df_output.head())

            # --- GERAÇÃO E DOWNLOAD DO CSV (COM DADOS PUROS) ---
            csv_data = df_output.to_csv(index=False).encode('utf-8')
            output_filename = f"{course1_value}_{group1_value}.csv"

            st.success(f"🎉 Arquivo '{output_filename}' processado e pronto para download!")

            st.download_button(
                label="📥 Baixar Arquivo CSV",
                data=csv_data,
                file_name=output_filename,
                mime="text/csv"
            )

            # --- SALVAR EM NOVA PÁGINA NA PLANILHA (COM DADOS MODIFICADOS) ---
            if new_worksheet_name:
                try:
                    with st.spinner(f"Verificando e salvando na página '{new_worksheet_name}'..."):
                        existing_worksheets = [ws.title for ws in spreadsheet.worksheets()]
                        if new_worksheet_name in existing_worksheets:
                            st.warning(f"⚠️ A página '{new_worksheet_name}' já existe e será sobrescrita.")
                            new_worksheet = spreadsheet.worksheet(new_worksheet_name)
                            new_worksheet.clear()
                        else:
                            new_worksheet = spreadsheet.add_worksheet(
                                title=new_worksheet_name,
                                rows=df_output.shape[0] + 1,
                                cols=df_output.shape[1]
                            )
                        
                        # Cria uma cópia do dataframe e adiciona o apóstrofo para forçar formato de texto no Sheets
                        df_for_sheets = df_output.copy()
                        df_for_sheets['username'] = "'" + df_for_sheets['username']
                        set_with_dataframe(new_worksheet, df_for_sheets, resize=True)

                        st.success(f"✅ Dados salvos com sucesso na nova página '{new_worksheet_name}' da planilha '{sheet_name}'.")
                except Exception as e:
                    st.error(f"🚨 Falha ao salvar os dados na nova página da planilha: {e}")
                    st.stop()

        except gspread.exceptions.SpreadsheetNotFound:
            st.error(f"🚨 Erro: A planilha '{sheet_name}' não foi encontrada. Verifique o nome e as permissões de compartilhamento.")
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"🚨 Erro: A página de origem '{worksheet_name}' não foi encontrada na planilha '{sheet_name}'. Verifique o nome da aba.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento: {e}")
            st.error("Verifique se os nomes da planilha/página e os cabeçalhos das colunas ('CPF', 'Nome', 'E-mail') estão corretos.")