# ITCHY YouTube Downloader

Modern arayuzlu Windows masaustu uygulamasi. YouTube videolarini MP3, MP4 ve M4A formatlarinda indirmek, kuyruga almak, toplu indirmek ve indirme gecmisini takip etmek icin tasarlanmistir.

**Versiyon:** v1.4 | **Platform:** Windows | **Dil:** Python | created by M.Mert

---

## One Cikanlar

- Modern dark/light tema ve tema
- Iki kolonlu ana ekran: indirme kontrolleri solda, video onizleme ve ozet sagda
- Hazir profiller: `MP3 Muzik`, `MP4 720p`, `MP4 1080p`, `Sadece Ses`
- Analiz sonrasi video basligi, kanal, sure, izlenme ve thumbnail gosterimi
- Indirme ozeti: secilen format, kalite ve kayit klasoru
- Son indirilenler paneli
- Detayli secenekler ve islem gunlugu icin acilir/kapanir alanlar

---

## Kurulum

### Yontem 1 - Setup ile Kur (Onerilen)

En kolay yontem. Kurulum gerektiren adimlar otomatik tamamlanir.

1. [Releases](https://github.com/Bogazitchy/Itchy-YouTube-Downloader/releases) sayfasindan `ItchyDownloader_Setup.exe` dosyasini indir.
2. Kurulum sihirbazini calistir.
3. Masaustundeki kisayoldan baslat.

> Setup paketinde ffmpeg dosyalari gomulu gelir; ayrica ffmpeg kurman gerekmez.

### Yontem 2 - Kaynak Koddan Calistir

Python ile calistirmak isteyenler icin:

- Python 3.9+
- ffmpeg, ffprobe ve ffplay
- `requirements.txt` icindeki Python paketleri

ffmpeg dosyalarini [ffmpeg builds](https://github.com/BtbN/ffmpeg-builds/releases/latest) sayfasindan indirip `itchy.py` ile ayni klasore koyabilirsin.

Python bagimliliklari:

```bash
pip install -r requirements.txt
```

Manuel kurulum:

```bash
pip install yt-dlp customtkinter pillow pystray winotify pypresence
```

Calistirma:

```bash
python itchy.py
```

---

## Kullanim

1. Ana ekrandaki video linki alanina YouTube linkini yapistir.
2. `Analiz Et` butonuna bas.
3. Format ve kalite sec veya hazir profillerden birini kullan.
4. Gerekirse `Detayli secenekler` alanindan klip kesme, altyazi, kayit klasoru ve mini modu ayarla.
5. `Indir` butonuna bas.

---

## Ozellikler

### Tek Video Indirme

- MP3, MP4 ve M4A format destegi
- YouTube video, Shorts ve playlist linklerini temizleme/donusturme
- Video kalitelerini analizden sonra otomatik listeleme
- Indirme sirasinda duraklatma ve iptal etme
- Tahmini dosya boyutu gosterimi

### Hazir Profiller

- `MP3 Muzik`: yuksek kaliteli ses
- `MP4 720p`: dengeli video indirme
- `MP4 1080p`: yuksek kalite video
- `Sadece Ses`: M4A ses cikisi

### Detayli Secenekler

- Klip kesme: baslangic ve bitis zamani girerek videonun belirli bolumunu indirme
- Altyazi indirme ve dil secimi
- Indirme sonrasi klasoru otomatik acma
- Kayit klasoru secimi
- Mini mod

### Kuyruk

- Birden fazla link ekleme
- Kuyrugu sirayla indirme
- Kuyruk indirmesini durdurma
- Her satir icin durum ve ilerleme gosterimi

### Batch Indirme

- `.txt` dosyasindan link yukleme
- Metin kutusuna coklu link girme
- Secilen format ve kalite ile toplu indirme

### Gecmis ve Istatistikler

- Indirme gecmisi `history.json` dosyasina kaydedilir
- Gecmiste arama ve format filtresi
- Gecmisten tekrar indirme
- Toplam indirme sayisi, toplam boyut ve format bazli istatistikler

### Ayarlar

- Indirme hiz limiti
- yt-dlp guncelleme
- Bildirim sesi
- Sistem tepsisine kucultme
- Proxy destegi
- `cookies.txt` destegi
- Discord Rich Presence
- Otomatik yt-dlp guncelleme kontrolu

---

## Desteklenen Kaliteler

| Format | Secenekler |
| --- | --- |
| MP3 | 128, 192, 256, 320 kbps |
| M4A | 128, 192, 256 kbps |
| MP4 | 144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p |

Not: Video kaliteleri videonun YouTube tarafinda sundugu formatlara gore degisir.

---

## Windows EXE Build

1. `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` dosyalarini proje klasorune koy.
2. `build_windows.bat` dosyasini calistir.
3. Cikti `dist/ItchyDownloader/` klasorunde olusur.
4. Kurulum paketi icin Inno Setup ile `setup.iss` dosyasini derle.

---

## Dosya Yapisi

```text
itchy.py              -> Ana uygulama
requirements.txt      -> Python bagimliliklari
build_windows.bat     -> Windows build scripti
ItchyDownloader.spec  -> PyInstaller spec dosyasi
setup.iss             -> Inno Setup kurulum scripti
logo.ico              -> Uygulama ikonu
history.json          -> Indirme gecmisi
stats.json            -> Istatistikler
ffmpeg.exe            -> Medya isleme araci
ffprobe.exe           -> Medya analiz araci
ffplay.exe            -> Medya oynatici
```

---

## Notlar

- Varsayilan indirme klasoru kullanicinin `Downloads` klasorudur.
- 1080p ustu MP4 videolarda ses ve goruntu ayri inip ffmpeg ile birlestirilebilir.
- Uye girisi veya yas/dogrulama isteyen videolar icin `cookies.txt` kullanilabilir.
- EXE modunda manuel yt-dlp guncellemesi kisitli olabilir; Python modunda Ayarlar ekranindan guncelleme yapilabilir.
- Sistem tepsisi, bildirim ve Discord ozellikleri ilgili paketler yukluyse aktif olur.

---

## Lisans

MIT
