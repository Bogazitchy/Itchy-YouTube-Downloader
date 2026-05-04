# ITCHY YouTube Downloader

YouTube'dan MP3, MP4 ve M4A indiren, retro terminal tasarımlı masaüstü uygulaması.

**Versiyon:** v0.3 Beta | **Platform:** Windows | **Dil:** Python

---

## Kurulum

### 1. Gereksinimler

- Python 3.9+
- ffmpeg (ses/video işleme için zorunlu)
- pip paketleri (bkz. requirements.txt)

### ffmpeg Kurulumu

**Windows:**
1. https://github.com/BtbN/ffmpeg-builds/releases/latest adresine git
2. `ffmpeg-master-latest-win64-gpl.zip` dosyasını indir
3. İçinden `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` dosyalarını `itchy.py` ile aynı klasöre koy

**Arch/CachyOS:**
```bash
sudo pacman -S ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

---

### 2. Python Bağımlılıkları

```bash
pip install -r requirements.txt
```

Ya da manuel:

```bash
pip install yt-dlp customtkinter pillow pystray
```

---

### 3. Çalıştırma

```bash
python itchy.py
```

---

## Windows EXE Build (Kurulum Sihirbazı)

1. `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` dosyalarını klasöre koy
2. `build_windows.bat` dosyasını çalıştır
3. `dist/ItchyDownloader/` klasöründe EXE oluşur
4. Inno Setup ile `setup.iss` dosyasını derle → tek tıkla kurulum sihirbazı

---

## Özellikler

### İndirme
- MP3, MP4, M4A format desteği
- MP3: 128 / 192 / 256 / 320 kbps
- MP4: 144p'den 4K'ya kadar (videoda mevcut kaliteler otomatik listelenir)
- Shorts, playlist ve normal video linkleri desteklenir
- İndirme sırasında duraklatma ve iptal etme
- İndirme hız limiti (MB/s)

### Klip Kesme
- Başlangıç ve bitiş zamanı girerek videonun yalnızca istenen bölümünü indir
- Format: `HH:MM:SS`

### Altyazı
- Video ile birlikte `.srt` altyazı indir
- 8 dil seçeneği: TR, EN, DE, FR, ES, JA, KO, AR

### Queue (Kuyruk)
- Birden fazla link ekle, sırayla otomatik indir
- Format ve kalite her kuyruk için ayrı seçilebilir

### Batch İndirme
- Metin kutusuna birden fazla link yaz veya `.txt` dosyası yükle
- Tamamı otomatik sırayla indirilir

### İndirme Geçmişi
- Her indirme otomatik kaydedilir (`history.json`)
- Geçmiş sekmesinden tek tıkla tekrar indir

### İstatistikler
- Toplam indirme sayısı ve boyutu
- Format bazlı dağılım (MP3 / MP4 / M4A)

### Sistem Tepsisi
- Küçültünce arka planda çalışmaya devam eder
- İndirme tamamlanınca bildirim ve ses uyarısı

### Mini Mod
- Tek tıkla küçük pencereye geçiş
- `[↑]` butonu ile tam ekrana geri dön

### Proxy & Cookie
- HTTP/SOCKS5 proxy desteği
- Üye girişi gerektiren videolar için `cookies.txt` desteği

### Tema
- Karanlık mod: turuncu-gri retro terminal
- Aydınlık mod: mavi-beyaz

---

## Desteklenen Kaliteler

| Format | Seçenekler |
|--------|------------|
| MP3    | 128, 192, 256, 320 kbps |
| M4A    | 128, 192, 256 kbps |
| MP4    | 144p, 240p, 360p, 480p, 720p, 1080p, 1440p (2K), 2160p (4K) |

> Mevcut kaliteler videoya göre değişir; yalnızca videoda bulunan kaliteler listelenir.

---

## Dosya Yapısı

```
itchy.py              → Ana uygulama
requirements.txt      → Python bağımlılıkları
build_windows.bat     → Windows EXE build scripti
setup.iss             → Inno Setup kurulum sihirbazı scripti
logo.ico              → Uygulama ikonu
history.json          → İndirme geçmişi (otomatik oluşur)
stats.json            → İstatistikler (otomatik oluşur)
```

---

## Notlar

- İndirilen dosyalar varsayılan olarak `~/Downloads` klasörüne kaydedilir.
- 1080p üstü MP4 videolarda ses ve görüntü ayrı indirilip ffmpeg ile birleştirilir.
- `yt-dlp` YouTube değişikliklerine karşı Ayarlar sekmesinden güncellenebilir.
- `pystray` paketi sistem tepsisi özelliği için gereklidir; yoksa özellik devre dışı kalır.

---

*created by M.Mert*