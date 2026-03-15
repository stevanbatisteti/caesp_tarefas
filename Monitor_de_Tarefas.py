import requests
import sys
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- NOVOS IMPORTS PARA GOOGLE TASKS ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Força o sistema a usar UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURAÇÃO ---
MEU_TOPICO = "caesp_tarefas" 
SCOPES = ['https://www.googleapis.com/auth/tasks']

def obter_servico_tasks():
    """Gerencia a autenticação e reconstrói os arquivos JSON a partir das Secrets do GitHub."""
    creds = None
    
    # Reconstrói os arquivos se estiver rodando no GitHub Actions
    if 'GOOGLE_TOKEN_JSON' in os.environ:
        with open('token.json', 'w') as f:
            f.write(os.environ['GOOGLE_TOKEN_JSON'])
    
    if 'GOOGLE_CREDENTIALS_JSON' in os.environ:
        with open('credentials.json', 'w') as f:
            f.write(os.environ['GOOGLE_CREDENTIALS_JSON'])

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('tasks', 'v1', credentials=creds)

def enviar_notificacao(titulo, mensagem):
    url = f"https://ntfy.sh/{MEU_TOPICO}"
    try:
        response = requests.post(
            url, 
            data=mensagem.encode('utf-8'), 
            headers={
                "Title": titulo.encode('utf-8'), 
                "Priority": "high", 
                "Tags": "books,pencil"
            }
        )
        if response.status_code == 200:
            print(f"🚀 Notificação enviada para o tópico: {MEU_TOPICO}")
    except Exception as e:
        print(f"❌ Falha ao enviar notificação: {e}")

# --- SCRAPER ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3") 

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

hoje = datetime.today().strftime("%d/%m")
URL = "https://www.caesp.com.br/web/muraldetarefaspub.php?action=getMateriaisPub&perletivo=2026C&codtur=8%C2%BA%20Ano%20A/9"

try:
    print(f"🔍 Buscando no portal CAESP: {hoje}")
    driver.get(URL)
    time.sleep(5) 
    
    linhas = driver.find_elements(By.TAG_NAME, "tr")
    materias_em_casa = []

    for linha in linhas:
        colunas = linha.find_elements(By.TAG_NAME, "td")
        if len(colunas) >= 3:
            data_tabela = colunas[0].text.strip()
            if hoje in data_tabela:
                materia = colunas[1].text.strip().upper()
                descricao = colunas[2].text.strip().upper()
                
                if "EM CASA" in descricao:
                    tarefa = descricao.replace("EM CASA", "").replace("=", "").replace("-", "").strip()
                    materias_em_casa.append(f"{materia}: {tarefa.capitalize()}")

finally:
    driver.quit()

# --- LÓGICA DE ENVIO E GOOGLE TASKS ---
if materias_em_casa:
    # 1. Enviar Notificação
    titulo_alerta = f"📚 TAREFAS DE HOJE ({hoje})"
    corpo_alerta = "\n".join([f"🔹 {item}" for item in materias_em_casa])
    print("✅ Tarefas encontradas! Disparando push...")
    enviar_notificacao(titulo_alerta, corpo_alerta)
    
    # 2. Adicionar ao Google Tasks
    try:
        service = obter_servico_tasks()
        for item in materias_em_casa:
            task_body = {
                'title': item,
                'notes': f'Importado do portal CAESP em {hoje}'
            }
            service.tasks().insert(tasklist='@default', body=task_body).execute()
            print(f"📌 Adicionado ao Google Tasks: {item}")
    except Exception as e:
        print(f"❌ Erro ao adicionar no Google Tasks: {e}")
        
else:
    print("✅ Nenhuma tarefa para hoje.")
    enviar_notificacao(f"✅ TUDO LIMPO ({hoje})", "Sem tarefas hoje.")
