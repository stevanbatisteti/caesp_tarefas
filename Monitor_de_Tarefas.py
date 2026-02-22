import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time

# --- CONFIGURAÇÃO ---
MEU_TOPICO = "caesp_tarefas" 

def enviar_notificacao_ios(titulo, mensagem):
    """Envia push para o app ntfy no iOS/Android."""
    url = f"https://ntfy.sh/{MEU_TOPICO}"
    try:
        response = requests.post(
            url,
            data=mensagem.encode('utf-8'),
            headers={
                "Title": titulo,
                "Priority": "high",
                "Tags": "books,pencil"
            }
        )
        if response.status_code == 200:
            print("🚀 Notificação enviada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")

# --- CHROME EM MODO SERVIDOR (LINUX) ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# DATA AUTOMÁTICA (RESTAURADA)
hoje = datetime.today().strftime("%d/%m")
URL = "https://www.caesp.com.br/web/muraldetarefaspub.php?action=getMateriaisPub&perletivo=2026C&codtur=8%C2%BA%20Ano%20A/9"

try:
    print(f"🔍 Verificando tarefas para hoje ({hoje})...")
    driver.get(URL)
    time.sleep(5) 

    linhas = driver.find_elements(By.TAG_NAME, "tr")
    materias_em_casa = []

    for linha in linhas:
        colunas = linha.find_elements(By.TAG_NAME, "td")
        if len(colunas) >= 3:
            data_tabela = colunas[0].text.strip()
            materia = colunas[1].text.strip()
            descricao = colunas[2].text.strip().upper()

            if hoje in data_tabela and "EM CASA" in descricao:
                tarefa_limpa = descricao.replace("EM CASA", "").replace("=", "").replace("-", "").strip()
                materias_em_casa.append(f"🔹 {materia.upper()}: {tarefa_limpa.capitalize()}")

finally:
    driver.quit()

# --- ENVIO FINAL ---
if materias_em_casa:
    conteudo = "\n".join(materias_em_casa)
    enviar_notificacao_ios(f"📚 TAREFAS DE HOJE ({hoje})", conteudo)
else:
    # Esta linha avisa que o script rodou e não achou nada
    enviar_notificacao_ios(f"✅ TUDO LIMPO ({hoje})", "Nenhuma tarefa 'Em Casa' encontrada hoje. Aproveite!")
