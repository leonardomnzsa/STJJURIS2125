import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random
import os
import openai  # Adicionado import
import json # Adicionado para parsear resposta da API
import re # Adicionado para extrair JSON

# Configuração da página
st.set_page_config(
    page_title="Dashboard Informativos STF",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Função para configurar a API da OpenAI
def configurar_openai():
    try:
        # Tenta obter a chave dos segredos
        api_key = st.secrets.get("openai", {}).get("api_key")
        if api_key:
            openai.api_key = api_key
            return True
        else:
            # Chave não encontrada ou seção [openai] ausente
            return False
    except Exception as e:
        st.error(f"Erro ao configurar a API da OpenAI: {e}")
        return False

# Função para carregar os dados (corrigida para Streamlit Cloud)
@st.cache_data
def carregar_dados():
    # Caminho relativo para o arquivo de dados
    arquivo_final = 'data/informativos_stf_2021_2025.xlsx'
    
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(arquivo_final):
            st.error(f"Arquivo de dados não encontrado em: {arquivo_final}")
            return None
            
        # Carregar o arquivo Excel
        df = pd.read_excel(arquivo_final)
        
        # Converter a coluna de data para datetime
        df["Data Julgamento"] = pd.to_datetime(df["Data Julgamento"], format="%d/%m/%Y", errors="coerce")
        
        # Garantir que as novas colunas existam, preenchendo com NaN se não existirem
        if 'Legislação' not in df.columns:
            df['Legislação'] = pd.NA
        if 'Notícia completa' not in df.columns:
            df['Notícia completa'] = pd.NA
            
        # Garantir que a coluna Matéria exista e preencher NaNs
        if 'Matéria' not in df.columns:
            df['Matéria'] = 'Não especificada'
        else:
            df['Matéria'] = df['Matéria'].fillna('Não especificada')
            
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {str(e)}")
        return None

# Estilo CSS personalizado
def aplicar_estilo():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #0e1117;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0e1117;
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .reading-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #4e8cff;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .reading-card h3 {
        color: #1f1f1f;
        margin-bottom: 15px;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 10px;
    }
    .reading-card-meta {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }
    .reading-card-content {
        color: #333;
    }
    .highlight {
        color: #ff4b4b;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: #888888;
        font-size: 0.8rem;
    }
    .assertiva-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 4px solid #4e8cff;
    }
    .assertiva-card.correct {
        border-left: 4px solid #28a745;
    }
    .assertiva-card.incorrect {
        border-left: 4px solid #dc3545;
    }
    .feedback-correct {
        color: #28a745;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(40, 167, 69, 0.1);
    }
    .feedback-incorrect {
        color: #dc3545;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(220, 53, 69, 0.1);
    }
    .question-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 4px solid #17a2b8;
    }
    .answer-card {
        background-color: #f0f7ff;
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 20px;
        border-left: 4px solid #4e8cff;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para gerar assertivas (SIMULAÇÃO - será substituída pela API)
def gerar_assertivas_simuladas(df, materias_selecionadas=None, num_assertivas=5):
    assertivas = []
    
    # Filtrar por matéria se selecionado
    if materias_selecionadas and 'Todas' not in materias_selecionadas:
        df_filtrado_materia = df[df['Matéria'].isin(materias_selecionadas)]
    else:
        df_filtrado_materia = df
        
    # Filtrar apenas registros com resumo não nulo
    df_com_resumo = df_filtrado_materia[df_filtrado_materia["Resumo"].notna()]
    
    if len(df_com_resumo) < 1:
        return [{"texto": "Não há dados suficientes para gerar assertivas com os filtros selecionados.", "resposta": None, "explicacao": ""}]
    
    # Selecionar registros aleatórios
    indices = random.sample(range(len(df_com_resumo)), min(num_assertivas * 2, len(df_com_resumo)))
    registros_selecionados = df_com_resumo.iloc[indices]
    
    # Tipos de assertivas
    tipos_assertivas = [
        "O STF decidiu que {tese}.",
        "De acordo com o informativo {informativo}, {resumo_parcial}.",
        "No julgamento de {classe} em {data}, o STF entendeu que {resumo_parcial}.",
        "É correto afirmar que, segundo o STF, {tese}.",
        "O {orgao} do STF, ao julgar {classe} em {data}, firmou entendimento de que {resumo_parcial}."
    ]
    
    # Gerar assertivas verdadeiras e falsas
    count = 0
    for _, registro in registros_selecionados.iterrows():
        if count >= num_assertivas:
            break
            
        # Obter dados do registro
        informativo = registro["Informativo"]
        classe = registro["Classe Processo"]
        data = registro["Data Julgamento"].strftime("%d/%m/%Y") if pd.notna(registro["Data Julgamento"]) else "data não especificada"
        
        # Verificar se há resumo ou tese
        if pd.notna(registro["Resumo"]):
            resumo = registro["Resumo"]
            # Pegar apenas parte do resumo para não ficar muito longo
            palavras = resumo.split()
            if len(palavras) > 15:
                resumo_parcial = " ".join(palavras[:15]) + "..."
            else:
                resumo_parcial = resumo
        else:
            resumo_parcial = "o tema foi objeto de análise pelo tribunal"
        
        tese = registro["Tese Julgado"] if pd.notna(registro["Tese Julgado"]) else resumo_parcial
        
        # Pular se tese for muito curta ou vazia
        if not tese or len(str(tese)) < 10:
            continue
            
        # Escolher aleatoriamente se a assertiva será verdadeira ou falsa
        e_verdadeira = random.choice([True, False])
        
        # Escolher um tipo de assertiva aleatoriamente
        tipo_assertiva = random.choice(tipos_assertivas)
        
        # Formatar a assertiva
        if e_verdadeira:
            texto_assertiva = tipo_assertiva.format(
                tese=tese,
                informativo=informativo,
                resumo_parcial=resumo_parcial,
                classe=classe,
                data=data,
                orgao="Plenário"
            )
        else:
            # Para assertivas falsas, modificamos algum elemento
            modificadores = [
                lambda t: "Não " + t[0].lower() + t[1:] if t else t,  # Negar a afirmação
                lambda t: t.replace("pode", "não pode") if "pode" in t else t.replace("não pode", "pode"),  # Inverter permissões
                lambda t: t.replace("constitucional", "inconstitucional") if "constitucional" in t else t.replace("inconstitucional", "constitucional"),  # Inverter constitucionalidade
                lambda t: t.replace("direito", "dever") if "direito" in t else t.replace("dever", "direito"),  # Trocar direito por dever
            ]
            
            modificador = random.choice(modificadores)
            texto_modificado = modificador(str(tese))
            
            texto_assertiva = tipo_assertiva.format(
                tese=texto_modificado,
                informativo=informativo,
                resumo_parcial=modificador(resumo_parcial),
                classe=classe,
                data=data,
                orgao="Plenário"
            )
        
        assertivas.append({
            "texto": texto_assertiva,
            "resposta": e_verdadeira,
            "explicacao": f"Informativo {informativo}: {resumo_parcial}"
        })
        count += 1
        
    # Se não gerou assertivas suficientes, adicionar mensagem
    if not assertivas:
         return [{"texto": "Não foi possível gerar assertivas com os filtros selecionados.", "resposta": None, "explicacao": ""}]
         
    return assertivas

# Função para extrair JSON de uma string (mais robusta)
def extrair_json(texto):
    # Tenta encontrar o JSON principal (lista ou objeto)
    match_lista = re.search(r'(\[.*?\])', texto, re.DOTALL)
    match_objeto = re.search(r'(\{.*?\})', texto, re.DOTALL)
    
    if match_lista:
        return match_lista.group(1)
    elif match_objeto:
         # Se encontrar objeto, mas o prompt pede lista, pode ser um erro da API
         # Mesmo assim, retornamos o objeto para tentar o parse
        return match_objeto.group(1)
    else:
        # Se não encontrar nada parecido com JSON, retorna None
        return None

# Função para gerar assertivas usando a API do ChatGPT (Refinada)
def gerar_assertivas_api(df, materias_selecionadas=None, num_assertivas=5):
    # Configurar a API
    api_configurada = configurar_openai()
    if not api_configurada:
        st.warning("A chave da API da OpenAI não está configurada. Usando a simulação de assertivas.")
        return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)

    # Filtrar por matéria se selecionado
    if materias_selecionadas and 'Todas' not in materias_selecionadas:
        df_filtrado_materia = df[df['Matéria'].isin(materias_selecionadas)]
    else:
        df_filtrado_materia = df
        
    # Selecionar alguns informativos relevantes aleatoriamente
    df_com_resumo = df_filtrado_materia[df_filtrado_materia["Resumo"].notna() | df_filtrado_materia["Tese Julgado"].notna()]
    if len(df_com_resumo) < 1:
        return [{"texto": "Não há dados suficientes para gerar assertivas com os filtros selecionados.", "resposta": None, "explicacao": ""}]
        
    num_exemplos = min(len(df_com_resumo), 5) # Usar até 5 informativos como base
    indices = random.sample(range(len(df_com_resumo)), num_exemplos)
    registros_selecionados = df_com_resumo.iloc[indices]
    
    # Criar contexto com os informativos selecionados
    contexto_informativos = """
    Baseado nos seguintes trechos de informativos do STF:
    """
    for _, row in registros_selecionados.iterrows():
        contexto_informativos += f"\n---\nInformativo: {row['Informativo']}\nMatéria: {row['Matéria']}\n"
        if pd.notna(row['Tese Julgado']):
            contexto_informativos += f"Tese: {row['Tese Julgado']}\n"
        if pd.notna(row['Resumo']):
            contexto_informativos += f"Resumo: {row['Resumo']}\n"
            
    # Construir o prompt para a API (Refinado)
    prompt = f"""{contexto_informativos}
    
    Elabore {num_assertivas} assertivas de VERDADEIRO ou FALSO, no estilo de questões de concurso público (Cespe/Cebraspe, FGV), sobre os temas abordados nos informativos acima. 
    Para cada assertiva, forneça:
    1. O texto da assertiva.
    2. A resposta correta (True para VERDADEIRO, False para FALSO).
    3. Uma breve explicação baseada no informativo correspondente.
    
    Formate a resposta EXATAMENTE como um JSON contendo uma lista de objetos, onde cada objeto tem as chaves "texto", "resposta" e "explicacao".
    Exemplo de formato JSON:
    [
      {{"texto": "Assertiva 1...", "resposta": True, "explicacao": "Conforme Informativo X..."}},
      {{"texto": "Assertiva 2...", "resposta": False, "explicacao": "Segundo o Informativo Y..."}}
    ]
    
    IMPORTANTE: Sua resposta deve conter APENAS o código JSON válido, começando com '[' e terminando com ']', sem nenhum texto introdutório, comentários ou explicações adicionais fora do JSON.
    """

    try:
        # Chamar a API da OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", # Ou gpt-4 se disponível e preferível
            messages=[
                {"role": "system", "content": "Você é um especialista em criar questões de concurso sobre jurisprudência do STF. Responda APENAS com o JSON solicitado."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500, # Aumentar tokens para comportar JSON e contexto
            temperature=0.6, # Um pouco menos de criatividade para focar no formato
            # response_format={ "type": "json_object" } # Remover se causar problemas ou não for suportado consistentemente
        )
        resposta_bruta = response.choices[0].message.content.strip()
        
        # Tentar extrair o JSON da resposta bruta
        json_extraido_str = extrair_json(resposta_bruta)
        
        if not json_extraido_str:
            st.error(f"Não foi possível encontrar um bloco JSON na resposta da API. Resposta recebida: '{resposta_bruta[:200]}...'. Usando simulação.")
            print(f"JSON não encontrado. Resposta bruta: {resposta_bruta}") # Log para debug
            return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)
            
        # Tentar parsear o JSON extraído
        assertivas_api = json.loads(json_extraido_str)
        
        # Validar a estrutura da resposta (lista de dicionários com chaves corretas)
        if isinstance(assertivas_api, list) and all(isinstance(item, dict) and all(key in item for key in ["texto", "resposta", "explicacao"]) for item in assertivas_api):
            # Verificar se o número de assertivas é razoável (evitar listas vazias ou muito grandes)
            if 1 <= len(assertivas_api) <= num_assertivas * 2: # Permite alguma flexibilidade
                 return assertivas_api[:num_assertivas] # Retorna no máximo o número solicitado
            else:
                 st.warning(f"API retornou um número inesperado de assertivas ({len(assertivas_api)}). Usando simulação.")
                 print(f"Número inesperado de assertivas. JSON: {json_extraido_str}") # Log
                 return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)
        else:
            st.error("A resposta da API não continha uma lista válida de assertivas no formato JSON esperado. Usando simulação.")
            print(f"Resposta JSON inválida recebida: {json_extraido_str}") # Log para debug
            return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)
            
    except json.JSONDecodeError:
        st.error(f"Erro ao decodificar o JSON extraído da API. JSON extraído: '{json_extraido_str[:200]}...'. Usando simulação.")
        print(f"Erro JSONDecodeError. JSON extraído: {json_extraido_str}") # Log para debug
        return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)
    except openai.AuthenticationError:
        st.error("Erro de autenticação com a API da OpenAI. Verifique sua chave de API. Usando simulação.")
        return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)
    except Exception as e:
        st.error(f"Erro ao chamar a API da OpenAI para gerar assertivas: {e}. Usando simulação.")
        print(f"Erro Exception na API: {e}") # Log para debug
        return gerar_assertivas_simuladas(df, materias_selecionadas, num_assertivas)

