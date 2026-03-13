import json
import os
import time
import requests
import io
import zipfile
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# PARAMETER CONFIGURATION
# =========================
EFFECTIVE_DATE = "2026-03-01"
START_DATE_OF_ENACTMENT = "1972-01-01"
#MAX_DOCS_PER_TYPE = None # Set to None to download ALL documents via pagination
MAX_DOCS_PER_TYPE = None # Set to None to download ALL documents via pagination

ACT_TYPES = [
    "COSTITUZIONE",
    "LEGGE",
    "LEGGE COSTITUZIONALE",
    "DECRETO-LEGGE",
    "DECRETO LEGISLATIVO",
    "DECRETO DEL PRESIDENTE DELLA REPUBBLICA",
    "DECRETO DEL PRESIDENTE DEL CONSIGLIO DEI MINISTRI",
    "DECRETO MINISTERIALE",
    "DECRETO",
    "DECRETO DEL CAPO DEL GOVERNO",
    "DECRETO DEL CAPO DEL GOVERNO, PRIMO MINISTRO SEGRETARIO DI STATO",
    "DECRETO DEL CAPO PROVVISORIO DELLO STATO",
    "DECRETO LEGISLATIVO DEL CAPO PROVVISORIO DELLO STATO",
    "DECRETO DEL DUCE",
    "DECRETO DEL DUCE DEL FASCISMO, CAPO DEL GOVERNO",
    "DECRETO-LEGGE LUOGOTENENZIALE",
    "DECRETO LEGISLATIVO LUOGOTENENZIALE",
    "DECRETO LEGISLATIVO PRESIDENZIALE",
    "DECRETO LUOGOTENENZIALE",
    "DECRETO PRESIDENZIALE",
    "DECRETO REALE",
    "DELIBERAZIONE",
    "DETERMINAZIONE DEL COMMISSARIO PER LE FINANZE",
    "DETERMINAZIONE DEL COMMISSARIO PER LA PRODUZIONE BELLICA",
    "DETERMINAZIONE INTERCOMMISSARIALE",
    "ORDINANZA",
    "REGIO DECRETO",
    "REGIO DECRETO-LEGGE",
    "REGIO DECRETO LEGISLATIVO",
    "REGOLAMENTO"
]

