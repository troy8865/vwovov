import requests
import os
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def dlhd_channels():
    """
    Estrae tutti i canali da https://daddylive.sx/24-7-channels.php,
    deduce la regione dal nome canale, usa il dominio corretto e salva in un file M3U.
    """
    import requests
    import re
    from bs4 import BeautifulSoup

    url = "https://daddylive.sx/24-7-channels.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    
    # Inizializza UNA SOLA VOLTA
    channels_by_region = {}
    seen_channels = set()  # Aggiungi un set per tracciare i canali già visti

    region_keywords = [
        "USA", "UK", "Italy", "Germany", "France", "Spain", "Portugal", "Poland", "Russia", "India", "Turkey", "Greece", "Netherlands", "Belgium", "Sweden", "Norway", "Denmark", "Finland", "Romania", "Hungary", "Bulgaria", "Serbia", "Croatia", "Slovenia", "Slovakia", "Czech", "Austria", "Switzerland", "Ireland", "Albania", "Bosnia", "Macedonia", "Montenegro", "Kosovo", "Ukraine", "Georgia", "Armenia", "Azerbaijan", "Lithuania", "Latvia", "Estonia", "China", "Japan", "Korea", "Australia", "Canada", "Brazil", "Argentina", "Mexico", "Chile", "Colombia", "Peru", "Venezuela", "Uruguay", "Paraguay", "Ecuador", "Bolivia", "Africa", "Arabia", "UAE", "Qatar", "Saudi", "Egypt", "Israel", "Morocco", "Tunisia", "Algeria", "International"
    ]

    def guess_region(name):
        for region in region_keywords:
            if region.lower() in name.lower():
                return region
        return "Other"

    # Prendi tutti i div.grid-item che contengono i canali
    grid_items = soup.find_all("div", class_="grid-item")

    for div in grid_items:
        a = div.find("a", href=True)
        if not a:
            continue
        
        href = a["href"].strip()
        href = href.replace(" ", "").replace("//", "/")
        
        strong = a.find("strong")
        if strong:
            name = strong.get_text(strip=True)
        else:
            name = a.get_text(strip=True)
        
        match = re.search(r'stream-(\d+)\.php', href)
        if not match:
            continue
            
        channel_id = match.group(1)
        
        # Crea una chiave unica per identificare canali duplicati
        channel_key = (name.lower(), channel_id)
        
        # Salta se il canale è già stato processato
        if channel_key in seen_channels:
            continue
            
        seen_channels.add(channel_key)
        
        stream_url = f"https://daddylive.sx/stream/stream-{channel_id}.php"
        region = guess_region(name)
        
        if region not in channels_by_region:
            channels_by_region[region] = []
        channels_by_region[region].append((name, stream_url))

    # Resto del codice rimane uguale...
    output_file = "dlhd_channels.m3u"
    
    def clean_name_for_m3u(name):
        cleaned = name
        for region_word in region_keywords:
            cleaned = re.sub(rf"(\s|\(|\[|^)({re.escape(region_word)})(\s|\)|\]|$)", r" ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if not cleaned:
            cleaned = name
        return cleaned

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for region in sorted(channels_by_region.keys()):
            channels = sorted(channels_by_region[region], key=lambda x: x[0].lower())
            for name, url in channels:
                name_clean = clean_name_for_m3u(name)
                f.write(f'#EXTINF:-1 group-title="{region} DLHD",{name_clean}\n{url}\n')
    
    print(f"Creato file {output_file} con {sum(len(v) for v in channels_by_region.values())} canali 24/7.")

def dlhd_events():
    print("Eseguendo dlhd_events...")
    import json
    import re
    import requests
    import urllib.parse # Consolidato
    from datetime import datetime, timedelta
    from dateutil import parser
    import os
    from dotenv import load_dotenv
    # ...existing code...
    import time
    
    # Carica le variabili d'ambiente dal file .env
    load_dotenv()

    LINK_DADDY = os.getenv("LINK_DADDY", "https://daddylive.sx").strip() 
    JSON_FILE = "daddyliveSchedule.json" 
    OUTPUT_FILE = "dlhd_events.m3u" 
    HEADERS = { 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36" 
    } 
     
    HTTP_TIMEOUT = 10 
    session = requests.Session() 
    session.headers.update(HEADERS) 
    # Definisci current_time e three_hours_in_seconds per la logica di caching
    current_time = time.time()
    three_hours_in_seconds = 3 * 60 * 60
    
    def clean_category_name(name): 
        # Rimuove tag html come </span> o simili 
        return re.sub(r'<[^>]+>', '', name).strip()
        
    def clean_tvg_id(tvg_id):
        """
        Pulisce il tvg-id rimuovendo caratteri speciali, spazi e convertendo tutto in minuscolo
        """
        # import re # 're' Ã¨ giÃ  importato a livello di funzione
        # Rimuove caratteri speciali comuni mantenendo solo lettere e numeri
        cleaned = re.sub(r'[^a-zA-Z0-9À-ÿ]', '', tvg_id)
        return cleaned.lower()
     
    def get_stream_from_channel_id(channel_id): 
        # Restituisce direttamente l'URL .php
        embed_url = f"{LINK_DADDY}/stream/stream-{channel_id}.php" 
        return embed_url
     
    # ...existing code...
     
    def extract_channels_from_json(path): 
        keywords = {"uk", "tnt", "usa", "tennis channel", "tennis stream", "la"} 
        now = datetime.now()  # ora attuale completa (data+ora) 
        yesterday_date = (now - timedelta(days=1)).date() # Data di ieri
     
        with open(path, "r", encoding="utf-8") as f: 
            data = json.load(f) 
     
        categorized_channels = {} 
     
        for date_key, sections in data.items(): 
            date_part = date_key.split(" - ")[0] 
            try: 
                date_obj = parser.parse(date_part, fuzzy=True).date() 
            except Exception as e: 
                print(f"[!] Errore parsing data '{date_part}': {e}") 
                continue 
            
            # Determina se processare questa data
            process_this_date = False
            is_yesterday_early_morning_event_check = False

            if date_obj == now.date():
                process_this_date = True
            elif date_obj == yesterday_date:
                process_this_date = True
                is_yesterday_early_morning_event_check = True # Flag per eventi di ieri mattina presto
            else:
                # Salta date che non sono nÃ© oggi nÃ© ieri
                continue

            if not process_this_date:
                continue
     
            for category_raw, event_items in sections.items(): 
                category = clean_category_name(category_raw)
                # Salta la categoria TV Shows
                if category.lower() == "tv shows":
                    continue
                if category not in categorized_channels: 
                    categorized_channels[category] = [] 
     
                for item in event_items: 
                    time_str = item.get("time", "00:00") # Orario originale dal JSON
                    event_title = item.get("event", "Evento") 
     
                    try: 
                        # Parse orario evento originale (dal JSON)
                        original_event_time_obj = datetime.strptime(time_str, "%H:%M").time()

                        # Costruisci datetime completo dell'evento con la sua data originale e l'orario originale (senza aggiungere ore)
                        event_datetime_adjusted_for_display_and_filter = datetime.combine(date_obj, original_event_time_obj)

                        if is_yesterday_early_morning_event_check:
                            # Filtro per eventi di ieri mattina presto (00:00 - 04:00, ora JSON)
                            start_filter_time = datetime.strptime("00:00", "%H:%M").time()
                            end_filter_time = datetime.strptime("04:00", "%H:%M").time()
                            # Confronta l'orario originale dell'evento
                            if not (start_filter_time <= original_event_time_obj <= end_filter_time):
                                # Evento di ieri, ma non nell'intervallo 00:00-04:00 -> salto
                                continue
                        else: # Eventi di oggi
                            # Controllo: includi solo se l'evento Ã¨ iniziato da meno di 2 ore
                            # Usa event_datetime_adjusted_for_display_and_filter che ha giÃ  il +2h
                            if now - event_datetime_adjusted_for_display_and_filter > timedelta(hours=2):
                                # Evento di oggi iniziato da piÃ¹ di 2 ore -> salto
                                continue
                        
                        time_formatted = event_datetime_adjusted_for_display_and_filter.strftime("%H:%M")
                    except Exception as e_time:
                        print(f"[!] Errore parsing orario '{time_str}' per evento '{event_title}' in data '{date_key}': {e_time}")
                        time_formatted = time_str # Fallback
     
                    for ch in item.get("channels", []): 
                        channel_name = ch.get("channel_name", "") 
                        channel_id = ch.get("channel_id", "") 
     
                        words = set(re.findall(r'\b\w+\b', channel_name.lower())) 
                        if keywords.intersection(words): 
                            tvg_name = f"{event_title} ({time_formatted})" 
                            categorized_channels[category].append({ 
                                "tvg_name": tvg_name, 
                                "channel_name": channel_name, 
                                "channel_id": channel_id,
                                "event_title": event_title 
                            }) 
     
        return categorized_channels 
     
    def generate_m3u_from_schedule(json_file, output_file): 
        categorized_channels = extract_channels_from_json(json_file) 

        with open(output_file, "w", encoding="utf-8") as f: 
            f.write("#EXTM3U\n") 

            # Controlla se ci sono eventi prima di aggiungere il canale DADDYLIVE
            has_events = any(channels for channels in categorized_channels.values())
            
            if has_events:
                # Aggiungi il canale iniziale/informativo solo se ci sono eventi
                f.write(f'#EXTINF:-1 group-title="Live Events",DADDYLIVE\n')
                f.write("https://example.com.m3u8\n\n")
            else:
                print("[ℹ️] Nessun evento trovato, canale DADDYLIVE non aggiunto.")

            for category, channels in categorized_channels.items(): 
                if not channels: 
                    continue 
          
                for ch in channels: 
                    tvg_name = ch["tvg_name"] 
                    channel_id = ch["channel_id"] 
                    event_title = ch["event_title"]  # Otteniamo il titolo dell'evento
                    channel_name = ch["channel_name"]
     
                    try: 
                        stream = get_stream_from_channel_id(channel_id)
                        if stream: 
                            cleaned_event_id = clean_tvg_id(event_title) # Usa event_title per tvg-id
                            f.write(f'#EXTINF:-1 group-title="Live Events",{category} | {tvg_name}\n')
                            f.write(f'{stream}\n\n')
                        else: 
                            print(f"[✗] {tvg_name} - Nessuno stream trovato") 
                    except Exception as e: 
                        print(f"[!] Errore su {tvg_name}: {e}") 
     
    # Esegui la generazione quando la funzione viene chiamata
    generate_m3u_from_schedule(JSON_FILE, OUTPUT_FILE)

# Funzione per il quarto script (schedule_extractor.py)
def schedule_extractor():
    # Codice del quarto script qui
    # Aggiungi il codice del tuo script "schedule_extractor.py" in questa funzione.
    print("Eseguendo lo schedule_extractor.py...")
    # Il codice che avevi nello script "schedule_extractor.py" va qui, senza modifiche.
    from playwright.sync_api import sync_playwright
    import os
    import json
    from datetime import datetime
    import re
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv
    
    # Carica le variabili d'ambiente dal file .env
    load_dotenv()
    
    LINK_DADDY = os.getenv("LINK_DADDY", "https://daddylive.sx").strip()
    
    def html_to_json(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        result = {}
        
        date_rows = soup.find_all('tr', class_='date-row')
        if not date_rows:
            print("AVVISO: Nessuna riga di data trovata nel contenuto HTML!")
            return {}
    
        current_date = None
        current_category = None
    
        for row in soup.find_all('tr'):
            if 'date-row' in row.get('class', []):
                current_date = row.find('strong').text.strip()
                result[current_date] = {}
                current_category = None
    
            elif 'category-row' in row.get('class', []) and current_date:
                current_category = row.find('strong').text.strip() + "</span>"
                result[current_date][current_category] = []
    
            elif 'event-row' in row.get('class', []) and current_date and current_category:
                time_div = row.find('div', class_='event-time')
                info_div = row.find('div', class_='event-info')
    
                if not time_div or not info_div:
                    continue
    
                time_strong = time_div.find('strong')
                event_time = time_strong.text.strip() if time_strong else ""
                event_info = info_div.text.strip()
    
                event_data = {
                    "time": event_time,
                    "event": event_info,
                    "channels": []
                }
    
                # Cerca la riga dei canali successiva
                next_row = row.find_next_sibling('tr')
                if next_row and 'channel-row' in next_row.get('class', []):
                    channel_links = next_row.find_all('a', class_='channel-button-small')
                    for link in channel_links:
                        href = link.get('href', '')
                        channel_id_match = re.search(r'stream-(\d+)\.php', href)
                        if channel_id_match:
                            channel_id = channel_id_match.group(1)
                            channel_name = link.text.strip()
                            channel_name = re.sub(r'\s*\(CH-\d+\)$', '', channel_name)
    
                            event_data["channels"].append({
                                "channel_name": channel_name,
                                "channel_id": channel_id
                            })
    
                result[current_date][current_category].append(event_data)
    
        return result
    
    def modify_json_file(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        current_month = datetime.now().strftime("%B")
    
        for date in list(data.keys()):
            match = re.match(r"(\w+\s\d+)(st|nd|rd|th)\s(\d{4})", date)
            if match:
                day_part = match.group(1)
                suffix = match.group(2)
                year_part = match.group(3)
                new_date = f"{day_part}{suffix} {current_month} {year_part}"
                data[new_date] = data.pop(date)
    
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        print(f"File JSON modificato e salvato in {json_file_path}")
    
    def extract_schedule_container():
        url = f"{LINK_DADDY}/"
    
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_output = os.path.join(script_dir, "daddyliveSchedule.json")
    
        print(f"Accesso alla pagina {url} per estrarre il main-schedule-container...")
    
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
    
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    print(f"Tentativo {attempt} di {max_attempts}...")
                    page.goto(url)
                    print("Attesa per il caricamento completo...")
                    page.wait_for_timeout(10000)  # 10 secondi
    
                    schedule_content = page.evaluate("""() => {
                        const container = document.getElementById('main-schedule-container');
                        return container ? container.outerHTML : '';
                    }""")
    
                    if not schedule_content:
                        print("AVVISO: main-schedule-container non trovato o vuoto!")
                        if attempt == max_attempts:
                            browser.close()
                            return False
                        else:
                            continue
    
                    print("Conversione HTML in formato JSON...")
                    json_data = html_to_json(schedule_content)
    
                    with open(json_output, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
    
                    print(f"Dati JSON salvati in {json_output}")
    
                    modify_json_file(json_output)
                    browser.close()
                    return True
    
                except Exception as e:
                    print(f"ERRORE nel tentativo {attempt}: {str(e)}")
                    if attempt == max_attempts:
                        print("Tutti i tentativi falliti!")
                        browser.close()
                        return False
                    else:
                        print(f"Riprovando... (tentativo {attempt + 1} di {max_attempts})")
    
            browser.close()
            return False
    
    if __name__ == "__main__":
        success = extract_schedule_container()
        if not success:
            exit(1)

def vavoo_channels():
    # Codice del settimo script qui
    # Aggiungi il codice del tuo script "world_channels_generator.py" in questa funzione.
    print("Eseguendo vavoo_channels...")
    # Il codice che avevi nello script "world_channels_generator.py" va qui, senza modifiche.
    import requests
    import time
    import re
    
    def getAuthSignature():
        headers = {
            "user-agent": "okhttp/4.11.0",
            "accept": "application/json",
            "content-type": "application/json; charset=utf-8",
            "content-length": "1106",
            "accept-encoding": "gzip"
        }
        data = {
            "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoADQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
            "reason": "app-blur",
            "locale": "de",
            "theme": "dark",
            "metadata": {
                "device": {
                    "type": "Handset",
                    "os": "Android",
                    "osVersion": "10",
                    "model": "Pixel 4",
                    "brand": "Google"
                }
            }
        }
        resp = requests.post("https://vavoo.to/mediahubmx-signature.json", json=data, headers=headers, timeout=10)
        return resp.json().get("signature")
    
    def vavoo_groups():
        # Puoi aggiungere altri gruppi per più canali
        return [""]
    
    def clean_channel_name(name):
        """Rimuove i suffissi .a, .b, .c dal nome del canale"""
        # Rimuove .a, .b, .c alla fine del nome (con o senza spazi prima)
        cleaned_name = re.sub(r'\s*\.(a|b|c|s|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|t|u|v|w|x|y|z)\s*$', '', name, flags=re.IGNORECASE)
        return cleaned_name.strip()
    
    def get_channels():
        signature = getAuthSignature()
        headers = {
            "user-agent": "okhttp/4.11.0",
            "accept": "application/json",
            "content-type": "application/json; charset=utf-8",
            "accept-encoding": "gzip",
            "mediahubmx-signature": signature
        }
        all_channels = []
        for group in vavoo_groups():
            cursor = 0
            while True:
                data = {
                    "language": "de",
                    "region": "AT",
                    "catalogId": "iptv",
                    "id": "iptv",
                    "adult": False,
                    "search": "",
                    "sort": "name",
                    "filter": {"group": group},
                    "cursor": cursor,
                    "clientVersion": "3.0.2"
                }
                resp = requests.post("https://vavoo.to/mediahubmx-catalog.json", json=data, headers=headers, timeout=10)
                r = resp.json()
                items = r.get("items", [])
                all_channels.extend(items)
                cursor = r.get("nextCursor")
                if not cursor:
                    break
        return all_channels
    
    def save_as_m3u(channels, filename="vavoo_channels.m3u"):
        # Raggruppa i canali per categoria
        channels_by_category = {}
        
        for ch in channels:
            original_name = ch.get("name", "SenzaNome")
            # Pulisce il nome rimuovendo .a, .b, .c
            name = clean_channel_name(original_name)
            url = ch.get("url", "")
            category = ch.get("group", "Generale")  # Usa il campo "group" come categoria
            
            if url:
                if category not in channels_by_category:
                    channels_by_category[category] = []
                channels_by_category[category].append((name, url))
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            # Ordina categorie e canali alfabeticamente
            for category in sorted(channels_by_category.keys()):
                channel_list = sorted(channels_by_category[category], key=lambda x: x[0].lower())
                f.write(f"\n# {category.upper()}\n")
                for name, url in channel_list:
                    f.write(f'#EXTINF:-1 group-title="{category} VAVOO",{name}\n{url}\n')
        
        print(f"Playlist M3U salvata in: {filename}")
        print(f"Canali organizzati in {len(channels_by_category)} categorie:")
        for category, channel_list in channels_by_category.items():
            print(f"  - {category}: {len(channel_list)} canali")
    
    if __name__ == "__main__":
        channels = get_channels()
        print(f"Trovati {len(channels)} canali. Creo la playlist M3U con i link proxy...")
        save_as_m3u(channels) 

def main():
    # ...existing code...
    try:
        try:
            schedule_extractor()
        except Exception as e:
            print(f"Errore durante l'esecuzione di schedule_extractor: {e}")
            return
        try:
            vavoo_channels()
        except Exception as e:
            print(f"Errore durante l'esecuzione di vavoo_channels: {e}")
            return
        try:
            dlhd_events()
        except Exception as e:
            print(f"Errore durante l'esecuzione di dlhd_events: {e}")
            return
        try:
            dlhd_channels()
        except Exception as e:
            print(f"Errore durante l'esecuzione di dlhd_channels: {e}")
            return
        print("Tutti gli script sono stati eseguiti correttamente!")
    finally:
        pass

if __name__ == "__main__":
    main()
