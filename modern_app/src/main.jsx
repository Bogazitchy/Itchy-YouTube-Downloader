import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  Download,
  FileAudio,
  FileVideo,
  Folder,
  History,
  ListPlus,
  Moon,
  Music2,
  Play,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  Sun,
  Trash2,
} from 'lucide-react';
import './styles.css';
import itchyLogo from './assets/itchy-logo.png';

const api = window.itchy;

const profiles = [
  { id: 'music', label: 'MP3 Muzik', mode: 'mp3', quality: '320k', icon: Music2 },
  { id: 'balanced', label: 'MP4 720p', mode: 'mp4', quality: '720p', icon: FileVideo },
  { id: 'fullhd', label: 'MP4 1080p', mode: 'mp4', quality: '1080p', icon: Sparkles },
  { id: 'audio', label: 'Sadece Ses', mode: 'm4a', quality: '256k', icon: FileAudio },
];

const navItems = [
  { id: 'download', label: 'Indir', icon: Download },
  { id: 'queue', label: 'Kuyruk', icon: ListPlus },
  { id: 'history', label: 'Gecmis', icon: History },
  { id: 'stats', label: 'Istatistik', icon: BarChart3 },
  { id: 'settings', label: 'Ayarlar', icon: Settings },
];

const subtitleLanguages = ['tr', 'en', 'de', 'fr', 'es', 'ja', 'ko', 'ar'].map((lang) => ({
  value: lang,
  label: lang.toUpperCase(),
}));

function formatViews(value) {
  if (!value) return '-';
  return new Intl.NumberFormat('tr-TR').format(value);
}

function thumbnailCandidates(video) {
  if (!video) return [];
  return [
    video.thumbnail,
    video.id ? `https://i.ytimg.com/vi/${video.id}/maxresdefault.jpg` : '',
    video.id ? `https://i.ytimg.com/vi/${video.id}/hqdefault.jpg` : '',
  ].filter(Boolean);
}

function SoftSelect({ value, options, onChange, placeholder }) {
  const [open, setOpen] = useState(false);
  const [menuBox, setMenuBox] = useState(null);
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  const selected = options.find((item) => item.value === value) || options[0];

  useEffect(() => {
    if (!open) return undefined;
    const close = (event) => {
      if (!rootRef.current?.contains(event.target) && !menuRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, [open]);

  useEffect(() => {
    if (!open) return undefined;
    const updatePosition = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      setMenuBox({ left: rect.left, top: rect.bottom + 8, width: rect.width });
    };
    updatePosition();
    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition, true);
    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition, true);
    };
  }, [open]);

  function toggleMenu() {
    const rect = triggerRef.current?.getBoundingClientRect();
    if (rect) setMenuBox({ left: rect.left, top: rect.bottom + 8, width: rect.width });
    setOpen((current) => !current);
  }

  const menu = open && menuBox && createPortal(
    <div
      className="soft-select-menu"
      ref={menuRef}
      style={{ left: menuBox.left, top: menuBox.top, width: menuBox.width }}
    >
      {options.map((item) => (
        <button
          type="button"
          key={item.value}
          className={item.value === value ? 'soft-select-option selected' : 'soft-select-option'}
          onClick={() => {
            onChange(item.value);
            setOpen(false);
          }}
        >
          {item.label}
        </button>
      ))}
    </div>,
    document.body,
  );

  return (
    <div className="soft-select" ref={rootRef}>
      <button type="button" className="soft-select-trigger" ref={triggerRef} onClick={toggleMenu}>
        <span>{selected?.label || placeholder}</span>
        <ChevronDown size={17} className={open ? 'rotated' : ''} />
      </button>
      {menu}
    </div>
  );
}

