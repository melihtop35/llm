import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import toast from "react-hot-toast";
import Logo from "./Logo";
import "./Settings.css";
import { useTheme } from "../theme/ThemeProvider";

export default function Settings() {
  const { themeId, setThemeId, themes } = useTheme();

  const [settings, setSettings] = useState({
    chairman: "",
    experts: [],
    failover_models: [],
    all_providers: {},
    api_keys: {},
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editedKeys, setEditedKeys] = useState({}); // Track which keys were edited

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      setEditedKeys({}); // Reset edited keys on load
    } catch (error) {
      console.error("Failed to load settings:", error);
      toast.error("Ayarlar yüklenemedi");
    } finally {
      setLoading(false);
    }
  };

  const handleChairmanSelect = (providerId) => {
    setSettings((prev) => {
      // If selecting current chairman, do nothing
      if (prev.chairman === providerId) return prev;

      // If selecting an expert, swap them
      const newExperts = prev.experts.filter((id) => id !== providerId);
      if (prev.chairman && !newExperts.includes(prev.chairman)) {
        // Old chairman becomes expert if was selected from experts
        if (prev.experts.includes(providerId)) {
          newExperts.push(prev.chairman);
        }
      }

      return {
        ...prev,
        chairman: providerId,
        experts: newExperts,
      };
    });
  };

  const handleExpertToggle = (providerId) => {
    // Can't toggle chairman as expert
    if (settings.chairman === providerId) {
      toast.error("Başkan aynı zamanda uzman olamaz!");
      return;
    }

    setSettings((prev) => ({
      ...prev,
      experts: prev.experts.includes(providerId)
        ? prev.experts.filter((id) => id !== providerId)
        : [...prev.experts, providerId],
    }));
  };

  const handleApiKeyChange = (providerId, value) => {
    setEditedKeys((prev) => ({
      ...prev,
      [providerId]: value,
    }));
  };

  const handleSave = async () => {
    if (!settings.chairman) {
      toast.error("Lütfen bir başkan seçin!");
      return;
    }

    // Uzman yoksa uyarı göster ama kaydetmeye izin ver (normal LLM modu)
    if (settings.experts.length === 0) {
      toast("Uzman seçilmedi - Sadece başkan yanıt verecek", { icon: "ℹ️" });
    }

    setSaving(true);
    const savingToastId = toast.loading("Kaydediliyor...");
    try {
      // Only send edited API keys (not masked ones)
      const apiKeysToSave = {};
      Object.entries(editedKeys).forEach(([id, key]) => {
        if (key && key.trim()) {
          apiKeysToSave[id] = key;
        }
      });

      await api.updateSettings({
        chairman: settings.chairman,
        experts: settings.experts,
        api_keys: apiKeysToSave,
      });
      toast.dismiss(savingToastId);
      toast.success("Ayarlar kaydedildi! Yeni sohbetlerde aktif olacak.");
      setEditedKeys({}); // Clear edited keys
      loadSettings(); // Reload to get fresh masked keys
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast.dismiss(savingToastId);
      toast.error("Ayarlar kaydedilemedi");
    } finally {
      setSaving(false);
    }
  };

  // Calculate failover (unselected providers)
  const getFailoverModels = () => {
    const selected = new Set([settings.chairman, ...settings.experts]);
    return Object.keys(settings.all_providers || {}).filter(
      (id) => !selected.has(id)
    );
  };

  if (loading) {
    return (
      <div className="settings-page">
        <div className="loading-spinner">Yükleniyor...</div>
      </div>
    );
  }

  const providers = settings.all_providers || {};
  const failoverModels = getFailoverModels();

  return (
    <div className="settings-page">
      <div className="settings-header">
        <Link to="/" className="back-btn">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Geri
        </Link>
        <h1>⚙️ Konsey Ayarları</h1>
      </div>

      <div className="settings-content">
        {/* Theme Selection */}
        <section className="settings-section theme-section">
          <div className="section-header">
            <h2>🎨 Tema</h2>
          </div>
          <p className="section-desc">
            Tema; yazı fontlarını, renkleri ve logoyu birlikte değiştirir.
          </p>
          <div className="theme-row">
            <label className="theme-label">Tema seçin</label>
            <select
              className="theme-select"
              value={themeId}
              onChange={(e) => setThemeId(e.target.value)}
            >
              {themes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </section>

        {/* Chairman Selection */}
        <section className="settings-section chairman-section">
          <div className="section-header">
            <h2>👑 Başkan Seçimi</h2>
            <span className="section-badge">1 Seçim</span>
          </div>
          <p className="section-desc">
            Başkan, tüm uzman görüşlerini değerlendirip nihai sentezi oluşturur.
          </p>
          <div className="providers-grid chairman-grid">
            {Object.entries(providers).map(([id, provider]) => (
              <div
                key={id}
                className={`provider-card chairman-card ${
                  settings.chairman === id ? "selected" : ""
                }`}
                onClick={() => handleChairmanSelect(id)}
              >
                <div className="card-check">
                  {settings.chairman === id && <Logo size={20} />}
                </div>
                <div className="provider-icon">{provider.icon}</div>
                <div className="provider-name">{provider.name}</div>
                <div className="provider-model">{provider.model}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Expert Selection */}
        <section className="settings-section experts-section">
          <div className="section-header">
            <h2>🧠 Uzman Seçimi</h2>
            <span className="section-badge">
              {settings.experts.length} Seçili
            </span>
          </div>
          <p className="section-desc">
            Uzmanlar, soruya bireysel yanıtlar verir ve birbirlerini
            değerlendirir.
          </p>
          <div className="providers-grid">
            {Object.entries(providers).map(([id, provider]) => {
              const isChairman = settings.chairman === id;
              const isExpert = settings.experts.includes(id);
              return (
                <div
                  key={id}
                  className={`provider-card expert-card ${
                    isExpert ? "selected" : ""
                  } ${isChairman ? "disabled" : ""}`}
                  onClick={() => !isChairman && handleExpertToggle(id)}
                >
                  <div className="card-check">
                    {isChairman ? <Logo size={18} /> : isExpert ? "✓" : ""}
                  </div>
                  <div className="provider-icon">{provider.icon}</div>
                  <div className="provider-name">{provider.name}</div>
                  <div className="provider-model">{provider.model}</div>
                  <div className="provider-role">{provider.role}</div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Failover Models (Auto) */}
        <section className="settings-section failover-section">
          <div className="section-header">
            <h2>🛡️ Yedek Modeller (Failover)</h2>
            <span className="section-badge auto">Otomatik</span>
          </div>
          <p className="section-desc">
            Seçilmeyen modeller otomatik olarak yedek havuzuna eklenir. Bir
            uzman başarısız olursa bu modeller devreye girer.
          </p>
          <div className="failover-list">
            {failoverModels.length > 0 ? (
              failoverModels.map((id) => (
                <div key={id} className="failover-item">
                  <span className="failover-icon">{providers[id]?.icon}</span>
                  <span className="failover-name">{providers[id]?.name}</span>
                  <span className="failover-model">{providers[id]?.model}</span>
                </div>
              ))
            ) : (
              <div className="failover-empty">
                Tüm modeller aktif - yedek model yok
              </div>
            )}
          </div>
        </section>

        {/* API Keys */}
        <section className="settings-section api-section">
          <div className="section-header">
            <h2>🔑 API Anahtarları</h2>
          </div>
          <p className="section-desc">
            Sağlayıcıların API anahtarlarını buradan güncelleyebilirsiniz.
          </p>
          <div className="api-keys-list">
            {Object.entries(providers).map(([id, provider]) => {
              const hasExistingKey = settings.api_keys?.[`${id}_exists`];
              const maskedKey = settings.api_keys?.[id] || "";
              const editedValue = editedKeys[id];
              const isEditing = editedValue !== undefined;

              return (
                <div key={id} className="api-key-item">
                  <label>
                    <span className="api-provider-icon">{provider.icon}</span>
                    {provider.name}
                    {hasExistingKey && !isEditing && (
                      <span className="key-status configured">
                        ✓ Yapılandırıldı
                      </span>
                    )}
                  </label>
                  <input
                    type={isEditing ? "text" : "password"}
                    placeholder={
                      hasExistingKey
                        ? "Yeni anahtar girin (değiştirmek için)"
                        : `${provider.api_key_env} girin`
                    }
                    value={
                      isEditing ? editedValue : hasExistingKey ? maskedKey : ""
                    }
                    onChange={(e) => handleApiKeyChange(id, e.target.value)}
                    className={isEditing ? "editing" : ""}
                  />
                  {isEditing && (
                    <button
                      className="clear-edit-btn"
                      onClick={() =>
                        setEditedKeys((prev) => {
                          const newKeys = { ...prev };
                          delete newKeys[id];
                          return newKeys;
                        })
                      }
                      title="Değişikliği iptal et"
                    >
                      ✕
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        <button className="save-btn" onClick={handleSave} disabled={saving}>
          {saving ? "Kaydediliyor..." : "💾 Ayarları Kaydet"}
        </button>
      </div>
    </div>
  );
}
