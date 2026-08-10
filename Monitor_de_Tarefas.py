import requests
import sys
import time
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURAÇÃO ---
MEU_TOPICO = "caesp_tarefas"

def enviar_notificacao(titulo, mensagem):
    try:
        requests.post(
            f"https://ntfy.sh/{MEU_TOPICO}",
            data=mensagem.encode('utf-8'),
            headers={
                "Title": titulo.encode('utf-8'),
                "Priority": "high",
                "Tags": "books,pencil"
            }
        )
    except Exception:
        pass

# --- SCRAPER ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--log-level=3")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

fuso_brasilia = timezone(timedelta(hours=-3))
hoje = datetime.now(fuso_brasilia).strftime("%d/%m")
URL = "https://www.caesp.com.br/web/muraldetarefaspub.php?action=getMateriaisPub&perletivo=2026C&codtur=8%C2%BA%20Ano%20B/9"

try:
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

                # Modificação feita aqui para aceitar "EM CASA" ou "TAREFA"
                if "EM CASA" in descricao or "TAREFA" in descricao:
                    tarefa = (
                        descricao.replace("EM CASA", "")
                                 .replace("TAREFA", "")
                                 .replace("=", "")
                                 .replace("-", "")
                                 .strip()
                    )
                    materias_em_casa.append(f"{materia}: {tarefa.capitalize()}")
finally:
    driver.quit()

# --- ENVIO ---
if materias_em_casa:
    enviar_notificacao(
        f"📚 TAREFAS DE HOJE ({hoje})",
        "\n".join([f"🔹 {item}" for item in materias_em_casa])
    )
else:
    enviar_notificacao(f"✅ TUDO LIMPO ({hoje})", "Sem tarefas hoje.")
