import os
import requests
from urllib.parse import urlparse, parse_qs

# Qaynaq linkləri (istədiyin qədər əlavə edə bilərsən)
source_urls = [

"http://158.101.222.193:88/georgia_play.php?id=viasatexp",
"http://158.101.222.193:88/georgia_play.php?id=viasathist",
"http://158.101.222.193:88/georgia_play.php?id=viasatnat",
"http://158.101.222.193:88/georgia_play.php?id=viasatsport",
"http://158.101.222.193:88/georgia_play.php?id=setanta_georgia",
"http://158.101.222.193:88/georgia_play.php?id=setanta_sports_3",
"http://158.101.222.193:88/georgia_play.php?id=setanta_sports_plus_georgia",
"http://158.101.222.193:88/georgia_play.php?id=silk_sport4",
"https://www.elahmad.com/tv/live/channels.php?id=213",
"https://www.elahmad.com/tv/canlitvizle.php?id=duzcetv",

]

# Faylların yazılacağı qovluq
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

def extract_m3u8(url):
    try:
        kanal_adi = parse_qs(urlparse(url).query).get("id", ["stream"])[0]
        filename = f"{kanal_adi}.m3u8"
        file_path = os.path.join(output_folder, filename)

        response = requests.get(url)
        response.raise_for_status()
        lines = response.text.splitlines()

        modified = "#EXTM3U\n#EXT-X-VERSION:3\n"
        for line in lines:
            if line.strip() and not line.startswith("#"):
                full_url = f"http://tbs01-edge17.itdc.ge/{kanal_adi}/{line.strip()}"
                modified += f"#EXT-X-STREAM-INF:BANDWIDTH=2085600,RESOLUTION=1280x720\n{full_url}\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified)

        print(f"✅ {filename} yaradıldı.")
    except Exception as e:
        print(f"❌ {url} üçün xəta: {e}")

if __name__ == "__main__":
    for url in source_urls:
        extract_m3u8(url)
