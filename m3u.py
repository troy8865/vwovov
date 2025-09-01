import requests
import os
import re
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ------------------- DLHD Fonksiyonu -------------------
def dlhd():
    """
    Estrae canali 24/7 e eventi live da DaddyLive e li salva in un unico file M3U.
    Rimuove automaticamente i canali duplicati.
    """
    print("Eseguendo dlhd...")
    import requests
    from bs4 import BeautifulSoup
    import re
    from datetime import datetime, timedelta
    from dateutil import parser
    import os
    import json

    load_dotenv()

    LINK_DADDY = os.getenv("LINK_DADDY", "https://daddylive.sx").strip()
    JSON_FILE = "daddyliveSchedule.json"
    OUTPUT_FILE = "dlhd.m3u"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    def clean_category_name(name):
        return re.sub(r'<[^>]+>', '', name).strip()

    def clean_tvg_id(tvg_id):
        cleaned = re.sub(r'[^a-zA-Z0-9À-ÿ]', '', tvg_id)
        return cleaned.lower()

    def get_stream_from_channel_id(channel_id):
        return f"{LINK_DADDY}/stream/stream-{channel_id}.php"

    # ========== CANALI 24/7 ==========
    print("Estraendo canali 24/7...")
    url = "https://daddylive.sx/24-7-channels.php"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        channels_247 = []

        grid_items = soup.find_all("div", class_="grid-item")
        for div in grid_items:
            a = div.find("a", href=True)
            if not a:
                continue
            href = a["href"].strip().replace(" ", "").replace("//", "/")
            name = a.find("strong").get_text(strip=True) if a.find("strong") else a.get_text(strip=True)

            if name == "LA7d HD+ Italy":
                name = "Canale 5 Italy"
            if name == "Sky Calcio 7 (257) Italy":
                name = "DAZN"

            match = re.search(r'stream-(\d+)\.php', href)
            if not match:
                continue
            channel_id = match.group(1)
            stream_url = get_stream_from_channel_id(channel_id)
            channels_247.append((name, stream_url))

        # Rimuove duplicati
        name_counts = {}
        for name, _ in channels_247:
            name_counts[name] = name_counts.get(name, 0) + 1

        final_channels = []
        name_counter = {}
        for name, stream_url in channels_247:
            if name_counts[name] > 1:
                if name not in name_counter:
                    name_counter[name] = 1
                    final_channels.append((name, stream_url))
                else:
                    name_counter[name] += 1
                    final_channels.append((f"{name} ({name_counter[name]})", stream_url))
            else:
                final_channels.append((name, stream_url))

        channels_247 = sorted(final_channels, key=lambda x: x[0].lower())
        print(f"Trovati {len(channels_247)} canali 24/7")
    except Exception as e:
        print(f"Errore nell'estrazione dei canali 24/7: {e}")
        channels_247 = []

    # ========== EVENTI LIVE ==========
    print("Estraendo eventi live...")
    live_events = []
    if os.path.exists(JSON_FILE):
        try:
            now = datetime.now()
            yesterday_date = (now - timedelta(days=1)).date()

            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            categorized_channels = {}
            for date_key, sections in data.items():
                date_part = date_key.split(" - ")[0]
                try:
                    date_obj = parser.parse(date_part, fuzzy=True).date()
                except:
                    continue

                process_this_date = date_obj == now.date() or date_obj == yesterday_date
                is_yesterday_early_morning_event_check = date_obj == yesterday_date

                if not process_this_date:
                    continue

                for category_raw, event_items in sections.items():
                    category = clean_category_name(category_raw)
                    if category.lower() == "tv shows":
                        continue
                    if category not in categorized_channels:
                        categorized_channels[category] = []

                    for item in event_items:
                        time_str = item.get("time", "00:00")
                        event_title = item.get("event", "Evento")
                        try:
                            original_event_time_obj = datetime.strptime(time_str, "%H:%M").time()
                            event_datetime = datetime.combine(date_obj, original_event_time_obj)
                            if is_yesterday_early_morning_event_check:
                                if not (datetime.strptime("00:00", "%H:%M").time() <= original_event_time_obj <= datetime.strptime("04:00", "%H:%M").time()):
                                    continue
                            else:
                                if now - event_datetime > timedelta(hours=2):
                                    continue
                            time_formatted = event_datetime.strftime("%H:%M")
                        except:
                            time_formatted = time_str

                        for ch in item.get("channels", []):
                            channel_name = ch.get("channel_name", "")
                            channel_id = ch.get("channel_id", "")
                            tvg_name = f"{event_title} ({time_formatted})"
                            categorized_channels[category].append({
                                "tvg_name": tvg_name,
                                "channel_name": channel_name,
                                "channel_id": channel_id,
                                "event_title": event_title,
                                "category": category
                            })

            for category, channels in categorized_channels.items():
                for ch in channels:
                    try:
                        stream = get_stream_from_channel_id(ch["channel_id"])
                        if stream:
                            live_events.append((f"{category} | {ch['tvg_name']} | {ch['channel_name']}", stream))
                    except:
                        continue

            print(f"Trovati {len(live_events)} eventi live")
        except Exception as e:
            print(f"Errore nell'estrazione degli eventi live: {e}")

    # ========== CREAZIONE FILE M3U ==========
    print("Generando file M3U unificato...")
    OUTPUT_FILE = "dlhd.m3u"
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        if live_events:
            f.write(f'#EXTINF:-1 group-title="Live Events",DADDYLIVE\n')
            f.write("https://example.com.m3u8\n\n")
            for name, url in live_events:
                f.write(f'#EXTINF:-1 group-title="Live Events",{name}\n{url}\n\n')

        if channels_247:
            for name, url in channels_247:
                f.write(f'#EXTINF:-1 group-title="DLHD 24/7",{name}\n{url}\n\n')

    total_channels = len(channels_247) + len(live_events)
    print(f"Creato file {OUTPUT_FILE} con {total_channels} canali totali.")

# ------------------- VAVOO Fonksiyonu -------------------
def vavoo_channels():
    print("Eseguendo vavoo_channels...")
    import requests
    import re

    PROXY_PREFIX = "https://pulutotv-alsancak.hf.space/proxy/m3u?url="

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
            "metadata": {"device":{"type":"Handset","os":"Android","osVersion":"10","model":"Pixel 4","brand":"Google"}}
        }
        resp = requests.post("https://vavoo.to/mediahubmx-signature.json", json=data, headers=headers, timeout=10)
        return resp.json().get("signature")

    def vavoo_groups():
        return [""]

    def clean_channel_name(name):
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
                    "language": "de","region":"AT","catalogId":"iptv","id":"iptv","adult":False,
                    "search":"","sort":"name","filter":{"group": group},"cursor":cursor,"clientVersion":"3.0.2"
                }
                resp = requests.post("https://vavoo.to/mediahubmx-catalog.json", json=data, headers=headers, timeout=10)
                r = resp.json()
                items = r.get("items", [])
                all_channels.extend(items)
                cursor = r.get("nextCursor")
                if not cursor:
                    break
        return all_channels

    def save_as_m3u(channels, filename="vavoo.m3u"):
        all_channels_flat = []
        for ch in channels:
            original_name = ch.get