# Função para encontrar registros relevantes para a pergunta
def encontrar_registros_relevantes(pergunta, df, max_registros=3):
    # Palavras-chave para buscar nos dados
    palavras_chave = [palavra.lower() for palavra in pergunta.split() if len(palavra) > 3]
    
    # Se não houver palavras-chave significativas, retornar lista vazia
    if not palavras_chave:
        return []
    
    # Buscar registros relevantes
    registros_relevantes = []
    
    for _, row in df.iterrows():
        pontuacao = 0
        
        # Verificar título
        if pd.notna(row["Título"]):
            for palavra in palavras_chave:
                if palavra in row["Título"].lower():
                    pontuacao += 3  # Peso maior para correspondência no título
        
        # Verificar resumo
        if pd.notna(row["Resumo"]):
            for palavra in palavras_chave:
                if palavra in row["Resumo"].lower():
                    pontuacao += 2
        
        # Verificar matéria
        if pd.notna(row["Matéria"]):
            for palavra in palavras_chave:
                if palavra in row["Matéria"].lower():
                    pontuacao += 1
        
        # Verificar ramo do direito
        if pd.notna(row["Ramo Direito"]):
            for palavra in palavras_chave:
                if palavra in row["Ramo Direito"].lower():
                    pontuacao += 1
                    
        # Verificar legislação
        if 'Legislação' in row and pd.notna(row["Legislação"]):
            for palavra in palavras_chave:
                if palavra in row["Legislação"].lower():
                    pontuacao += 1
                    
        # Verificar notícia completa
        if 'Notícia completa' in row and pd.notna(row["Notícia completa"]):
            for palavra in palavras_chave:
                if palavra in row["Notícia completa"].lower():
                    pontuacao += 1
        
        # Se houver pontuação, adicionar à lista de registros relevantes
        if pontuacao > 0:
            registros_relevantes.append((pontuacao, row))
    
    # Ordenar por relevância (pontuação)
    registros_relevantes.sort(reverse=True, key=lambda x: x[0])
    
    # Retornar apenas os registros mais relevantes
    return [registro for _, registro in registros_relevantes[:max_registros]]

