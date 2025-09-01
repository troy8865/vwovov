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
        return [""]

    def clean_channel_name(name):
        return re.sub(r'\s*\.(a|b|c|s|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|t|u|v|w|x|y|z)\s*$', '', name, flags=re.IGNORECASE).strip()

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

    def save_as_m3u(channels, filename="vavoo.m3u"):
        all_channels_flat = []
        for ch in channels:
            name = clean_channel_name(ch.get("name", "SenzaNome"))
            url = ch.get("url", "")
            category = ch.get("group", "Generale")
            if url:
                all_channels_flat.append({"name": name, "url": url, "category": category})

        # Rinomina duplicati
        name_counts = {}
        for ch in all_channels_flat:
            name_counts[ch["name"]] = name_counts.get(ch["name"], 0) + 1

        final_channels = []
        name_counter = {}
        for ch in all_channels_flat:
            name = ch["name"]
            if name_counts[name] > 1:
                if name not in name_counter:
                    name_counter[name] = 1
                    new_name = name
                else:
                    name_counter[name] += 1
                    new_name = f"{name} ({name_counter[name]})"
            else:
                new_name = name
            final_channels.append({"name": new_name, "url": ch["url"], "category": ch["category"]})

        # Gruplama per categoria
        channels_by_category = {}
        for ch in final_channels:
            cat = ch["category"]
            if cat not in channels_by_category:
                channels_by_category[cat] = []
            channels_by_category[cat].append((ch["name"], ch["url"]))

        # Scrittura M3U con proxy
        with open(filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for cat in sorted(channels_by_category.keys()):
                f.write(f"\n# {cat.upper()}\n")
                for name, url in sorted(channels_by_category[cat], key=lambda x: x[0].lower()):
                    proxy_url = f"{PROXY_PREFIX}{url}"
                    f.write(f'#EXTINF:-1 group-title="{cat} VAVOO",{name}\n{proxy_url}\n')

        print(f"Playlist M3U salvata in: {filename}")
        print(f"Canali organizzati in {len(channels_by_category)} categorie:")
        for cat, ch_list in channels_by_category.items():
            print(f"  - {cat}: {len(ch_list)} canali")

    # Esecuzione
    channels = get_channels()
    print(f"Trovati {len(channels)} canali. Creo la playlist M3U con i link proxy...")
    save_as_m3u(channels)