function App() {
  const [theme, setTheme] = useState('dark');
  const [activePage, setActivePage] = useState('download');
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState('mp4');
  const [quality, setQuality] = useState('');
  const [qualities, setQualities] = useState([]);
  const [video, setVideo] = useState(null);
  const [status, setStatus] = useState('Sistem hazir');
  const [progress, setProgress] = useState({ value: 0, percent: '' });
  const [log, setLog] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [isBusy, setIsBusy] = useState(false);
  const [clipEnabled, setClipEnabled] = useState(false);
  const [clipStart, setClipStart] = useState('');
  const [clipEnd, setClipEnd] = useState('');
  const [subtitle, setSubtitle] = useState(false);
  const [subLang, setSubLang] = useState('tr');
  const [outputDir, setOutputDir] = useState('');
  const [queueUrl, setQueueUrl] = useState('');
  const [queueItems, setQueueItems] = useState([]);
  const [queueRunning, setQueueRunning] = useState(false);
  const [thumbnailIndex, setThumbnailIndex] = useState(0);

  const addLog = (message) => {
    setLog((items) => [`${new Date().toLocaleTimeString('tr-TR')}  ${message}`, ...items].slice(0, 80));
  };

  const selectedQuality = useMemo(() => {
    if (quality) return quality;
    return qualities[0]?.label || '';
  }, [quality, qualities]);

  const qualityOptions = useMemo(() => {
    const list = qualities.length ? qualities : [{ label: quality || '-- URL GIRIN --' }];
    return list.map((item) => ({ value: item.label, label: item.label }));
  }, [qualities, quality]);

  const thumbnails = useMemo(() => thumbnailCandidates(video), [video]);
  const thumbnailSrc = thumbnails[thumbnailIndex] || '';

  async function refreshSideData() {
    try {
      const [historyResult, statsResult] = await Promise.all([
        api.runWorker('history', {}),
        api.runWorker('stats', {}),
      ]);
      setHistory(historyResult.records || []);
      setStats(statsResult.stats || null);
    } catch (error) {
      addLog(`Veri okunamadi: ${error.message}`);
    }
  }

  useEffect(() => {
    refreshSideData();
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  async function analyze(nextMode = mode, preferredQuality = '') {
    if (!url.trim()) {
      addLog('URL bos olamaz.');
      return;
    }
    setIsBusy(true);
    setStatus('Video analiz ediliyor');
    setProgress({ value: 0, percent: '' });
    try {
      const result = await api.runWorker('analyze', { url, mode: nextMode });
      setVideo(result);
      setThumbnailIndex(0);
      setQualities(result.qualities || []);
      const preferred = (result.qualities || []).find((item) => item.label.startsWith(preferredQuality));
      setQuality(preferred?.label || result.selectedQuality || result.qualities?.[0]?.label || '');
      setStatus('Video hazir');
      addLog(`Analiz tamamlandi: ${result.title}`);
    } catch (error) {
      setStatus('Analiz basarisiz');
      addLog(`Hata: ${error.message}`);
    } finally {
      setIsBusy(false);
    }
  }

  async function downloadFrom(link, nextMode = mode, nextQuality = selectedQuality) {
    await api.runWorker(
      'download',
      {
        url: link,
        mode: nextMode,
        quality: nextQuality,
        outdir: outputDir,
        clipStart: clipEnabled ? clipStart : '',
        clipEnd: clipEnabled ? clipEnd : '',
        subtitle,
        subLang,
      },
      (event) => {
        if (event.event === 'status') {
          setStatus(event.message);
          addLog(event.message);
        }
        if (event.event === 'progress') {
          setProgress({ value: event.progress || 0, percent: event.percent || '' });
          if (event.status) setStatus(event.status);
        }
        if (event.event === 'done') {
          setStatus('Indirme tamamlandi');
          addLog('Indirme tamamlandi.');
        }
      },
    );
  }

  async function startDownload() {
    if (!video || !url.trim()) {
      addLog('Once videoyu analiz et.');
      return;
    }
    setIsBusy(true);
    setProgress({ value: 0, percent: '' });
    setStatus('Indirme baslatiliyor');
    try {
      await downloadFrom(url);
      await refreshSideData();
    } catch (error) {
      setStatus('Indirme basarisiz');
      addLog(`Hata: ${error.message}`);
    } finally {
      setIsBusy(false);
    }
  }

  function applyProfile(profile) {
    setMode(profile.mode);
    if (video) {
      analyze(profile.mode, profile.quality);
    } else {
      setQuality(profile.quality);
    }
  }

  function changeMode(nextMode) {
    if (nextMode === mode) return;
    setMode(nextMode);
    setQuality('');
    setQualities([]);
    if (url.trim()) {
      analyze(nextMode);
    }
  }

  function addQueueItem() {
    const link = queueUrl.trim();
    if (!link) return;
    setQueueItems((items) => [
      ...items,
      { id: `${Date.now()}-${items.length}`, url: link, mode, quality: selectedQuality || quality || 'best', status: 'Bekliyor' },
    ]);
    setQueueUrl('');
  }

  async function runQueue() {
    if (queueItems.length === 0 || queueRunning) return;
    setQueueRunning(true);
    setIsBusy(true);
    try {
      for (const item of queueItems) {
        setQueueItems((items) => items.map((entry) => (entry.id === item.id ? { ...entry, status: 'Indiriliyor' } : entry)));
        setStatus('Kuyruk indiriliyor');
        await downloadFrom(item.url, item.mode, item.quality);
        setQueueItems((items) => items.map((entry) => (entry.id === item.id ? { ...entry, status: 'Tamamlandi' } : entry)));
      }
      await refreshSideData();
    } catch (error) {
      setStatus('Kuyruk durdu');
      addLog(`Kuyruk hatasi: ${error.message}`);
    } finally {
      setQueueRunning(false);
      setIsBusy(false);
    }
  }

  const downloadPage = (
    <div className="main-grid">
      <section className="left-column">
        <div className="glass-card input-card">
          <label>Video linki</label>
          <div className="url-row">
            <Search size={20} />
            <input
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && analyze()}
              placeholder="youtube.com/watch?v=..."
            />
            <button disabled={isBusy} onClick={() => analyze()}>{isBusy ? 'Bekle' : 'Analiz Et'}</button>
          </div>
        </div>

        <div className="profile-grid">
          {profiles.map((profile) => {
            const Icon = profile.icon;
            return (
              <button key={profile.id} className="profile-card" onClick={() => applyProfile(profile)}>
                <Icon size={20} />
                <span>{profile.label}</span>
              </button>
            );
          })}
        </div>

        <div className="control-grid">
          <div className="glass-card">
            <label>Format</label>
            <div className="segmented">
              {['mp3', 'mp4', 'm4a'].map((item) => (
                <button key={item} className={mode === item ? 'selected' : ''} onClick={() => changeMode(item)}>
                  {item.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="glass-card">
            <label>Kalite</label>
            <SoftSelect value={selectedQuality} options={qualityOptions} onChange={setQuality} placeholder="Kalite sec" />
          </div>
        </div>

        <details className="glass-card advanced">
          <summary>Detayli secenekler</summary>
          <div className="advanced-grid">
            <label className="check-row">
              <input type="checkbox" checked={clipEnabled} onChange={(e) => setClipEnabled(e.target.checked)} />
              Klip kesme
            </label>
            <input value={clipStart} onChange={(e) => setClipStart(e.target.value)} placeholder="Baslangic 00:00:00" />
            <input value={clipEnd} onChange={(e) => setClipEnd(e.target.value)} placeholder="Bitis 00:00:00" />
            <label className="check-row">
              <input type="checkbox" checked={subtitle} onChange={(e) => setSubtitle(e.target.checked)} />
              Altyazi indir
            </label>
            <SoftSelect value={subLang} options={subtitleLanguages} onChange={setSubLang} placeholder="Dil" />
            <div className="folder-row">
              <Folder size={18} />
              <input value={outputDir} onChange={(e) => setOutputDir(e.target.value)} placeholder="Varsayilan Downloads klasoru" />
            </div>
          </div>
        </details>

        <div className="download-card">
          <button className="primary-download" disabled={isBusy || !video} onClick={startDownload}>
            <Download size={22} />
            Indir
          </button>
          <div className="progress-track">
            <div style={{ width: `${Math.round((progress.value || 0) * 100)}%` }} />
          </div>
          <span>{progress.percent || 'Hazir'}</span>
        </div>
      </section>

      <section className="right-column">
        <div className="glass-card preview-card">
          <div className="thumbnail">
            {thumbnailSrc ? (
              <img
                src={thumbnailSrc}
                alt=""
                onError={() => setThumbnailIndex((index) => (index + 1 < thumbnails.length ? index + 1 : index))}
              />
            ) : (
              <Play size={46} />
            )}
          </div>
          <h2>{video?.title || 'URL girip analiz edin'}</h2>
          <p>{video ? `${video.channel} - ${video.duration} - ${formatViews(video.views)} izlenme` : 'Video bilgileri burada gorunecek.'}</p>
        </div>

        <div className="glass-card summary-card">
          <h3>Indirme ozeti</h3>
          <dl>
            <dt>Format</dt><dd>{mode.toUpperCase()}</dd>
            <dt>Kalite</dt><dd>{selectedQuality || '-'}</dd>
            <dt>Tahmini boyut</dt><dd>{video?.estimatedSize || '-'}</dd>
            <dt>Kayit</dt><dd>{outputDir || 'Downloads'}</dd>
          </dl>
        </div>

        <RecentDownloads history={history} />
        <LogPanel log={log} />
      </section>
    </div>
  );

  const queuePage = (
    <section className="page-panel">
      <div className="page-head">
        <div>
          <h2>Kuyruk</h2>
          <p>Birden fazla linki siraya alip ayni ayarlarla indirebilirsin.</p>
        </div>
        <button className="soft-action" disabled={queueRunning || queueItems.length === 0} onClick={runQueue}>
          <Download size={18} />
          Kuyrugu Baslat
        </button>
      </div>
      <div className="glass-card input-card">
        <label>Kuyruga link ekle</label>
        <div className="url-row">
          <Plus size={20} />
          <input
            value={queueUrl}
            onChange={(event) => setQueueUrl(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && addQueueItem()}
            placeholder="youtube.com/watch?v=..."
          />
          <button onClick={addQueueItem}>Ekle</button>
        </div>
      </div>
      <div className="queue-list">
        {queueItems.length === 0 && <div className="empty-state">Kuyrukta link yok.</div>}
        {queueItems.map((item) => (
          <div className="glass-card queue-row" key={item.id}>
            <div>
              <strong>{item.url}</strong>
              <span>{item.mode.toUpperCase()} - {item.quality}</span>
            </div>
            <span className="status-chip">{item.status}</span>
            <button className="icon-button" onClick={() => setQueueItems((items) => items.filter((entry) => entry.id !== item.id))}>
              <Trash2 size={17} />
            </button>
          </div>
        ))}
      </div>
    </section>
  );

  const historyPage = (
    <section className="page-panel">
      <div className="page-head">
        <div>
          <h2>Gecmis</h2>
          <p>Tamamlanan indirmeler burada listelenir.</p>
        </div>
        <button className="soft-action" onClick={refreshSideData}>
          <RefreshCw size={18} />
          Yenile
        </button>
      </div>
      <div className="history-list">
        {history.length === 0 && <div className="empty-state">Henuz indirme yok.</div>}
        {history.slice().reverse().map((item, index) => (
          <div className="glass-card history-row" key={`${item.date}-${index}`}>
            <CheckCircle2 size={18} />
            <div>
              <strong>{item.title}</strong>
              <span>{item.mode?.toUpperCase()} - {item.quality} - {item.date}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );

  const statsPage = (
    <section className="page-panel">
      <div className="page-head">
        <div>
          <h2>Istatistik</h2>
          <p>Genel indirme ozeti.</p>
        </div>
        <button className="soft-action" onClick={refreshSideData}>
          <RefreshCw size={18} />
          Yenile
        </button>
      </div>
      <div className="stats-grid">
        <StatCard label="Toplam indirme" value={stats?.total_count ?? history.length} />
        <StatCard label="MP3" value={stats?.by_format?.mp3 ?? 0} />
        <StatCard label="MP4" value={stats?.by_format?.mp4 ?? 0} />
        <StatCard label="M4A" value={stats?.by_format?.m4a ?? 0} />
      </div>
      <LogPanel log={log} />
    </section>
  );

  const settingsPage = (
    <section className="page-panel">
      <div className="page-head">
        <div>
          <h2>Ayarlar</h2>
          <p>Kayit klasoru, tema ve varsayilan indirme ayarlari.</p>
        </div>
      </div>
      <div className="settings-grid">
        <div className="glass-card">
          <label>Tema</label>
          <button className="theme-card-button" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
            {theme === 'dark' ? <Moon size={20} /> : <Sun size={20} />}
            {theme === 'dark' ? 'Dark mod' : 'Light mod'}
          </button>
        </div>
        <div className="glass-card">
          <label>Varsayilan klasor</label>
          <div className="folder-row">
            <Folder size={18} />
            <input value={outputDir} onChange={(e) => setOutputDir(e.target.value)} placeholder="Varsayilan Downloads klasoru" />
          </div>
        </div>
        <div className="glass-card">
          <label>Varsayilan format</label>
          <div className="segmented">
            {['mp3', 'mp4', 'm4a'].map((item) => (
              <button key={item} className={mode === item ? 'selected' : ''} onClick={() => changeMode(item)}>
                {item.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );

  const pages = {
    download: downloadPage,
    queue: queuePage,
    history: historyPage,
    stats: statsPage,
    settings: settingsPage,
  };

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <img className="brand-logo" src={itchyLogo} alt="Itchy Downloader" />
        </div>
        <nav>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={activePage === item.id ? 'nav-item active' : 'nav-item'}
                onClick={() => setActivePage(item.id)}
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
        <button className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} title="Tema degistir">
          {theme === 'dark' ? <Moon size={18} /> : <Sun size={18} />}
          {theme === 'dark' ? 'Dark' : 'Light'}
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar compact">
          <div className="status-pill">
            <Activity size={16} />
            {status}
          </div>
        </header>
        {pages[activePage]}
      </section>
    </main>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="glass-card stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RecentDownloads({ history }) {
  return (
    <div className="glass-card recent-card">
      <h3>Son indirilenler</h3>
      {history.length === 0 && <p className="muted">Henuz indirme yok.</p>}
      {history.slice(-4).reverse().map((item, index) => (
        <div className="recent-row" key={`${item.date}-${index}`}>
          <CheckCircle2 size={16} />
          <div>
            <strong>{item.title}</strong>
            <span>{item.mode?.toUpperCase()} - {item.quality} - {item.date}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function LogPanel({ log }) {
  return (
    <div className="glass-card log-card">
      <h3>Islem gunlugu</h3>
      {log.length === 0 && <p className="muted">Log kaydi yok.</p>}
      {log.map((item, index) => (
        <p key={index}>{item}</p>
      ))}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