# Função para criar um contexto baseado nos registros relevantes
def criar_contexto(registros_relevantes):
    if not registros_relevantes:
        return ""
    
    contexto = "Contexto dos informativos do STF:\n\n"
    
    for i, registro in enumerate(registros_relevantes):
        informativo = registro["Informativo"]
        data = registro["Data Julgamento"].strftime("%d/%m/%Y") if pd.notna(registro["Data Julgamento"]) else "data não especificada"
        titulo = registro["Título"] if pd.notna(registro["Título"]) else "Título não disponível"
        
        contexto += f"Informativo {informativo} ({data}): {titulo}\n"
        
        if pd.notna(registro["Resumo"]):
            contexto += f"Resumo: {registro['Resumo']}\n"
        
        if pd.notna(registro["Tese Julgado"]):
            contexto += f"Tese: {registro['Tese Julgado']}\n"
            
        if 'Legislação' in registro and pd.notna(registro["Legislação"]):
            contexto += f"Legislação: {registro['Legislação']}\n"
            
        if 'Notícia completa' in registro and pd.notna(registro["Notícia completa"]):
            contexto += f"Notícia Completa: {registro['Notícia completa']}\n"
        
        contexto += "\n"
    
    return contexto

# Função para obter resposta da API do ChatGPT
def obter_resposta_chatgpt(pergunta, df):
    # Configurar a API
    api_configurada = configurar_openai()
    if not api_configurada:
        st.warning("A chave da API da OpenAI não está configurada. Usando a simulação de resposta.")
        return simular_resposta(pergunta, df)

    # Encontrar registros relevantes e criar contexto
    registros_relevantes = encontrar_registros_relevantes(pergunta, df)
    contexto = criar_contexto(registros_relevantes)

    # Construir o prompt
    prompt = f"""Você é um assistente especializado em informativos do Supremo Tribunal Federal do Brasil.
Responda à pergunta do usuário com base apenas nas informações fornecidas abaixo.
Se as informações não forem suficientes para responder à pergunta, diga que não há informações suficientes nos informativos entre 2021 e 2025.

CONTEXTO DOS INFORMATIVOS:
{contexto}

PERGUNTA DO USUÁRIO:
{pergunta}

RESPOSTA:"""

    try:
        # Chamar a API da OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Ou outro modelo de sua preferência
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em informativos do STF."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,  # Limitar o tamanho da resposta
            temperature=0.5, # Controlar a criatividade da resposta
        )
        resposta_api = response.choices[0].message.content.strip()
        return resposta_api
    except openai.AuthenticationError:
        st.error("Erro de autenticação com a API da OpenAI. Verifique sua chave de API.")
        return simular_resposta(pergunta, df) # Fallback para simulação
    except Exception as e:
        st.error(f"Erro ao chamar a API da OpenAI: {e}")
        return simular_resposta(pergunta, df) # Fallback para simulação

