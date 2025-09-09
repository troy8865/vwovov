import requests
import re

# Birleştirilecek M3U listelerinin URL'leri
URLS = [
    "https://cine10giris.org.tr/ulusaltv.m3u",
    "https://raw.githubusercontent.com/pigzillaaa/daddylive/refs/heads/main/daddylive-channels.m3u8",
    "https://raw.githubusercontent.com/ahmet21ahmet/Trgoalsvsdengetv/main/Birlesik.m3u",
    
]

# Çıktı dosyasının adı
OUTPUT_FILE = "karams.m3u"

}

def get_group_title(info_line):
    """
    #EXTINF satırından grup başlığını (kategoriyi) çeker.
    """
    match = re.search(r'group-title="([^"]+)"', info_line)
    if match:
        return match.group(1)
    return "Diğer" # Kategori bulunamazsa varsayılan olarak bu kategoriye ekler

def process_m3u_lists():
    """
    URL'lerdeki M3U listelerini işler, istenmeyen kategorileri filtreler,
    birleştirir ve dosyaya yazar.
    """
    # Kanalları kategorilerine göre saklamak için bir sözlük (dictionary) yapısı
    categorized_channels = {}

    # Tekrar eden yayın URL'lerini kontrol etmek için bir set
    seen_urls = set()

    print("M3U listeleri indiriliyor ve işleniyor...")

    for url in URLS:
        try:
            print(f"-> {url} işleniyor...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()  # HTTP hatası varsa programı durdurur

            # İçeriği satırlara ayır
            lines = response.text.splitlines()

            # Satırları gezerek kanal bilgilerini ve URL'sini al
            for i in range(len(lines)):
                if lines[i].startswith("#EXTINF:"):
                    info_line = lines[i]

                    # Sonraki satırın yayın URL'si olduğunu varsayalım
                    if i + 1 < len(lines) and lines[i+1].strip().startswith("http"):
                        stream_url = lines[i+1].strip()

                        # Eğer bu yayın URL'si daha önce eklenmediyse işle
                        if stream_url not in seen_urls:
                            # Kategoriyi al
                            category = get_group_title(info_line)

                            # YENİ EKLENTİ: Kategori dışlama listesinde mi kontrol et
                            if category in EXCLUDED_CATEGORIES:
                                continue # Bu kategoriyi atla ve bir sonraki kanala geç

                            # Kanal bilgisini ve URL'sini bir demet (tuple) olarak sakla
                            channel_data = (info_line, stream_url)

                            # Eğer bu kategori daha önce oluşturulmadıysa, oluştur
                            if category not in categorized_channels:
                                categorized_channels[category] = []

                            # Kanalı ilgili kategoriye ekle
                            categorized_channels[category].append(channel_data)

                            # Yayın URL'sini görülenlere ekle
                            seen_urls.add(stream_url)

        except requests.exceptions.RequestException as e:
            print(f"Hata: {url} adresine ulaşılamadı. Hata detayı: {e}")
        except Exception as e:
            print(f"Beklenmedik bir hata oluştu: {e}")

    print("\nListeler birleştirildi ve filtrelendi. Şimdi dosya oluşturuluyor...")

    # Kategorileri alfabetik olarak sırala
    sorted_categories = sorted(categorized_channels.keys())

    # Sonuçları dosyaya yaz
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n") # M3U dosyasının başlangıç etiketi

            total_channels = 0
            for category in sorted_categories:
                channels_in_category = categorized_channels[category]
                if channels_in_category:
                    f.write("\n")
                    print(f"-> '{category}' kategorisinde {len(channels_in_category)} kanal bulundu.")
                    for info, url in channels_in_category:
                        f.write(f"{info}\n")
                        f.write(f"{url}\n")
                        total_channels += 1

        print(f"\nİşlem tamamlandı! Toplam {len(sorted_categories)} kategori ve {total_channels} benzersiz kanal '{OUTPUT_FILE}' dosyasına kaydedildi.")
        print(f"Dışlanan kategoriler: {', '.join(EXCLUDED_CATEGORIES)}")

    except IOError as e:
        print(f"Dosya yazma hatası: {e}")


if __name__ == "__main__":
    process_m3u_lists()
