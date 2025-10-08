import requests
import re

# Birleştirilecek M3U listelerinin URL'leri
URLS = [
    "https://tinyurl.com/2ao2rans",
    "https://raw.githubusercontent.com/Lunedor/iptvTR/refs/heads/main/FilmArsiv.m3u",
    "https://dl.dropbox.com/scl/fi/dj74gt6awxubl4yqoho07/github.m3u?rlkey=m7pzzvk27d94bkfl9a98tluai",
    "https://raw.githubusercontent.com/Lunedor/iptvTR/refs/heads/main/FilmArsiv.m3u",
    "https://raw.githubusercontent.com/Zerk1903/zerkfilm/refs/heads/main/Filmler.m3u",
]

# Çıktı dosyasının adı
OUTPUT_FILE = "karams.m3u"

# Dışlanacak kategori yok, tüm kanallar dahil edilecek
EXCLUDED_CATEGORIES = set()

def get_group_title(info_line):
    """
    #EXTINF satırından grup başlığını (kategoriyi) çeker.
    """
    match = re.search(r'group-title="([^"]+)"', info_line)
    if match:
        return match.group(1)
    return "Diğer"  # Kategori bulunamazsa varsayılan olarak

def process_m3u_lists():
    """
    URL'lerdeki M3U listelerini işler, birleştirir ve .m3u dosyasına yazar.
    """
    categorized_channels = {}  # Kategoriye göre kanalları tutar
    seen_urls = set()  # Aynı yayını tekrar eklememek için

    print("M3U listeleri indiriliyor ve işleniyor...\n")

    for url in URLS:
        try:
            print(f"-> {url} işleniyor...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            lines = response.text.splitlines()

            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF:"):
                    info_line = lines[i]

                    if i + 1 < len(lines) and lines[i+1].strip().startswith("http"):
                        stream_url = lines[i+1].strip()

                        if stream_url not in seen_urls:
                            category = get_group_title(info_line)

                            # Kategori dışlama kontrolü (boş olduğundan tümü geçer)
                            if category in EXCLUDED_CATEGORIES:
                                continue

                            channel_data = (info_line, stream_url)

                            if category not in categorized_channels:
                                categorized_channels[category] = []

                            categorized_channels[category].append(channel_data)
                            seen_urls.add(stream_url)

        except requests.exceptions.RequestException as e:
            print(f"Hata: {url} alınamadı. Hata detayı: {e}")
        except Exception as e:
            print(f"Beklenmedik bir hata oluştu: {e}")

    print("\n✔️ Tüm listeler işlendi. Şimdi dosya yazılıyor...\n")

    # Kategorileri alfabetik sırala
    sorted_categories = sorted(categorized_channels.keys())

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")

            total_channels = 0
            for category in sorted_categories:
                channels = categorized_channels[category]
                if channels:
                    f.write("\n")
                    print(f"📂 '{category}' kategorisinde {len(channels)} kanal bulundu.")
                    for info, url in channels:
                        f.write(f"{info}\n")
                        f.write(f"{url}\n")
                        total_channels += 1

        print(f"\n✅ Tamamlandı! Toplam {total_channels} kanal '{OUTPUT_FILE}' dosyasına kaydedildi.\n")

    except IOError as e:
        print(f"❌ Dosya yazma hatası: {e}")

if __name__ == "__main__":
    process_m3u_lists()