# Função para simular respostas às perguntas (Fallback)
def simular_resposta(pergunta, df):
    # Buscar registros relevantes
    registros_relevantes = encontrar_registros_relevantes(pergunta, df)
    
    # Se não houver registros relevantes, retornar mensagem
    if not registros_relevantes:
        return "Não encontrei informações específicas sobre essa pergunta nos informativos do STF entre 2021 e 2025."
    
    # Construir resposta com base nos registros mais relevantes
    resposta = "(Simulação) Com base nos informativos do STF, posso informar que:\n\n"
    
    for i, registro in enumerate(registros_relevantes):
        informativo = registro["Informativo"]
        data = registro["Data Julgamento"].strftime("%d/%m/%Y") if pd.notna(registro["Data Julgamento"]) else "data não especificada"
        titulo = registro["Título"] if pd.notna(registro["Título"]) else "Título não disponível"
        
        resposta += f"**Informativo {informativo} ({data})**: {titulo}\n\n"
        
        if pd.notna(registro["Resumo"]):
            resposta += f"{registro['Resumo']}\n\n"
        elif pd.notna(registro["Tese Julgado"]):
            resposta += f"**Tese**: {registro['Tese Julgado']}\n\n"
            
        if 'Legislação' in registro and pd.notna(registro["Legislação"]):
            resposta += f"**Legislação**: {registro['Legislação']}\n\n"
            
        if 'Notícia completa' in registro and pd.notna(registro["Notícia completa"]):
            resposta += f"**Notícia Completa**: {registro['Notícia completa']}\n\n"
        
        if i < len(registros_relevantes) - 1:
            resposta += "---\n\n"
    
    return resposta

