import requests
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

# Força o sistema a usar UTF-8 para evitar erros com emojis e acentos
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURAÇÃO ---
# Nome do tópico que você assinou no app ntfy do iPhone
MEU_TOPICO = "caesp_tarefas" 

def enviar_notificacao(titulo, mensagem):
    """Envia a notificação via ntfy.sh tratando corretamente o texto em UTF-8."""
    url = f"https://ntfy.sh/{MEU_TOPICO}"
    try:
        # Enviamos os dados encodados em UTF-8 para evitar erros de latin-1
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

# --- CONFIGURAÇÃO DO CHROME (MODO SERVIDOR) ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Remove logs desnecessários no terminal do GitHub
chrome_options.add_argument("--log-level=3") 

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

hoje = datetime.today().strftime("%d/%m")
URL = "https://www.caesp.com.br/web/muraldetarefaspub.php?action=getMateriaisPub&perletivo=2026C&codtur=8%C2%BA%20Ano%20A/9"

try:
    print(f"🔍 Iniciando busca no portal CAESP para a data: {hoje}")
    driver.get(URL)
    time.sleep(5) # Tempo para carregamento da tabela via JS
    
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
                    # Limpeza do texto da tarefa
                    tarefa = descricao.replace("EM CASA", "").replace("=", "").replace("-", "").strip()
                    materias_em_casa.append(f"🔹 {materia}: {tarefa.capitalize()}")

finally:
    driver.quit()

# --- LÓGICA DE ENVIO ---
if materias_em_casa:
    titulo_alerta = f"📚 TAREFAS DE HOJE ({hoje})"
    corpo_alerta = "\n".join(materias_em_casa)
    print("✅ Tarefas encontradas! Disparando push...")
    enviar_notificacao(titulo_alerta, corpo_alerta)
else:
    print("✅ Nenhuma tarefa para hoje. Enviando confirmação de execução.")
    # Texto alterado conforme sua solicitação
    enviar_notificacao(f"✅ TUDO LIMPO ({hoje})", "Sem tarefas hoje.")

