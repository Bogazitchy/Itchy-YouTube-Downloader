# ITCHY YouTube Downloader

```
  ##    ######   #####  ##  ##  ##  ##
  ##      ##    ##      ##  ##   ## # 
  ##      ##    ##      ######    ##  
  ##      ##    ##      ##  ##    ##  
  ##      ##     #####  ##  ##    ##  
```

**Versiyon:** v1.3 | **Platform:** Windows | created by M.Mert

YouTube'dan MP3, MP4 ve M4A indiren, retro terminal tasarımlı masaüstü uygulaması.

---

## Kurulum

### Yöntem 1 — Setup ile Kur (Önerilen)

En kolay yöntem. Kurulum gerektiren tüm adımlar otomatik tamamlanır.

1. [Releases](https://github.com/Bogazitchy/Itchy-YouTube-Downloader/releases) sayfasından `ItchyDownloader_Setup.exe` dosyasını indir
2. Kurulum sihirbazını çalıştır
3. Masaüstündeki kısayoldan başlat

> ffmpeg kurulum gerektirmez, setup içinde gömülü gelir.

---

### Yöntem 2 — Kaynak Koddan Çalıştır

Python ile çalıştırmak isteyenler için.

**Gereksinimler:**
- Python 3.9+
- ffmpeg

**1. ffmpeg kur:**

[github.com/BtbN/ffmpeg-builds/releases](https://github.com/BtbN/ffmpeg-builds/releases/latest) adresinden `ffmpeg-master-latest-win64-gpl.zip` dosyasını indir, içindeki `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` dosyalarını `itchy.py` ile aynı klasöre koy.

**2. Python paketlerini kur:**

```bash
pip install -r requirements.txt
```

**3. Çalıştır:**

```bash
python itchy.py
```

---

## Özellikler

| Özellik | Açıklama |
|---------|----------|
| MP3 / MP4 / M4A | 128 kbps'den 4K'ya kalite seçimi |
| Klip Kesme | Başlangıç–bitiş zamanı girerek bölüm indir |
| Altyazı | 8 dil seçeneği ile .srt indirme |
| Queue | Birden fazla linki sırayla otomatik indir |
| Batch | .txt dosyasından toplu indirme |
| Geçmiş | Tüm indirmeler kayıtlı, tek tıkla tekrar indir |
| Mini Mod | Küçük pencere modu |
| Discord RPC | İndirme sırasında Discord status |
| Proxy & Cookie | Kısıtlı içeriklere erişim |
| Tema | Karanlık / Aydınlık mod |

---

## Desteklenen Kaliteler

| Format | Seçenekler |
|--------|------------|
| MP3 | 128, 192, 256, 320 kbps |
| M4A | 128, 192, 256 kbps |
| MP4 | 144p → 4K |

---

## Lisans

MIT