# Função principal
def main():
    # Aplicar estilo
    aplicar_estilo()
    
    # Cabeçalho
    st.markdown('<div class="main-header">Dashboard Informativos STF (2021-2025)</div>', unsafe_allow_html=True)
    
    # Carregar dados
    df = carregar_dados()
    
    if df is None:
        st.error("Não foi possível carregar os dados. Por favor, verifique se o arquivo existe.")
        return
    
    # Sidebar para filtros
    with st.sidebar:
        st.header("Filtros Gerais")
        
        # Filtro por Informativo
        informativos = sorted(df["Informativo"].unique())
        informativo_selecionado = st.selectbox("Número do Informativo", 
                                              options=["Todos"] + list(informativos))
        
        # Filtro por Ramo do Direito
        ramos_direito = sorted(df["Ramo Direito"].dropna().unique())
        ramo_selecionado = st.selectbox("Ramo do Direito", 
                                       options=["Todos"] + list(ramos_direito))
        
        # Filtro por Classe Processual
        classes_processo = sorted(df["Classe Processo"].unique())
        classe_selecionada = st.selectbox("Classe Processual", 
                                         options=["Todos"] + list(classes_processo))
        
        # Filtro por Repercussão Geral
        repercussoes = sorted(df["Repercussão Geral"].dropna().unique())
        repercussao_selecionada = st.selectbox("Repercussão Geral", 
                                              options=["Todos"] + list(repercussoes))
        
        # Filtro por Data
        min_date = df["Data Julgamento"].min().date()
        max_date = df["Data Julgamento"].max().date()
        
        data_selecionada = st.date_input(
            "Intervalo de Data",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Barra de pesquisa
        termo_pesquisa = st.text_input("Pesquisar termo", "")
        
        # Botão para limpar filtros
        if st.button("Limpar Filtros"):
            informativo_selecionado = "Todos"
            ramo_selecionado = "Todos"
            classe_selecionada = "Todos"
            repercussao_selecionada = "Todos"
            data_selecionada = (min_date, max_date)
            termo_pesquisa = ""
            # Limpar também o estado das assertivas e matérias selecionadas
            if "materias_assertivas" in st.session_state:
                st.session_state.materias_assertivas = ['Todas']
            if "assertivas" in st.session_state:
                del st.session_state["assertivas"]
            if "respostas_usuario" in st.session_state:
                del st.session_state["respostas_usuario"]
            st.rerun() # Forçar recarregamento da página para aplicar limpeza
    
    # Aplicar filtros gerais
    df_filtrado = df.copy()
    
    # Filtro por Informativo
    if informativo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Informativo"] == informativo_selecionado]
    
    # Filtro por Ramo do Direito
    if ramo_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Ramo Direito"] == ramo_selecionado]
    
    # Filtro por Classe Processual
    if classe_selecionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Classe Processo"] == classe_selecionada]
    
    # Filtro por Repercussão Geral
    if repercussao_selecionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Repercussão Geral"] == repercussao_selecionada]
    
    # Filtro por Data
    if len(data_selecionada) == 2:
        start_date, end_date = data_selecionada
        df_filtrado = df_filtrado[(df_filtrado["Data Julgamento"].dt.date >= start_date) & 
                                 (df_filtrado["Data Julgamento"].dt.date <= end_date)]
    
    # Filtro por termo de pesquisa
    if termo_pesquisa:
        mask = (
            df_filtrado["Título"].fillna("").str.contains(termo_pesquisa, case=False) |
            df_filtrado["Resumo"].fillna("").str.contains(termo_pesquisa, case=False) |
            df_filtrado["Matéria"].fillna("").str.contains(termo_pesquisa, case=False) |
            df_filtrado["Tese Julgado"].fillna("").str.contains(termo_pesquisa, case=False) |
            df_filtrado["Legislação"].fillna("").str.contains(termo_pesquisa, case=False) | # Adicionado filtro por Legislação
            df_filtrado["Notícia completa"].fillna("").str.contains(termo_pesquisa, case=False) # Adicionado filtro por Notícia completa
        )
        df_filtrado = df_filtrado[mask]
    
    # Criar abas para as diferentes seções
    tab1, tab2, tab3, tab4 = st.tabs(["Visualização dos Informativos", "Estatísticas Interativas", 
                                      "Assertivas para Estudo", "Pergunte para a Result"])
    
    # Aba 1: Visualização dos Informativos
    with tab1:
        st.markdown('<div class="sub-header">Visualização dos Informativos</div>', unsafe_allow_html=True)
        
        # Mostrar número de resultados
        st.write(f"Exibindo {len(df_filtrado)} de {len(df)} informativos.")
        
        # Opções de visualização
        visualizacao = st.radio(
            "Modo de visualização:",
            ["Tabela", "Cards de Leitura"],
            horizontal=True
        )
        
        if visualizacao == "Tabela":
            # Tabela interativa
            if not df_filtrado.empty:
                # Formatar a data para exibição
                df_exibicao = df_filtrado.copy()
                df_exibicao["Data Julgamento"] = df_exibicao["Data Julgamento"].dt.strftime("%d/%m/%Y")
                
                # Selecionar colunas para exibição (incluindo as novas colunas)
                colunas_exibicao = ["Informativo", "Classe Processo", "Data Julgamento", "Título", "Ramo Direito", "Matéria", "Legislação", "Notícia completa"]
                # Filtrar colunas que realmente existem no DataFrame
                colunas_exibicao_existentes = [col for col in colunas_exibicao if col in df_exibicao.columns]
                st.dataframe(df_exibicao[colunas_exibicao_existentes], use_container_width=True)
                
                # Detalhes do informativo selecionado
                st.markdown('<div class="sub-header">Detalhes do Informativo Selecionado</div>', unsafe_allow_html=True)
                
                # Permitir selecionar um informativo para ver detalhes
                indices = df_exibicao.index.tolist()
                if indices:
                    # Usar Título + Informativo como chave única para seleção
                    opcoes_select = [f"{row['Título']} (Inf. {row['Informativo']})" for _, row in df_exibicao.iterrows()]
                    selecao_str = st.selectbox("Selecione um informativo para ver detalhes:", opcoes_select)
                    
                    # Encontrar o índice correspondente à seleção
                    indice_selecionado = None
                    for idx, opcao in enumerate(opcoes_select):
                        if opcao == selecao_str:
                            indice_selecionado = df_exibicao.index[idx]
                            break
                            
                    if indice_selecionado is not None:
                        informativo_selecionado = df_exibicao.loc[indice_selecionado]
                        
                        # Exibir detalhes em cards
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.markdown(f"**Informativo:** {informativo_selecionado['Informativo']}")
                            st.markdown(f"**Classe Processo:** {informativo_selecionado['Classe Processo']}")
                            st.markdown(f"**Data Julgamento:** {informativo_selecionado['Data Julgamento']}")
                            st.markdown(f"**Ramo Direito:** {informativo_selecionado['Ramo Direito']}")
                            st.markdown(f"**Matéria:** {informativo_selecionado['Matéria']}")
                            st.markdown(f"**Repercussão Geral:** {informativo_selecionado['Repercussão Geral']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.markdown(f"**Título:** {informativo_selecionado['Título']}")
                            
                            # Verificar se há tese julgada
                            if pd.notna(informativo_selecionado["Tese Julgado"]):
                                st.markdown("**Tese Julgada:**")
                                st.markdown(f"{informativo_selecionado['Tese Julgado']}")
                            
                            # Verificar se há resumo
                            if pd.notna(informativo_selecionado["Resumo"]):
                                st.markdown("**Resumo:**")
                                st.markdown(f"{informativo_selecionado['Resumo']}")
                                
                            # Exibir Legislação
                            if 'Legislação' in informativo_selecionado and pd.notna(informativo_selecionado["Legislação"]):
                                st.markdown("**Legislação:**")
                                st.markdown(f"{informativo_selecionado['Legislação']}")
                                
                            # Exibir Notícia Completa
                            if 'Notícia completa' in informativo_selecionado and pd.notna(informativo_selecionado["Notícia completa"]):
                                st.markdown("**Notícia Completa:**")
                                st.markdown(f"{informativo_selecionado['Notícia completa']}")
                                
                            st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("Nenhum informativo encontrado com os filtros selecionados.")
        
        else:  # Cards de Leitura
            if not df_filtrado.empty:
                # Ordenar por data (mais recente primeiro)
                df_cards = df_filtrado.sort_values(by="Data Julgamento", ascending=False)
                
                # Paginação
                items_por_pagina = 5
                num_paginas = (len(df_cards) + items_por_pagina - 1) // items_por_pagina
                
                if num_paginas > 1:
                    pagina_atual = st.number_input("Página", min_value=1, max_value=num_paginas, value=1) - 1
                    inicio = pagina_atual * items_por_pagina
                    fim = min(inicio + items_por_pagina, len(df_cards))
                    df_pagina = df_cards.iloc[inicio:fim]
                    st.write(f"Mostrando {inicio+1}-{fim} de {len(df_cards)} informativos")
                else:
                    df_pagina = df_cards
                
                # Exibir cards
                for _, row in df_pagina.iterrows():
                    st.markdown(f"""
                    <div class="reading-card">
                        <h3>{row['Título'] if pd.notna(row['Título']) else 'Sem título'}</h3>
                        <div class="reading-card-meta">
                            <strong>Informativo:</strong> {row['Informativo']} | 
                            <strong>Data:</strong> {row['Data Julgamento'].strftime('%d/%m/%Y') if pd.notna(row['Data Julgamento']) else 'Data não disponível'} | 
                            <strong>Classe:</strong> {row['Classe Processo']} | 
                            <strong>Ramo:</strong> {row['Ramo Direito'] if pd.notna(row['Ramo Direito']) else 'Não especificado'}
                        </div>
                        <div class="reading-card-content">
                    """, unsafe_allow_html=True)
                    
                    # Verificar se há tese julgada
                    if pd.notna(row["Tese Julgado"]):
                        st.markdown("<strong>Tese Julgada:</strong>", unsafe_allow_html=True)
                        st.markdown(f"{row['Tese Julgado']}")
                    
                    # Verificar se há resumo
                    if pd.notna(row["Resumo"]):
                        st.markdown("<strong>Resumo:</strong>", unsafe_allow_html=True)
                        st.markdown(f"{row['Resumo']}")
                        
                    # Exibir Legislação
                    if 'Legislação' in row and pd.notna(row["Legislação"]):
                        st.markdown("<strong>Legislação:</strong>", unsafe_allow_html=True)
                        st.markdown(f"{row['Legislação']}")
                        
                    # Exibir Notícia Completa
                    if 'Notícia completa' in row and pd.notna(row["Notícia completa"]):
                        st.markdown("<strong>Notícia Completa:</strong>", unsafe_allow_html=True)
                        st.markdown(f"{row['Notícia completa']}")
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                st.warning("Nenhum informativo encontrado com os filtros selecionados.")
    
    # Aba 2: Estatísticas Interativas
    with tab2:
        st.markdown('<div class="sub-header">Estatísticas Interativas</div>', unsafe_allow_html=True)
        
        # Verificar se há dados suficientes para gerar estatísticas
        if len(df) > 0:
            # Layout em colunas para os gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de distribuição por Ramo do Direito
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Distribuição por Ramo do Direito")
                
                # Contar ocorrências de cada ramo do direito
                ramo_counts = df["Ramo Direito"].value_counts().reset_index()
                ramo_counts.columns = ["Ramo do Direito", "Quantidade"]
                
                # Limitar para os 10 principais ramos
                top_ramos = ramo_counts.head(10)
                
                # Criar gráfico de barras
                fig = px.bar(
                    top_ramos, 
                    x="Quantidade", 
                    y="Ramo do Direito",
                    orientation="h",
                    color="Quantidade",
                    color_continuous_scale="Blues",
                    title="Top 10 Ramos do Direito"
                )
                
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                # Gráfico de distribuição por Repercussão Geral
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Proporção de Casos com Repercussão Geral")
                
                # Contar ocorrências de cada tipo de repercussão geral
                repercussao_counts = df["Repercussão Geral"].value_counts().reset_index()
                repercussao_counts.columns = ["Repercussão Geral", "Quantidade"]
                
                # Criar gráfico de pizza
                fig = px.pie(
                    repercussao_counts, 
                    values="Quantidade", 
                    names="Repercussão Geral",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues_r
                )
                
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Gráfico de distribuição por Classe Processual
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Classes Processuais mais Frequentes")
            
            # Contar ocorrências de cada classe processual
            classe_counts = df["Classe Processo"].value_counts().reset_index()
            classe_counts.columns = ["Classe Processual", "Quantidade"]
            
            # Limitar para as 15 principais classes
            top_classes = classe_counts.head(15)
            
            # Criar gráfico de barras
            fig = px.bar(
                top_classes, 
                x="Classe Processual", 
                y="Quantidade",
                color="Quantidade",
                color_continuous_scale="Blues",
                title="Top 15 Classes Processuais"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Gráfico de distribuição por ano
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Distribuição de Informativos por Ano")
            
            # Extrair o ano da data de julgamento
            df["Ano"] = df["Data Julgamento"].dt.year
            
            # Contar ocorrências de cada ano
            ano_counts = df["Ano"].value_counts().sort_index().reset_index()
            ano_counts.columns = ["Ano", "Quantidade"]
            
            # Criar gráfico de linha
            fig = px.line(
                ano_counts, 
                x="Ano", 
                y="Quantidade",
                markers=True,
                line_shape="linear",
                title="Evolução Anual dos Informativos"
            )
            
            fig.update_layout(xaxis=dict(tickmode="linear", dtick=1))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Não há dados suficientes para gerar estatísticas.")
    
    # Aba 3: Assertivas para Estudo
    with tab3:
        st.markdown('<div class="sub-header">Assertivas para Estudo (Estilo Concurso)</div>', unsafe_allow_html=True)
        
        # Introdução
        st.markdown("""
        Esta seção apresenta assertivas de verdadeiro ou falso geradas por IA, no estilo de questões de concurso, 
        baseadas nos informativos do STF. Teste seus conhecimentos e gere novas questões dinamicamente.
        Se a API da OpenAI não estiver configurada, será usada uma simulação.
        """)
        
        # Filtro por Matéria
        st.markdown("**Filtre por Matéria(s):**")
        materias_disponiveis = sorted(df['Matéria'].dropna().unique())
        
        # Usar estado da sessão para manter a seleção de matérias
        if "materias_assertivas" not in st.session_state:
            st.session_state.materias_assertivas = ['Todas']
            
        materias_selecionadas = st.multiselect(
            "Selecione as matérias para as assertivas:",
            options=['Todas'] + materias_disponiveis,
            default=st.session_state.materias_assertivas,
            key="select_materias"
        )
        
        # Atualizar estado da sessão
        st.session_state.materias_assertivas = materias_selecionadas
        
        # Botão para gerar novas assertivas
        if st.button("Gerar Novas Assertivas"):
            # Limpar estado anterior das assertivas e respostas
            if "assertivas" in st.session_state:
                del st.session_state["assertivas"]
            if "respostas_usuario" in st.session_state:
                del st.session_state["respostas_usuario"]
            # A geração ocorrerá abaixo
        
        # Inicializar estado da sessão se necessário
        if "assertivas" not in st.session_state:
            with st.spinner("Gerando assertivas..."):
                st.session_state.assertivas = gerar_assertivas_api(df, st.session_state.materias_assertivas, num_assertivas=5)
        
        if "respostas_usuario" not in st.session_state:
            st.session_state.respostas_usuario = {}
        
        # Exibir assertivas
        if "assertivas" in st.session_state and st.session_state.assertivas:
            for i, assertiva in enumerate(st.session_state.assertivas):
                # Verificar se a assertiva tem resposta (algumas podem ser apenas informativas)
                if assertiva.get("resposta") is None:
                    st.markdown(f"""
                    <div class="assertiva-card">
                        <p>{assertiva.get('texto', 'Erro ao carregar assertiva.')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    continue
                
                # Determinar a classe CSS com base no estado da resposta
                classe_css = "assertiva-card"
                if i in st.session_state.respostas_usuario:
                    if st.session_state.respostas_usuario[i] == assertiva["resposta"]:
                        classe_css += " correct"
                    else:
                        classe_css += " incorrect"
                
                st.markdown(f"""
                <div class="{classe_css}">
                    <p><strong>Assertiva {i+1}:</strong> {assertiva['texto']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Opções de resposta (desabilitar se já respondido)
                resposta_dada = i in st.session_state.respostas_usuario
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    verdadeiro = st.button("Verdadeiro", key=f"v_{i}", disabled=resposta_dada)
                    if verdadeiro:
                        st.session_state.respostas_usuario[i] = True
                        st.rerun() # Recarregar para mostrar feedback
                
                with col2:
                    falso = st.button("Falso", key=f"f_{i}", disabled=resposta_dada)
                    if falso:
                        st.session_state.respostas_usuario[i] = False
                        st.rerun() # Recarregar para mostrar feedback
                
                # Mostrar feedback se o usuário já respondeu
                if resposta_dada:
                    resposta_correta = assertiva["resposta"]
                    resposta_usuario = st.session_state.respostas_usuario[i]
                    explicacao = assertiva.get("explicacao", "Explicação não disponível.")
                    
                    if resposta_usuario == resposta_correta:
                        st.markdown(f"""
                        <div class="feedback-correct">
                            ✓ Correto! {explicacao}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="feedback-incorrect">
                            ✗ Incorreto. A resposta correta é {"Verdadeiro" if resposta_correta else "Falso"}.
                            {explicacao}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("<hr>", unsafe_allow_html=True)
            
            # Mostrar pontuação
            if st.session_state.respostas_usuario:
                acertos = sum(1 for i, resposta in st.session_state.respostas_usuario.items() 
                             if i < len(st.session_state.assertivas) and st.session_state.assertivas[i].get("resposta") is not None and 
                             resposta == st.session_state.assertivas[i]["resposta"])
                total_respondidas = len(st.session_state.respostas_usuario)
                
                if total_respondidas > 0:
                    st.markdown(f"""
                    <div class="card">
                        <h3>Pontuação Atual</h3>
                        <p>Você acertou {acertos} de {total_respondidas} assertivas respondidas ({acertos/total_respondidas*100:.1f}%).</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
             st.warning("Clique em 'Gerar Novas Assertivas' para começar.")
    
    # Aba 4: Pergunte para a Result
    with tab4:
        st.markdown('<div class="sub-header">Pergunte para a Result</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Nesta seção, você pode fazer perguntas sobre os informativos do STF e receber respostas baseadas nos dados disponíveis.
        Se a API da OpenAI estiver configurada, a resposta será gerada por IA. Caso contrário, será usada uma simulação.
        
        **Exemplos de perguntas que você pode fazer:**
        - Quais são as principais teses sobre direito tributário julgadas em 2023?
        - Resumir os informativos sobre direito administrativo com repercussão geral reconhecida.
        - Explicar a tese do informativo sobre matéria constitucional.
        """)
        
        # Campo de entrada para a pergunta
        pergunta = st.text_input("Digite sua pergunta sobre os informativos do STF:", placeholder="Ex: Quais são as principais teses sobre direito tributário?")
        
        # Botão para enviar a pergunta
        if st.button("Enviar Pergunta"):
            if pergunta:
                with st.spinner("Analisando sua pergunta e buscando a melhor resposta..."):
                    # Obter resposta (usando API ou simulação)
                    resposta = obter_resposta_chatgpt(pergunta, df)
                    
                    # Exibir a resposta
                    st.markdown(f"""
                    <div class="question-card">
                        <strong>Sua pergunta:</strong> {pergunta}
                    </div>
                    <div class="answer-card">
                        <strong>Resposta:</strong><br>
                        {resposta}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Por favor, digite uma pergunta para continuar.")
    
    # Rodapé
    st.markdown('<div class="footer">Dashboard Informativos STF © 2025</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
