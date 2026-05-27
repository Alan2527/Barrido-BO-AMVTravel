import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def correr_crawler_profundo():
    # Variables de entorno (Configuradas en GitHub Secrets para mayor seguridad)
    USER = os.getenv("BO_USER", "Pablo@amv.travel")
    PASSWORD = os.getenv("BO_PASS", "amvtest")
    PALABRA_A_BUSCAR = r'\bARS\b'
    MAX_PAGINAS = 1000

    # Configuración fundamental para GitHub Actions (Modo Headless)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)
    
    # ==========================================
    # 1. LOGUEO
    # ==========================================
    print("Iniciando sesión en el BO (Modo Headless)...")
    driver.get("https://preprod.bo.amv.travel/login")
    try:
        wait.until(EC.presence_of_element_located((By.NAME, "txtUser"))).send_keys(USER)
        driver.find_element(By.NAME, "txtPassword").send_keys(PASSWORD)
        driver.find_element(By.NAME, "btnLogin").click()
        wait.until(EC.presence_of_element_located((By.ID, "ctl00_lnkSignOut")))
        print("✅ Login exitoso.")
    except Exception as e:
        print(f"❌ Error en login: {e}")
        driver.quit()
        exit(1)

    # ==========================================
    # 2. INICIALIZAR LA COLA DE NAVEGACIÓN
    # ==========================================
    urls_pendientes = set()
    urls_visitadas = set()
    fallas_encontradas = []

    # Arrancamos capturando el menú inicial
    links_menu = driver.find_elements(By.XPATH, "//nav[@role='navigation']//a[@href]") 
    for link in links_menu:
        url = link.get_attribute("href")
        if url and "bo.amv.travel" in url and "ctl00_lnkSignOut" not in url and not url.endswith("#"):
            urls_pendientes.add(url)

    # ==========================================
    # 3. ESCANEO PROFUNDO (CRAWLING DINÁMICO)
    # ==========================================
    print("\nIniciando barrido profundo buscando 'ARS'...")
    
    while urls_pendientes and len(urls_visitadas) < MAX_PAGINAS:
        url_actual = urls_pendientes.pop()
        
        if url_actual in urls_visitadas:
            continue
            
        urls_visitadas.add(url_actual)
        print(f"[{len(urls_visitadas)}] Analizando: {url_actual}")
        
        try:
            driver.get(url_actual)
            time.sleep(3) # Espera AJAX
            
            # A. BUSCAR LA PALABRA EN LA PANTALLA ACTUAL
            texto_body = driver.find_element(By.TAG_NAME, "body").text.upper()
            if re.search(PALABRA_A_BUSCAR, texto_body):
                fallas_encontradas.append(url_actual)
                print(f"   [!] ALERTA: Se encontró 'ARS' en esta pantalla.")
            
            # B. RECOLECTAR NUEVOS LINKS DENTRO DE ESTA PANTALLA
            nuevos_links = driver.find_elements(By.XPATH, "//a[@href]")
            for link in nuevos_links:
                nueva_url = link.get_attribute("href")
                
                if (nueva_url and 
                    "bo.amv.travel" in nueva_url and 
                    "ctl00_lnkSignOut" not in nueva_url and 
                    not nueva_url.endswith("#") and 
                    "javascript:" not in nueva_url):
                    
                    if nueva_url not in urls_visitadas:
                        urls_pendientes.add(nueva_url)
                        
        except Exception as e:
            print(f"   [x] Error al leer la pantalla: {e}")

    # ==========================================
    # 4. REPORTE FINAL
    # ==========================================
    print("\n==================================================")
    print("                REPORTE DE EJECUCIÓN              ")
    print(f"           Páginas escaneadas: {len(urls_visitadas)}")
    print("==================================================")
    
    if not fallas_encontradas:
        print("✅ ÉXITO TOTAL: Sistema limpio de 'ARS'.")
        driver.quit()
        exit(0)
    else:
        print(f"❌ BUG: 'ARS' encontrado en {len(fallas_encontradas)} pantallas:")
        for url_falla in set(fallas_encontradas): 
            print(f"  - {url_falla}")
        driver.quit()
        exit(1)

if __name__ == "__main__":
    correr_crawler_profundo()
