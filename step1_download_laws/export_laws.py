import json
import os
import time
import requests
import io
import zipfile

# =========================
# PARAMETER CONFIGURATION
# =========================
EFFECTIVE_DATE = "2026-03-01"
START_DATE_OF_ENACTMENT = "1972-01-01"

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

def download_laws():
    output_dir = 'laws_collection'
    os.makedirs(output_dir, exist_ok=True)
    
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
    
    # --- PHASE 1: Downloading the list of the last 100 laws ---
    print("Downloading the list of the last 100 laws in progress...")
    search_url = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca/avanzata'
    list_payload = {
        "denominazioneAtto": "LEGGE",
        "orderType": "recente",
        "vigenza": "2026-03-01",
        "paginazione": {
            "paginaCorrente": 1,
            "numeroElementiPerPagina": 100
        }
    }
    
    try:
        list_res = session.post(search_url, headers=headers_post, json=list_payload)
        list_res.raise_for_status()
        data = list_res.json()
        
        # Backup save of the list in the output folder
        json_path = os.path.join(output_dir, 'list_100_recent_laws.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Error during list download: {e}")
        return
        
    laws = data.get('listaAtti', [])
    print(f"Found {len(laws)} laws to process.")
    
    month_translation = {
        'gennaio': 'january', 'febbraio': 'february', 'marzo': 'march',
        'aprile': 'april', 'maggio': 'may', 'giugno': 'june',
        'luglio': 'july', 'agosto': 'august', 'settembre': 'september',
        'ottobre': 'october', 'novembre': 'november', 'dicembre': 'december'
    }
    
    # --- PHASE 2: Asynchronous extraction and JSON saving ---
    for index, law in enumerate(laws):
        try:
            # Parameter extraction
            enactment_date = law.get('dataEmanazione', '')
            if enactment_date:
                enactment_date = enactment_date.split('T')[0] # Take only YYYY-MM-DD
            
            number = law.get('numeroProvvedimento', '')
            year = law.get('annoProvvedimento', '')
            title = law.get('descrizioneAtto', f'LAW_{year}_{number}')
            
            # Handling of the new file name (e.g. law_27_february_2026_n_27)
            month_ita = law.get('meseProvvedimentoIta', '')
            day = law.get('giornoProvvedimento', '')
            
            if not day or not month_ita or not enactment_date or not number:
                print(f"[{index+1}/{len(laws)}] Skipping file (missing parameters for name): {title}")
                continue
            
            month_eng = month_translation.get(month_ita.lower(), month_ita.lower())
            
            # Safe string construction for filename (replace spaces with underscore, make lowercase)
            base_name = f"law_{day}_{month_eng}_{year}_n_{number}".lower()
            # Clean possible double underscores or strange characters if present in API data
            base_name = base_name.replace(' ', '_').replace('__', '_')
                
            json_name = f"{output_dir}/{base_name}.json"
            if os.path.exists(json_name):
                print(f"[{index+1}/{len(laws)}] Already downloaded: {json_name}")
                continue
            
            print(f"\n[{index+1}/{len(laws)}] Processing: {title}")
            
            # Step 1: New asynchronous search
            new_url = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/nuova-ricerca'
            search_payload = {
                "formato": "JSON",
                "tipoRicerca": "A",
                "modalita": "C",
                "parametriRicerca": {
                    "denominazioneAtto": "LEGGE",
                    "orderType": "recente",
                    "vigenza": "2026-03-01",
                    "paginazione": {
                        "paginaCorrente": 1,
                        "numeroElementiPerPagina": 1
                    },
                    "dataInizioEmanazione": enactment_date,
                    "dataFineEmanazione": enactment_date,
                    "numeroProvvedimento": str(number)
                }
            }
            
            new_res = session.post(new_url, headers=headers_post, json=search_payload)
            new_res.raise_for_status()
            
            token = new_res.text.strip('"').strip()
            print(f"  Token obtained: {token}")
            
            # Step 2: Confirm search
            confirm_url = 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/conferma-ricerca'
            confirm_res = session.put(confirm_url, headers=headers_post, json={"token": token})
            confirm_res.raise_for_status()
            print("  Search confirmed.")
            
            # Step 3: Check status
            status_url = f'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/check-status/{token}'
            ready = False
            attempts = 0
            
            # Courtesy wait before first check
            time.sleep(6)
            
            while not ready and attempts < 20:
                # Normattiva returns 303 See Other when ready and redirects to download
                status_res = session.get(status_url, headers=headers_get, allow_redirects=False)
                
                if status_res.status_code == 303:
                    ready = True
                    print("  File ready for download.")
                elif status_res.status_code == 200:
                    status_json = status_res.json()
                    if status_json.get('stato') == 3:
                        ready = True
                        print("  File ready for download.")
                    else:
                        print(f"  Processing... status={status_json.get('stato')} (wait 6s)")
                        time.sleep(6)
                        attempts += 1
                elif status_res.status_code == 409:
                    print(f"  System busy (409): {status_res.text}. Retrying in 6s...")
                    time.sleep(6)
                    attempts += 1
                else:
                    print(f"  Unexpected status: {status_res.status_code} - {status_res.text}")
                    break
            
            if not ready:
                print(f"  Error: Timeout or failed status for token {token}")
                continue
                
            # Step 4: Download ZIP and JSON in-memory Extraction
            download_url = f'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/collections/download/collection-asincrona/{token}'
            print("  Downloading ZIP into memory...")
            
            download_res = session.get(download_url, headers=headers_get, stream=True)
            download_res.raise_for_status()
            
            # Read zip in RAM memory instead of disk
            zip_in_memory = io.BytesIO()
            for chunk in download_res.iter_content(chunk_size=8192):
                zip_in_memory.write(chunk)
                
            try:
                with zipfile.ZipFile(zip_in_memory) as z:
                    # Normattiva's zip contains a JSON file (usually only one and with .json extension)
                    json_files = [f for f in z.namelist() if f.endswith('.json')]
                    if json_files:
                        # Take the first json found
                        internal_filename = json_files[0]
                        with z.open(internal_filename) as internal_f:
                            json_content = json.load(internal_f)
                            
                        # Save formatted JSON content with new name
                        with open(json_name, 'w', encoding='utf-8') as out_f:
                            json.dump(json_content, out_f, ensure_ascii=False, indent=2)
                        print(f"  Saved successfully as {json_name}")
                    else:
                        print(f"  No JSON found in ZIP for token {token}")
            except zipfile.BadZipFile:
                print("  Error: The downloaded file is not a valid ZIP.")
                
            # Courtesy pause to avoid bombarding API
            time.sleep(1)
            
        except requests.exceptions.HTTPError as http_err:
            print(f"  HTTP Error: {http_err}")
        except Exception as err:
            print(f"  Error during processing: {err}")

if __name__ == '__main__':
    download_laws()