def download_documents():
    base_output_dir = 'documents_collection'
    os.makedirs(base_output_dir, exist_ok=True)
   
    headers_post = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0'
    }
   
    headers_get = {
        'Accept': 'application/json, text/plain, */*',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0'
    }
   
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[409, 429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    for act_type in ACT_TYPES:
        output_dir = os.path.join(base_output_dir, act_type.replace(' ', '_').lower())
        os.makedirs(output_dir, exist_ok=True)
        print(f"\n--- Processing acts: {act_type} ---")
       
        search_url = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca/avanzata'
        
        acts = []
        current_page = 1
        elements_per_page = 50 
        
        while True:
            remaining = None
            if MAX_DOCS_PER_TYPE is not None:
                remaining = MAX_DOCS_PER_TYPE - len(acts)
                if remaining <= 0:
                    break
            
            fetch_size = elements_per_page if remaining is None else min(elements_per_page, remaining)
            print(f"  Downloading list of acts for {act_type} (Page {current_page}, fetching up to {fetch_size})...")
            
            list_payload = {
                "denominazioneAtto": act_type,
                "orderType": "recente",
                "vigenza": EFFECTIVE_DATE,
                "dataInizioEmanazione": START_DATE_OF_ENACTMENT,
                "paginazione": {
                    "paginaCorrente": current_page,
                    "numeroElementiPerPagina": fetch_size
                }
            }
           
            try:
                list_res = session.post(search_url, headers=headers_post, json=list_payload)
                list_res.raise_for_status()
                data = list_res.json()
                page_acts = data.get('listaAtti', [])
                
                if not page_acts:
                    break # No more results
                    
                acts.extend(page_acts)
                
                # If the server returned fewer results than requested, we've reached the end
                if len(page_acts) < fetch_size:
                    break
                    
                current_page += 1
                time.sleep(1) # Courtesy pause between list requests
                
            except Exception as e:
                print(f"Error fetching page {current_page}: {e}")
                break
       
        print(f"Found {len(acts)} total documents of type {act_type} to process.")
       
        for index, act in enumerate(acts):
            try:
                enactment_date = act.get('dataEmanazione', '').split('T')[0] if act.get('dataEmanazione') else ''
                number = act.get('numeroProvvedimento', '')
                year = act.get('annoProvvedimento', '')
                title = act.get('descrizioneAtto', f'{act_type}_{year}_{number}')
                month_ita = act.get('meseProvvedimentoIta', '')
                day = act.get('giornoProvvedimento', '')
               
                if not day or not month_ita or not enactment_date or not number:
                    continue
                
                base_name = f"{act_type.lower()}_{day}_{month_ita.lower()}_{year}_n_{number}".replace(' ', '_').replace('__', '_')
                json_name = os.path.join(output_dir, f"{base_name}.json")
               
                if os.path.exists(json_name):
                    continue
               
                print(f"[{index+1}/{len(acts)}] Processing: {title}")
               
                new_url = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/nuova-ricerca'
                search_payload = {
                    "formato": "JSON",
                    "tipoRicerca": "A",
                    "modalita": "C",
                    "parametriRicerca": {
                        "denominazioneAtto": act_type,
                        "orderType": "recente",
                        "vigenza": EFFECTIVE_DATE,
                        "paginazione": {"paginaCorrente": 1, "numeroElementiPerPagina": 1},
                        "dataInizioEmanazione": enactment_date,
                        "dataFineEmanazione": enactment_date,
                        "numeroProvvedimento": str(number)
                    }
                }
               
                new_res = session.post(new_url, headers=headers_post, json=search_payload)
                new_res.raise_for_status()
                token = new_res.text.strip('"').strip()
               
                confirm_url = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/conferma-ricerca'
                session.put(confirm_url, headers=headers_post, json={"token": token})
               
                status_url = f'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/check-status/{token}'
                ready = False
                attempts = 0
                time.sleep(5)
               
                while not ready and attempts < 30:
                    status_res = session.get(status_url, headers=headers_get, allow_redirects=False)
                    if status_res.status_code == 303 or (status_res.status_code == 200 and status_res.json().get('stato') == 3):
                        ready = True
                    else:
                        time.sleep(4)
                        attempts += 1
               
                if not ready:
                    continue
               
                download_url = f'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/collections/download/collection-asincrona/{token}'
                download_res = session.get(download_url, headers=headers_get, stream=True)
                download_res.raise_for_status()
               
                zip_in_memory = io.BytesIO()
                for chunk in download_res.iter_content(chunk_size=8192):
                    zip_in_memory.write(chunk)
                   
                with zipfile.ZipFile(zip_in_memory) as z:
                    json_files = [f for f in z.namelist() if f.endswith('.json')]
                    if json_files:
                        with z.open(json_files[0]) as internal_f:
                            json_content = json.load(internal_f)
                        with open(json_name, 'w', encoding='utf-8') as out_f:
                            json.dump(json_content, out_f, ensure_ascii=False, indent=2)
               
                time.sleep(1)
               
            except Exception as e:
                print(f"Error processing {title}: {e}")
                err_str = str(e).lower()
                # If we get a connection block or 409/429, wait longer to avoid hammering
                if "connection aborted" in err_str or "connection reset" in err_str or "409 Client Error" in err_str or "429 Client Error" in err_str:
                    print("Detected possible rate limit or block. Waiting for 30 seconds before retrying...")
                    time.sleep(30)
                else:
                    time.sleep(5)

if __name__ == '__main__':
    download_documents()
