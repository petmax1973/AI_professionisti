# API Normattiva Open Data - Documentazione Completa

Questa documentazione riassume tutte le API Open Data esposte da Normattiva, comprensive del comando `curl` di esempio e dei parametri ammessi con i relativi valori consentiti.

Tutte le API hanno come indirizzo base uno dei seguenti (in base all'ambiente target):
* Ambente di Esercizio: `https://api.normattiva.it/t/normattiva.api`
* Ambiente di Test (PRE): `https://pre.api.normattiva.it/t/normattiva.api`

---

## 1. Tipologiche: Estensioni (formati di esportazione)
Recupera l'elenco delle tipologie di formati di esportazione previsti.

**Parametri:**
*Nessun parametro richiesto.*

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/tipologiche/estensioni' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' | jq
```

**Esempio di Risposta (JSON):**
```json
[
  {
    "label": "AKN",
    "value": "Esporta AKN"
  },
  {
    "label": "XML",
    "value": "Esporta XML"
  },
  "... (altri formati come PDF, EPUB, RTF, JSON, HTML)"
]
```

---

## 2. Collezioni predefinite
Recupera l'elenco dei nomi delle collezioni di atti esistenti e già disponibili.

**Parametri:**
*Nessun parametro richiesto.*

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/collections/collection-predefinite' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' | jq
```

**Esempio di Risposta (JSON):**
```json
[
  {
    "nomeCollezione": "Atti della sanita' e salute pubblica",
    "formatoCollezione": "O",
    "descrizioneFormatoCollezione": "ORIGINALE",
    "dataCreazione": "2026-02-25",
    "numeroAtti": 2890
  },
  {
    "nomeCollezione": "Testi Unici",
    "formatoCollezione": "V",
    "descrizioneFormatoCollezione": "VIGENTE",
    "dataCreazione": "2026-02-25",
    "numeroAtti": 255
  },
  "... (totale 178 risultati)"
]
```

---

## 3. Ricerche Predefinite
Recupera l'elenco delle ricerche già preimpostate nel portale Normattiva.

**Parametri:**
*Nessun parametro richiesto.*

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca/predefinita' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' | jq
```

**Esempio di Risposta (JSON):**
```json
{
  "ricerchePredefinite": [
    {
      "nome": "Atti Repubblica",
      "dettagli": [
        {
          "nomeCampo": "EmanazioneFrom",
          "valoreCampo": "1946-06-20"
        },
        {
          "nomeCampo": "EmanazioneTo",
          "valoreCampo": "2024-12-19"
        }
      ],
      "dataCreazione": "2024-12-17T20:23:02"
    },
    "... (altre ricerche come 'Atti abrogati' e 'Atti in formato originario')"
  ]
}
```

---

## 4. Tipologiche: Classe Provvedimento
Recupera l'elenco delle classi di provvedimento disponibili in base dati.

**Parametri:**
*Nessun parametro richiesto.*

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/tipologiche/classe-provvedimento' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' | jq
```

**Esempio di Risposta (JSON):**
```json
[
  {
    "label": "1",
    "value": "atto normativo – senza aggiornamenti"
  },
  {
    "label": "2",
    "value": "atto normativo – aggiornato"
  },
  {
    "label": "3",
    "value": "atto normativo – abrogato"
  }
]
```

---

## 5. Tipologiche: Denominazione atto
Recupera l'elenco dei tipi di provvedimento (es. DECRETO, LEGGE, ecc).

**Parametri:**
*Nessun parametro richiesto.*

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/tipologiche/denominazione-atto' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' | jq
```

**Esempio di Risposta (JSON):**
```json
[
  {
    "label": "COS",
    "value": "COSTITUZIONE"
  },
  {
    "label": "DCT",
    "value": "DECRETO"
  },
  {
    "label": "PDL",
    "value": "DECRETO-LEGGE"
  },
  {
    "label": "PLE",
    "value": "LEGGE"
  },
  "... (totale 30 elementi)"
]
```

---

## 6. Ricerca Semplice
Permette di esportare una collezione di atti o ottenerne i metadati sulla base di criteri elementari immessi (parole e ordinamento).

**Parametri Body JSON:**
* `testoRicerca`: (String) Parole ricercate nel titolo e/o nel testo ad inserimento libero.
* `orderType`: (String) Valori ammissibili: `"recente"` o `"vecchio"`.
* `paginazione.paginaCorrente`: (Number) Numero di pagina di interesse.
* `paginazione.numeroElementiPerPagina`: (Number) Limite risultati.
* `filtriMap` (Opzionale): Filtri tra i quali:
  * `codice_tipo_provvedimento`: (String) valore ottenuto da DENOMINAZIONE ATTO
  * `anno_provvedimento`: (Number) Anno del provvedimento (es: `2022`)

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca/semplice' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' \
  --data-raw '{"testoRicerca":"provvedimento","orderType":"recente","paginazione":{"paginaCorrente":1,"numeroElementiPerPagina":2}}' | jq
```

**Esempio di Risposta (JSON):**
```json
{
  "listaAtti": [
    {
      "numeroAtto": "12",
      "numeroAttoAlfanumerico": "12",
      "dataGU": "2025-02-18",
      "titoloAtto": "[Disposizioni  integrative  e  correttive  al  codice  dei  contratti, ...]",
      "denominazioneAtto": "DECRETO LEGISLATIVO",
      "descrizioneAtto": "DECRETO LEGISLATIVO 12 febbraio 2025, n. 12",
      "... (ulteriori dettagli ometti per brevità)"
    }
  ],
  "facetMap": {
    "anno_provvedimento": [ { "codice": "2025", "valore": 13, "descrizione": "2025" } ],
    "codice_tipo_provvedimento": [ { "codice": "DCT", "valore": 149, "descrizione": "DECRETO" } ]
  },
  "numeroPagine": 2045,
  "numeroAttiTrovati": 4090,
  "paginaCorrente": 1
}
```

---

## 7. Ricerca Avanzata
Permette di esportare una collezione di atti sulla base di criteri dettagliati.

**Parametri Body JSON:**
* `denominazioneAtto`: (String) Es: `"DECRETO"`.
* `titoloRicerca`: (String) Keywords ricercate nel titolo. 
* `testoRicerca`: (String) Keywords per la buca di ricerca del testo.
* `dataInizioEmanazione`: (String) Data Formato `YYYY-MM-DD`.
* `dataFineEmanazione`: (String) Data Formato `YYYY-MM-DD`.
* `dataInizioPubProvvedimento`: (String) Data Formato `YYYY-MM-DD`.
* `dataFinePubProvvedimento`: (String) Data Formato `YYYY-MM-DD`.
* `vigenza`: (String) Formato `YYYY-MM-DD`.
* `classeProvvedimento`: (String) Identificativo (es. `"1"`, `"2"`, `"3"` prelevati dalla rispettiva API).
* `orderType`: (String) `"recente"` o `"vecchio"`.
* `paginazione.paginaCorrente`: (Number) Pagina di ricerca.
* `paginazione.numeroElementiPerPagina`: (Number) Risultati.
* `annoProvvedimento`: (Number) Anno dell'atto.
* `meseProvvedimento`: (Number) Mese dell'atto.
* `giornoProvvedimento`: (Number) Giorno dell'atto.
* `numeroProvvedimento`: (String/Number) Numero identificativo.
* `filtriMap` (Opzionale): come nella ricerca semplice.

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca/avanzata' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' \
  --data-raw '{"denominazioneAtto":"DECRETO","orderType":"recente","titoloRicerca":"legge","testoRicerca":"ministro","dataInizioEmanazione":"2023-01-01","dataFineEmanazione":"2023-12-31","dataInizioPubProvvedimento":"2023-01-01","dataFinePubProvvedimento":"2023-12-31","vigenza":"2025-01-09","classeProvvedimento":"2","paginazione":{"paginaCorrente":1,"numeroElementiPerPagina":2}}' | jq
```

**Esempio di Risposta (JSON):**
```json
{
  "listaAtti": [
    {
      "numeroAtto": "217",
      "dataGU": "2023-12-30",
      "codiceRedazionale": "23G00224",
      "titoloAtto": "[Regolamento recante: «Decreto ai sensi dell'articolo 87...]",
      "denominazioneAtto": "DECRETO",
      "descrizioneAtto": "DECRETO 29 dicembre 2023, n. 217"
    },
    {
      "numeroAtto": "150",
      "dataGU": "2023-10-31",
      "denominazioneAtto": "DECRETO",
      "descrizioneAtto": "DECRETO 24 ottobre 2023, n. 150"
    }
  ],
  "facetMap": {
    "anno_provvedimento": [ { "codice": "2023", "valore": 2 } ]
  },
  "numeroPagine": 1,
  "numeroAttiTrovati": 2,
  "paginaCorrente": 1
}
```

---

## 8. Inserimento richiesta export (Ricerca Asincrona)
Avvio di ricerca per l'export ad eventi (.ZIP). La risposta fornirà nel body il token (`ID_COLLEZIONE`).

**Parametri Body JSON:**
* `formato`: (String) Obbligatorio, scegli da `"AKN"`, `"HTML"`, `"JSON"`, `"URI"`, `"XML"`, `"PDF"`, `"EPUB"`, `"RTF"`.
* `tipoRicerca`: (String) Obbligatorio, valori ammessi: `"S"` (Ricerca Semplice) oppure `"A"` (Ricerca Avanzata).
* `modalita`: (String) Opzionale, `"C"` (Classica) o `"R"` (Responsive).
* `email`: (String) Opzionale.
* `parametriRicerca`: (Oggetto JSON) Oggetto contenente tutti i parametri di ricerca definiti in *Ricerca Semplice* o *Ricerca Avanzata* con opzionalmente `filtriMap`.

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/nuova-ricerca' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' \
  --data-raw '{"formato":"PDF","tipoRicerca":"S","modalita":"C","parametriRicerca":{"filtriMap":{"codice_tipo_provvedimento":"DCS"},"testoRicerca":"104","vigenza":"2025-01-07"}}'
```

**Esempio di Risposta (Testo Semplice):**
```text
bbe2c735-de04-4f52-af69-a8c1dec46636
```
*(Questo è il token / ID_COLLEZIONE da usare negli step successivi)*

---

## 9. Conferma Ricerca (Asincrona)
Indispensabile per confermare la richiesta di esportazione effettuata, fornendo il Token.

**Parametri Body JSON:**
* `token`: (String) L'`ID_COLLEZIONE` ricavato in fase di start esportazione.

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/conferma-ricerca' \
  -X 'PUT' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' \
  --data-raw '{"token":"<ID_COLLEZIONE_QUI>"}' | jq
```

**Esempio di Risposta (Status Code 200/202 OK):**
*Nessun body restituito se la richiesta viene confermata ed accodata correttamente.*

---

## 10. Check-Status (Download Ricerca Asincrona)
Interrogazione in polling per monitorare e ottenere il file PDF/ZIP. Finchè status è `200` elabora. Se `303`, dalla header `x-ipzs-location` c'è l'URL da richiamare tramite GET per fare il file download.

**Parametri Query String:**
* `ID_COLLEZIONE` passato da route: Il check status è integrato nel path stesso.

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca-asincrona/check-status/ID_COLLEZIONE_QUI' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' | jq
```

**Esempio di Risposta (In Lavorazione - JSON - Status Code 200):**
```json
{
  "stato": 1,
  "descrizioneStato": "Ricerca in lavorazione..."
}
```

**Esempio di Risposta (Completata - JSON - Status Code 303):**
```json
{
  "stato": 3,
  "descrizioneStato": "Ricerca elaborata con successo",
  "descrizioneErrore": null
}
```
*(In questo caso, ispezionare l'header `x-ipzs-location` della risposta HTTP per l'URL di download)*

---

## 11. Visualizzazione Dettaglio Atto
API (per versione Mobile / Backend For Frontend) che serve a visualizzare il dettaglio di un atto preciso, articolo per articolo.

**Parametri Body JSON:**
* `dataGU`: (String) Obbligatorio, Formato `YYYY-DD-MM`.
* `codiceRedazionale`: (String) Obbligatorio.
* `idArticolo`: (Number) ID dell'articolo.
* `sottoArticolo`: (Number) Sottoarticolo.
* `dataVigenza`: (String) Formato `YYYY-DD-MM`.
* `idGruppo`: (Number) ID del gruppo articoli se presente.
* `progressivo`: (Number) Limit/Progress.
* `versione`: (Number) `0` per originale.

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-mobile/v1/api/v1/atto/dettaglio-atto' \
  -X 'POST' \
  -H 'Accept: */*' \
  -H 'Content-Type: application/json' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' \
  --data-raw '{"dataGU": "1988-09-12", "codiceRedazionale": "088G0458", "idArticolo": 13, "sottoArticolo": 2, "sottoArticolo1": 0, "dataVigenza": "2025-02-27", "idGruppo": 6, "progressivo": 0, "versione": 0}' | jq
```

**Esempio di Risposta (JSON):**
```json
{
  "data": {
    "atto": {
      "titolo": "LEGGE 23 agosto 1988, n. 400",
      "sottoTitolo": "Disciplina dell'attivita' di Governo e ordinamento della\r\nPresidenza del Consiglio dei Ministri.\r\n",
      "articoloHtml": "<div class=\"bodyTesto\">\n <h2 class=\"preamble-title-akn\"></h2>\n <h2 class=\"preamble-end-akn\"></h2>\n <h2 class=\"article-num-akn\" id=\"art_13-bis\">Art. 13-bis</h2>\n ... </div>",
      "tipoProvvedimentoDescrizione": "LEGGE",
      "tipoProvvedimentoCodice": "PLE",
      "numeroProvvedimento": 400,
      "annoGU": 1988,
      "meseGU": 9,
      "giornoGU": 12,
      "numeroGU": 214,
      "... (ulteriori informazioni sull'atto)"
    },
    "message": null
  },
  "success": true
}
```

---

## 12. Download Collezione Preconfezionata
API in GET per scaricare l'archivio già compilato e confezionato di atti di una specifica *collezione*.

**Parametri Query String:**
* `nome`: (String) Obbligatorio. Nome della collezione.
* `formato`: (String) Obbligatorio. Tipo formato come `"AKN"`, `"EPUB"`, `"HTML"`, `"JSON"`, `"PDF"`, `"RTF"`, `"XML"`, `"URI"`.
* `formatoRichiesta`: (String) Obbligatorio. Valori: `"O"` (Originario), `"V"` (Vigente), `"M"` (Multivigente).

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/collections/download/collection-preconfezionata?nome=Codici&formato=AKN&formatoRichiesta=O' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' --output collezione.zip
```

**Esempio di Risposta:**
*Non vi è output testuale (Status Code 200). La risposta sarà il contenuto binario del file `.zip` che verrà scaricato e salvato come `collezione.zip`.*

---

## 13. Ricerca Atti Aggiornati
API per ottenere un set di atti aggiornati entro un preciso arco temporale recente (Max 12 mesi).

**Parametri Body JSON:**
* `dataInizioAggiornamento`: (String) Obbligatorio, Formato completo ISO (es. `2024-04-27T11:43:51.827Z`).
* `dataFineAggiornamento`: (String) Obbligatorio, Formato completo ISO. 

**Curl Completo:**
```bash
curl 'https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/ricerca/aggiornati' \
  -X 'POST' \
  -H 'Accept: */*' \
  -H 'Content-Type: application/json' \
  -H 'Connection: keep-alive' \
  -H 'User-Agent: Mozilla/5.0' \
  --data-raw '{"dataInizioAggiornamento": "2024-04-27T11:43:51.827Z", "dataFineAggiornamento": "2024-04-29T11:43:51.827Z"}' | jq
```

**Esempio di Risposta (JSON):**
```json
{
  "listaAtti": [
    {
      "numeroAtto": "1",
      "numeroAttoAlfanumerico": "14",
      "dataGU": "2024-02-22",
      "titoloAtto": "Ratifica ed esecuzione del Protocollo tra il Governo [...] (24G00028)",
      "denominazioneAtto": "LEGGE",
      "descrizioneAtto": "LEGGE 21 febbraio 2024, n. 14",
      "dataUltimaModifica": "2024-04-29",
      "ultimiAttiModificanti": "24A02110"
    }
  ],
  "numeroPagine": 1,
  "numeroAttiTrovati": 4,
  "paginaCorrente": 1
}
```

---

## 14. Esportazione Diretta Atto Singolo (Navigazione Web)
Se conosci i parametri esatti (`dataPubblicazioneGazzetta` e `codiceRedazionale`) di un atto, il portale espone un URL diretto per richiederne l'esportazione completa (es. in XML). 
Questo link viene tipicamente gestito tramite sessione browser (richiede Cookie validi o Header origin), perciò se richiamato programmaticamente in GET nudo e crudo spesso restituisce l'HTML della pagina.

**Parametri Query String:**
* `atto.dataPubblicazioneGazzetta`: (String) Data nel formato `YYYY-MM-DD`.
* `atto.codiceRedazionale`: (String) Codice redazionale rintracciabile dalle altre chiamate.
* `exportFormat`: (String) Il formato desiderato, tipicamente `xml`.

**Curl Completo (Esempio teorico, potrebbe richiedere Cookie di sessione \JSESSIONID):**
```bash
curl -L 'https://www.normattiva.it/esporta/attoCompleto?atto.dataPubblicazioneGazzetta=2026-02-06&atto.codiceRedazionale=26G00028&exportFormat=xml' \
  -H 'Accept: application/xml' \
  -H 'User-Agent: Mozilla/5.0' \
  --output atto_completo.xml
```

**Esempio di Risposta:**
*Dipendentemente dal contesto di invocazione, se si possessori di una sessione valida il comando scaricherà il file XML parsato del documento. In assenza di sessione (`JSESSIONID`), il server potrebbe redigere una pagina HTML di blocco (Errore! Sessione scaduta).*

---

