import subprocess
import sys
import time
import threading

def run_command(cmd, step_description, log_file=None):
    if log_file:
        print(f"\n[{step_description}] Inizio... (Output su {log_file})")
        with open(log_file, "a") as f:
            f.write(f"\n{'='*50}\n[{step_description}] Comando:\n{cmd}\n{'='*50}\n")
            p = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=f, stderr=subprocess.STDOUT)
            p.wait()
    else:
        print(f"\n[{step_description}] Inizio...")
        p = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
        p.wait()
        
    if p.returncode != 0:
        print(f"\n[ERRORE] Fallimento in [{step_description}] (exit code {p.returncode}):\n{cmd}\n")
        return False
    print(f"[{step_description}] Completato con successo.\n")
    return True

def branch_normattiva(results):
    """Gestisce il ramo A: Download e Preprocessing per Normattiva"""
    log = "normattiva.log"
    # Fase 1
    if not run_command("cd step1_download_laws && source venv/bin/activate && python3 -u export_laws_2.py", "Normattiva - Download (Fase 1)", log):
        results['normattiva'] = False
        return
    # Fase 2 (Inizia immediatamente non appena finisce la Fase 1)
    if not run_command("cd step2_preprocessing && python3 -u preprocess_rag.py", "Normattiva - Preprocessing (Fase 2)", log):
        results['normattiva'] = False
        return
    
    results['normattiva'] = True

def branch_agenzia(results):
    """Gestisce il ramo B: Scraping e Preprocessing per l'Agenzia delle Entrate"""
    log = "agenzia.log"
    # Fase 1
    if not run_command("cd step1_download_laws && source venv/bin/activate && python3 -u scraping_data.py", "Agenzia Entrate - Scraping (Fase 1)", log):
        results['agenzia'] = False
        return
    # Fase 2 (Inizia immediatamente non appena finisce la Fase 1)
    if not run_command("cd step2_preprocessing && source venv/bin/activate && python3 -u preprocess_agenzia.py", "Agenzia Entrate - Preprocessing (Fase 2)", log):
        results['agenzia'] = False
        return
    
    results['agenzia'] = True

def main():
    # Reset dei file di log ad ogni avvio
    for log_file in ["normattiva.log", "agenzia.log", "ingestion.log"]:
        with open(log_file, "w") as f:
            f.write("")

    print("Avvio della pipeline OTTIMIZZATA di orchestrazione RAG...")
    print("I flussi di Normattiva e Agenzia delle Entrate viaggeranno in parallelo e in totale autonomia.")
    start_time = time.time()
    
    # Dizionario condiviso per raccogliere lo stato di successo dei due rami (Thread)
    results = {'normattiva': False, 'agenzia': False}
    
    # Creazione dei Thread per i due rami paralleli
    t_normattiva = threading.Thread(target=branch_normattiva, args=(results,))
    t_agenzia = threading.Thread(target=branch_agenzia, args=(results,))
    
    print(f"\n{'='*50}\nInizio elaborazioni asincrone (Fasi 1 e 2)\n{'='*50}")
    # Avvio dei Thread
    t_normattiva.start()
    t_agenzia.start()
    
    # Il programma principale (main) attende che entrambi i rami (Thread) abbiano concluso le loro Fasi 1 e 2
    t_normattiva.join()
    t_agenzia.join()
    
    # Controllo che nessuno dei due rami abbia subito errori letali durante il percorso
    if not (results['normattiva'] and results['agenzia']):
        print("\n[ERRORE CRITICO] Uno o entrambi i rami di acquisizione/preparazione hanno fallito.")
        print("Impossibile procedere all'indicizzazione. Pipeline interrotta.")
        sys.exit(1)
        
    print(f"\n{'='*50}\nFasi 1 e 2 completate per tutti i rami. Avvio Fase 3...\n{'='*50}")
    
    # ---------------------------------------------------------
    # STEP 3: Ingestion (Sequenziale, attende tutti)
    # ---------------------------------------------------------
    step3_command = "cd step3_ingestion && source venv/bin/activate && python3 -u ingest_rag.py"
    if not run_command(step3_command, "Ingestion Database Vettoriale ChromaDB (Fase 3)", "ingestion.log"):
        print("\nInterruzione pipeline a causa di un errore nello Step 3.")
        sys.exit(1)
        
    elapsed_time = time.time() - start_time
    print(f"\n{'='*50}\nPIPELINE COMPLETATA CON SUCCESSO!\nTempo totale: {elapsed_time:.2f} secondi.\n{'='*50}")

if __name__ == "__main__":
    main()
