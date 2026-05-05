import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def mapear_pantallas_buscar():
    USER = os.getenv("BO_USER", "Pablo@amv.travel")
    PASSWORD = os.getenv("BO_PASS", "amvtest")
    MAX_PAGINAS = 150 

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
    driver.get("https://qa.bo.amv.travel/login")
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
    pantallas_con_buscar = []

    print("Recolectando URLs del menú inicial...")
    links_menu = driver.find_elements(By.XPATH, "//nav[@role='navigation']//a[@href]") 
    for link in links_menu:
        url = link.get_attribute("href")
        if url and "bo.amv.travel" in url and "ctl00_lnkSignOut" not in url and not url.endswith("#"):
            urls_pendientes.add(url)

    # ==========================================
    # 3. ESCANEO PROFUNDO (BUSCANDO BOTONES ASP.NET)
    # ==========================================
    print("\nIniciando barrido profundo buscando botones 'Buscar'...")
    
    while urls_pendientes and len(urls_visitadas) < MAX_PAGINAS:
        url_actual = urls_pendientes.pop()
        
        if url_actual in urls_visitadas:
            continue
            
        urls_visitadas.add(url_actual)
        print(f"[{len(urls_visitadas)}] Analizando: {url_actual}")
        
        try:
            driver.get(url_actual)
            time.sleep(3) 
            
            tiene_buscar = False
            
            # A. VALIDAR SI EXISTE EL BOTÓN "BUSCAR" (Estrategia combinada)
            
            # 1. Buscar en etiquetas <a> (Como el de la captura ASP.NET)
            enlaces = driver.find_elements(By.TAG_NAME, "a")
            for enlace in enlaces:
                texto_enlace = enlace.text.upper()
                id_enlace = enlace.get_attribute("id") or ""
                # Si dice BUSCAR adentro del <span> o si el ID es el del filtro
                if "BUSCAR" in texto_enlace or "btnFilter" in id_enlace:
                    tiene_buscar = True
                    break
            
            # 2. Respaldo: Buscar en etiquetas <button> estándar
            if not tiene_buscar:
                botones = driver.find_elements(By.TAG_NAME, "button")
                for btn in botones:
                    if "BUSCAR" in btn.text.upper():
                        tiene_buscar = True
                        break
            
            # 3. Respaldo: Buscar en <input>
            if not tiene_buscar:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    tipo = inp.get_attribute("type")
                    valor = inp.get_attribute("value") or ""
                    if tipo in ["submit", "button"] and "BUSCAR" in valor.upper():
                        tiene_buscar = True
                        break
            
            # Si detectó el botón en cualquiera de sus formas, anota la URL
            if tiene_buscar:
                pantallas_con_buscar.append(url_actual)
                print(f"   [!] ATENCIÓN: Botón 'Buscar' detectado en esta pantalla.")
            
            # B. RECOLECTAR NUEVOS LINKS PARA SEGUIR NAVEGANDO
            nuevos_links = driver.find_elements(By.XPATH, "//a[@href]")
            for link in nuevos_links:
                nueva_url = link.get_attribute("href")
                
                # Omitimos navegar por los enlaces javascript como el __doPostBack del botón
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
    print("         MAPEO DE PANTALLAS CON BOTÓN BUSCAR      ")
    print(f"           Páginas escaneadas en total: {len(urls_visitadas)}")
    print("==================================================")
    
    if not pantallas_con_buscar:
        print("✅ No se encontraron botones 'Buscar' en las pantallas escaneadas.")
    else:
        urls_unicas = set(pantallas_con_buscar)
        print(f"⚠️ Se detectaron {len(urls_unicas)} pantallas que requieren accionar un botón 'Buscar':")
        for url_falla in urls_unicas: 
            print(f"  - {url_falla}")
            
    driver.quit()

if __name__ == "__main__":
    mapear_pantallas_buscar()
