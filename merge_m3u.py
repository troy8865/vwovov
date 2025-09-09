import requests
import re

# M3U listelerinin URL'leri
URLS = [
    "https://cine10giris.org.tr/ulusaltv.m3u",
    "https://raw.githubusercontent.com/pigzillaaa/daddylive/refs/heads/main/daddylive-channels.m3u8",
    "https://raw.githubusercontent.com/ahmet21ahmet/Trgoalsvsdengetv/main/Birlesik.m3u",
]

# Çıktı dosyası
OUTPUT_FILE = "karams.m3u"

# Hiçbir kategori dışlanmayacak
EXCLUDED_CATEGORIES = set()

def get_group_title(info_line):
    match = re.search(r'group-title="([^"]+)"', info_line)
    if match:
        return match.group(1)
    return "Diğer"

def process_m3u_lists():
    categorized_channels = {}
    seen_urls = set()

    print("📥 M3U listeleri indiriliyor...\n")

    for url in URLS:
        try:
            print(f"🔗 İşleniyor: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            text = response.text.replace('\r', ' ').replace('\n', ' ')
            parts = text.split("#EXTINF:")

            for part in parts[1:]:  # İlk parçayı atla çünkü boş olur
                info_block = "#EXTINF:" + part

                # Yayın URL'sini bul
                url_match = re.search(r'(http[^\s]+)', info_block)
                if not url_match:
                    continue

                stream_url = url_match.group(1)

                # Kanal açıklama satırını al (URL'den önceki kısım)
                info_line = info_block.split(stream_url)[0].strip()

                # Kanal adı kontrolü
                if not info_line:
                    continue

                # Kategoriyi al
                category = get_group_title(info_line)

                if category in EXCLUDED_CATEGORIES or stream_url in seen_urls:
                    continue

                categorized_channels.setdefault(category, []).append((info_line, stream_url))
                seen_urls.add(stream_url)

        except requests.exceptions.RequestException as e:
            print(f"❌ Hata: {url} yüklenemedi. Detay: {e}")
        except Exception as e:
            print(f"⚠️ Beklenmedik hata: {e}")

    print("\n✅ Tüm kaynaklar işlendi. Dosya yazılıyor...\n")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")

            total_channels = 0
            for category in sorted(categorized_channels.keys()):
                channels = categorized_channels[category]
                print(f"📂 {category}: {len(channels)} kanal")
                for info, stream_url in channels:
                    f.write(f"{info}\n")
                    f.write(f"{stream_url}\n")
                    total_channels += 1

        print(f"\n🎉 Tamamlandı! Toplam {total_channels} kanal '{OUTPUT_FILE}' dosyasına yazıldı.\n")

    except IOError as e:
        print(f"❌ Dosya yazma hatası: {e}")

if __name__ == "__main__":
    process_m3u_lists()
