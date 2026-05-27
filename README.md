# ITCHY YouTube Downloader

<p align="center">
  <img src="modern_app/src/assets/itchy-logo.png" alt="ITCHY Downloader Logo" width="520">
</p>

Modern, glass efektli Windows masaustu YouTube indirme uygulamasi. ITCHY; YouTube videolarini MP3, MP4 ve M4A formatlarinda analiz etmek, kalite secmek, indirmek, kuyruga almak, gecmisi ve istatistikleri takip etmek icin tasarlanmistir.

**Versiyon:** v2.0 | **Platform:** Windows | **Modern UI:** Electron + React | **Indirme motoru:** Python + yt-dlp | created by M.Mert

---

## One Cikanlar

- Logo ile uyumlu yesil modern tema, dark/light mod ve glass efektli arayuz
- Yeni ITCHY Downloader logosu ve genisletilmis marka alani
- Calisan sol navigasyon: `Indir`, `Kuyruk`, `Gecmis`, `Istatistik`, `Ayarlar`
- Modern, yuvarlak kenarli custom dropdown menuleri
- Dropdown menulerinin kartlarin arkasinda kalmasini engelleyen ust katman sistemi
- Format degisince kalite listesinin otomatik yenilenmesi
- Video analizinden sonra thumbnail icin yedekli gorsel yukleme
- Iki kolonlu ana ekran: indirme kontrolleri solda, video onizleme ve ozet sagda
- Hazir profiller: `MP3 Muzik`, `MP4 720p`, `MP4 1080p`, `Sadece Ses`
- Indirme ozeti, son indirilenler, islem gunlugu ve istatistik panelleri
- Python worker sayesinde arayuzden bagimsiz analiz/indirme altyapisi

---

## Kurulum

### Yontem 1 - Setup ile Kur

1. [Releases](https://github.com/Bogazitchy/Itchy-YouTube-Downloader/releases) sayfasindan `Itchy YouTube Downloader Setup 2.0.0.exe` dosyasini indir.
2. Kurulum sihirbazini calistir.
3. Masaustu veya Baslat Menusu kisayolundan uygulamayi ac.

> Modern setup paketinde Python worker ve ffmpeg dosyalari gomulu gelir; ekstra ffmpeg kurulumu gerekmez.

### Yontem 2 - Kaynak Koddan Calistir

Gerekenler:

- Python 3.9+
- Node.js 20+
- `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`
- `requirements.txt` icindeki Python paketleri

Python bagimliliklari:

```bash
pip install -r requirements.txt
```

Modern masaustu arayuzunu gelistirme modunda calistirma:

```bash
cd modern_app
npm install
npm run desktop
```

Windows installer paketi alma:

```bash
cd modern_app
npm run package
```

Cikti `dist-modern/` klasorune olusur.

---

## Kullanim

1. `Video linki` alanina YouTube linkini yapistir.
2. `Analiz Et` butonuna bas.
3. Format sec: `MP3`, `MP4` veya `M4A`.
4. Kalite listesinden uygun secenegi sec veya hazir profillerden birini kullan.
5. Gerekirse `Detayli secenekler` alanindan klip kesme, altyazi dili ve kayit klasorunu ayarla.
6. `Indir` butonuna bas.

Format degistirdiginde kalite listesi yeni formata gore temizlenir ve link varsa otomatik yeniden analiz edilir.

---

## Modern Desktop Mimarisi

```text
modern_app/             -> Electron + React modern arayuz
modern_app/src/assets/  -> UI gorselleri ve ITCHY logosu
python_core/worker.py   -> JSON tabanli Python analiz/indirme worker'i
itchy.py                -> Eski CustomTkinter surumu, geriye donuk olarak korunur
```

Electron arayuz, Python worker ile JSON olaylari uzerinden haberlesir. Bu sayede indirme motoru arayuzden bagimsiz kalir.

---

## Ozellikler

### Tek Video Indirme

- MP3, MP4 ve M4A format destegi
- YouTube video ve Shorts linklerini temizleme/donusturme
- Video kalitelerini analizden sonra otomatik listeleme
- Tahmini dosya boyutu gosterimi
- Indirme ilerlemesi ve islem gunlugu

### Modern Arayuz

- Glass efektli kartlar
- Logo ile uyumlu yesil tema
- Dark/light tema destegi
- Sol navigasyon sekmeleri
- Yuvarlak kenarli custom dropdown menuleri
- Thumbnail onizleme ve fallback thumbnail sistemi

### Hazir Profiller

- `MP3 Muzik`: yuksek kaliteli ses
- `MP4 720p`: dengeli video indirme
- `MP4 1080p`: yuksek kalite video
- `Sadece Ses`: M4A ses cikisi

### Detayli Secenekler

- Klip kesme: baslangic ve bitis zamani girerek belirli bolumu indirme
- Altyazi indirme
- Altyazi dili secimi
- Varsayilan veya ozel kayit klasoru

### Kuyruk, Gecmis ve Istatistik

- Kuyruga birden fazla link ekleme
- Kuyrugu sirayla indirme
- Indirme gecmisini `history.json` dosyasinda saklama
- Format bazli indirme istatistikleri

---

## Desteklenen Kaliteler

| Format | Secenekler |
| --- | --- |
| MP3 | 128, 192, 256, 320 kbps |
| M4A | 128, 192, 256 kbps |
| MP4 | 144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p |

Not: Video kaliteleri YouTube'un ilgili video icin sundugu formatlara gore degisir.

---

## v2.0 Guncellemeleri

- Uygulama surumu v2.0 olarak guncellendi.
- Yeni ITCHY Downloader logosu arayuze ve README'ye eklendi.
- Tema, logonun yesil marka rengine gore yeniden ayarlandi.
- Logo gorseli kirpildi ve sol marka alanina daha buyuk yerlestirildi.
- Sol menu sekmeleri gercek sayfalara baglandi.
- Native dropdownlar modern custom dropdownlar ile degistirildi.
- Dropdownlarin kartlarin arkasinda kalma sorunu portal katmani ile giderildi.
- Format degisince kalite listesinin eski formattan kalma sorunu duzeltildi.
- Thumbnail gorunmeme sorunu icin yedekli thumbnail sistemi eklendi.
- Kurulum paketi kullanici bazli kurulumla acilacak sekilde duzenlendi.

---

## Dosya Yapisi

```text
itchy.py                 -> Eski Python/CustomTkinter uygulamasi
requirements.txt         -> Python bagimliliklari
build_windows.bat        -> Eski Python UI icin Windows build scripti
ItchyDownloader.spec     -> PyInstaller spec dosyasi
modern_app/              -> Modern React/Electron desktop kabugu
python_core/             -> Arayuzden bagimsiz Python worker
setup.iss                -> Eski Inno Setup kurulum scripti
logo.ico                 -> Uygulama ikonu
history.json             -> Indirme gecmisi
stats.json               -> Istatistikler
ffmpeg.exe               -> Medya isleme araci
ffprobe.exe              -> Medya analiz araci
ffplay.exe               -> Medya oynatici
```

---

## Lisans

MIT
