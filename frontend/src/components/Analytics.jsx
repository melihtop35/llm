import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import "./Analytics.css";

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const [analyticsData, errorsData] = await Promise.all([
        api.getAnalytics(),
        api.getAnalyticsErrors(),
      ]);
      setAnalytics(analyticsData);
      setErrors(errorsData);
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num?.toFixed(0) || "0";
  };

  const formatTime = (ms) => {
    if (ms >= 1000) return (ms / 1000).toFixed(2) + "s";
    return ms?.toFixed(0) + "ms";
  };

  const getSuccessRate = (provider) => {
    if (!provider.total_requests) return 0;
    return (
      (provider.successful_requests / provider.total_requests) *
      100
    ).toFixed(1);
  };

  const getProviderIcon = (provider) => {
    const icons = {
      groq: "⚡",
      sambanova: "🟠",
      google: "🌐",
      mistral: "🌀",
      cohere: "📄",
      huggingface: "🤗",
      openrouter: "🔀",
    };
    return icons[provider] || "🤖";
  };

  const getStageLabel = (stage) => {
    const labels = {
      stage1: "Aşama 1 - Yanıtlar",
      stage2: "Aşama 2 - Değerlendirme",
      stage3: "Aşama 3 - Sentez",
      simple: "Tekli LLM",
      error: "Hata",
    };
    return labels[stage] || stage;
  };

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="analytics-loading">
          <div className="loading-spinner"></div>
          <p>Analitik veriler yükleniyor...</p>
        </div>
      </div>
    );
  }

  const totalRequests =
    analytics?.provider_stats?.reduce((sum, p) => sum + p.total_requests, 0) ||
    0;

  const totalSuccessful =
    analytics?.provider_stats?.reduce(
      (sum, p) => sum + p.successful_requests,
      0
    ) || 0;

  const avgResponseTime = analytics?.provider_stats?.length
    ? analytics.provider_stats.reduce(
        (sum, p) => sum + (p.avg_response_time || 0),
        0
      ) / analytics.provider_stats.length
    : 0;

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <Link to="/" className="back-button">
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
        <h1>📊 Model Analitiği</h1>
        <button className="refresh-button" onClick={loadAnalytics}>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Yenile
        </button>
      </div>

      {/* Tabs */}
      <div className="analytics-tabs">
        <button
          className={`tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          Genel Bakış
        </button>
        <button
          className={`tab ${activeTab === "providers" ? "active" : ""}`}
          onClick={() => setActiveTab("providers")}
        >
          Sağlayıcılar
        </button>
        <button
          className={`tab ${activeTab === "daily" ? "active" : ""}`}
          onClick={() => setActiveTab("daily")}
        >
          Günlük İstatistik
        </button>
        <button
          className={`tab ${activeTab === "errors" ? "active" : ""}`}
          onClick={() => setActiveTab("errors")}
        >
          Hatalar{" "}
          {errors.length > 0 && (
            <span className="error-badge">{errors.length}</span>
          )}
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="analytics-content">
          {/* Summary Cards */}
          <div className="summary-cards">
            <div className="summary-card">
              <div className="card-icon">📨</div>
              <div className="card-content">
                <div className="card-value">{formatNumber(totalRequests)}</div>
                <div className="card-label">Toplam İstek</div>
              </div>
            </div>
            <div className="summary-card success">
              <div className="card-icon">✅</div>
              <div className="card-content">
                <div className="card-value">
                  {totalRequests
                    ? ((totalSuccessful / totalRequests) * 100).toFixed(1)
                    : 0}
                  %
                </div>
                <div className="card-label">Başarı Oranı</div>
              </div>
            </div>
            <div className="summary-card">
              <div className="card-icon">⏱️</div>
              <div className="card-content">
                <div className="card-value">{formatTime(avgResponseTime)}</div>
                <div className="card-label">Ort. Yanıt Süresi</div>
              </div>
            </div>
            <div className="summary-card">
              <div className="card-icon">🤖</div>
              <div className="card-content">
                <div className="card-value">
                  {analytics?.provider_stats?.length || 0}
                </div>
                <div className="card-label">Aktif Model</div>
              </div>
            </div>
          </div>

          {/* Stage Stats */}
          <div className="section">
            <h2>🎯 Aşama İstatistikleri</h2>
            <div className="stage-stats">
              {analytics?.stage_stats?.map((stage) => (
                <div key={stage._id} className="stage-card">
                  <div className="stage-name">{getStageLabel(stage._id)}</div>
                  <div className="stage-metrics">
                    <div className="metric">
                      <span className="metric-value">
                        {formatNumber(stage.total_requests)}
                      </span>
                      <span className="metric-label">İstek</span>
                    </div>
                    <div className="metric">
                      <span className="metric-value">
                        {formatTime(stage.avg_response_time)}
                      </span>
                      <span className="metric-label">Ort. Süre</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Providers Chart */}
          <div className="section">
            <h2>🏆 En Aktif Modeller</h2>
            <div className="provider-chart">
              {analytics?.provider_stats?.slice(0, 5).map((provider, index) => {
                const maxRequests =
                  analytics.provider_stats[0]?.total_requests || 1;
                const percentage =
                  (provider.total_requests / maxRequests) * 100;
                return (
                  <div key={provider._id} className="chart-row">
                    <div className="chart-label">
                      <span className="provider-icon">
                        {getProviderIcon(provider._id)}
                      </span>
                      <span className="provider-name">{provider._id}</span>
                    </div>
                    <div className="chart-bar-container">
                      <div
                        className="chart-bar"
                        style={{ width: `${percentage}%` }}
                        data-rank={index + 1}
                      ></div>
                      <span className="chart-value">
                        {formatNumber(provider.total_requests)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Providers Tab */}
      {activeTab === "providers" && (
        <div className="analytics-content">
          <div className="providers-grid">
            {analytics?.provider_stats?.map((provider) => (
              <div key={provider._id} className="provider-card">
                <div className="provider-header">
                  <span className="provider-icon large">
                    {getProviderIcon(provider._id)}
                  </span>
                  <div className="provider-info">
                    <h3>{provider._id}</h3>
                    <span className="provider-requests">
                      {formatNumber(provider.total_requests)} istek
                    </span>
                  </div>
                </div>

                <div className="provider-metrics">
                  <div className="metric-row">
                    <span className="metric-label">Başarı Oranı</span>
                    <div className="metric-bar-container">
                      <div
                        className={`metric-bar ${
                          getSuccessRate(provider) >= 95
                            ? "excellent"
                            : getSuccessRate(provider) >= 80
                            ? "good"
                            : "poor"
                        }`}
                        style={{ width: `${getSuccessRate(provider)}%` }}
                      ></div>
                    </div>
                    <span className="metric-value">
                      {getSuccessRate(provider)}%
                    </span>
                  </div>

                  <div className="metric-row">
                    <span className="metric-label">Ort. Yanıt</span>
                    <span className="metric-value time">
                      {formatTime(provider.avg_response_time)}
                    </span>
                  </div>

                  <div className="metric-row">
                    <span className="metric-label">Başarılı</span>
                    <span className="metric-value success">
                      {formatNumber(provider.successful_requests)}
                    </span>
                  </div>

                  <div className="metric-row">
                    <span className="metric-label">Başarısız</span>
                    <span className="metric-value error">
                      {formatNumber(
                        provider.total_requests - provider.successful_requests
                      )}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Daily Stats Tab */}
      {activeTab === "daily" && (
        <div className="analytics-content">
          <div className="section">
            <h2>📅 Son 30 Gün</h2>
            <div className="daily-chart">
              {analytics?.daily_stats?.map((day) => {
                const maxRequests = Math.max(
                  ...analytics.daily_stats.map((d) => d.requests)
                );
                const height = (day.requests / maxRequests) * 100;
                return (
                  <div key={day._id} className="daily-bar-container">
                    <div className="daily-bar" style={{ height: `${height}%` }}>
                      <span className="daily-tooltip">
                        {day._id}
                        <br />
                        {day.requests} istek
                        <br />
                        {formatTime(day.avg_response_time)} ort.
                      </span>
                    </div>
                    <span className="daily-label">{day._id.slice(5)}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="daily-table">
            <table>
              <thead>
                <tr>
                  <th>Tarih</th>
                  <th>İstek Sayısı</th>
                  <th>Ort. Yanıt Süresi</th>
                </tr>
              </thead>
              <tbody>
                {analytics?.daily_stats?.map((day) => (
                  <tr key={day._id}>
                    <td>{day._id}</td>
                    <td>{day.requests}</td>
                    <td>{formatTime(day.avg_response_time)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Errors Tab */}
      {activeTab === "errors" && (
        <div className="analytics-content">
          {errors.length === 0 ? (
            <div className="no-errors">
              <div className="no-errors-icon">🎉</div>
              <h3>Harika! Hiç hata yok</h3>
              <p>Son dönemde kayıtlı hata bulunmuyor.</p>
            </div>
          ) : (
            <div className="errors-list">
              {errors.map((error) => (
                <div key={error._id} className="error-card">
                  <div className="error-header">
                    <span className="error-provider">
                      {getProviderIcon(error.provider)} {error.provider}
                    </span>
                    <span className="error-stage">
                      {getStageLabel(error.stage)}
                    </span>
                    <span className="error-time">
                      {new Date(error.timestamp).toLocaleString("tr-TR")}
                    </span>
                  </div>
                  <div className="error-message">{error.error_message}</div>
                  <div className="error-meta">
                    <span>Model: {error.model}</span>
                    <span>
                      Conversation: {error.conversation_id?.slice(0, 8)}...
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
