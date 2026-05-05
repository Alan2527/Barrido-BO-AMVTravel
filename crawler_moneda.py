import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def correr_crawler_moneda():
    # Variables de entorno (Configuradas en GitHub Secrets)
    USER = os.getenv("BO_USER", "Pablo@amv.travel") # El segundo valor es un fallback por si lo corres local
    PASSWORD = os.getenv("BO_PASS", "amvtest")

    # Configuración fundamental para GitHub Actions (Modo Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080") # Tamaño virtual para evitar problemas responsive
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    print("Iniciando sesión en el BO (Modo Headless)...")
    driver.get("https://qa.bo.amv.travel/login")
    
    try:
        wait.until(EC.presence_of_element_located((By.NAME, "txtUser"))).send_keys(USER)
        driver.find_element(By.NAME, "txtPassword").send_keys(PASSWORD)
        driver.find_element(By.NAME, "btnLogin").click()
        wait.until(EC.presence_of_element_located((By.ID, "ctl00_lnkSignOut")))
        print("✅ Login exitoso.")
    except Exception as e:
        print(f"❌ Error al intentar loguearse: {e}")
        driver.quit()
        exit(1) # Forzamos que GitHub Action falle si no hay login

    print("Recolectando URLs a escanear desde el menú...")
    urls_a_visitar = set()
    
    try:
        links_menu = driver.find_elements(By.XPATH, "//nav[@role='navigation']//a[@href]") 
        for link in links_menu:
            url = link.get_attribute("href")
            if url and "bo.amv.travel" in url and "ctl00_lnkSignOut" not in url:
                if not url.endswith("#"):
                    urls_a_visitar.add(url)
        print(f"🔍 Se encontraron {len(urls_a_visitar)} pantallas únicas.")
    except Exception as e:
        print(f"❌ Error al leer el menú: {e}")
        driver.quit()
        exit(1)

    fallas_encontradas = []
    
    print("\nIniciando barrido de pantallas...")
    for i, url in enumerate(urls_a_visitar, 1):
        print(f"[{i}/{len(urls_a_visitar)}] Analizando: {url}")
        try:
            driver.get(url)
            time.sleep(3) 
            texto_body = driver.find_element(By.TAG_NAME, "body").text.upper()
            if re.search(r'\bARS\b', texto_body):
                fallas_encontradas.append(url)
                print(f"   [!] ALERTA: Se encontró 'ARS' visible.")
        except Exception as e:
            print(f"   [x] Error al leer la pantalla: {e}")

    print("\n==================================================")
    print("                REPORTE DE EJECUCIÓN              ")
    print("==================================================")
    if not fallas_encontradas:
        print("✅ ÉXITO TOTAL: No se encontraron referencias a 'ARS'.")
        driver.quit()
        exit(0) # Exito
    else:
        print(f"❌ BUG: Se encontró 'ARS' en {len(fallas_encontradas)} pantallas:")
        for url_falla in fallas_encontradas:
            print(f"  - {url_falla}")
        driver.quit()
        exit(1) # Le avisa a GitHub que el Job falló para que quede en rojo

if __name__ == "__main__":
    correr_crawler_moneda()
