import { useState } from "react";
import ReactMarkdown from "react-markdown";
import "./Stage2.css";

function deAnonymizeText(text, labelToModel) {
  if (!labelToModel) return text;

  let result = text;
  // Replace each "Response X" with the actual model name
  Object.entries(labelToModel).forEach(([label, model]) => {
    const modelShortName = model.split("/")[1] || model;
    result = result.replace(new RegExp(label, "g"), `**${modelShortName}**`);
  });
  return result;
}

export default function Stage2({ rankings, labelToModel, aggregateRankings }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!rankings || rankings.length === 0) {
    return null;
  }

  return (
    <div className="stage stage2">
      <h3 className="stage-title">Aşama 2: Akran Değerlendirmesi</h3>

      <h4>Ham Değerlendirmeler</h4>
      <p className="stage-description">
        Her model tüm yanıtları <strong>anonim</strong> olarak (Yanıt A, B, C
        şeklinde) değerlendirdi.
        <br />
        <em style={{ opacity: 0.7, fontSize: "12px" }}>
          Not: Model isimleri okunabilirlik için sonradan eklenmektedir -
          değerlendirme sırasında modeller birbirlerinin kimliğini bilmiyordu.
        </em>
      </p>

      <div className="tabs">
        {rankings.map((rank, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? "active" : ""} ${
              rank.is_failover ? "failover" : ""
            }`}
            onClick={() => setActiveTab(index)}
            title={
              rank.is_failover
                ? `Yerine: ${
                    rank.original_display_name || rank.original_provider
                  }`
                : rank.display_name
            }
          >
            {rank.display_name || rank.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="ranking-model">
          {rankings[activeTab].display_name || rankings[activeTab].model}
          {rankings[activeTab].is_failover && (
            <span className="failover-info">
              {" "}
              (Yerine:{" "}
              {rankings[activeTab].original_display_name ||
                rankings[activeTab].original_provider}
              )
            </span>
          )}
        </div>
        <div className="ranking-content markdown-content">
          <ReactMarkdown>
            {deAnonymizeText(rankings[activeTab].ranking, labelToModel)}
          </ReactMarkdown>
        </div>

        {rankings[activeTab].parsed_ranking &&
          rankings[activeTab].parsed_ranking.length > 0 && (
            <div className="parsed-ranking">
              <strong>Çıkarılan Sıralama:</strong>
              <ol>
                {rankings[activeTab].parsed_ranking.map((label, i) => (
                  <li key={i}>
                    {labelToModel && labelToModel[label]
                      ? labelToModel[label].split("/")[1] || labelToModel[label]
                      : label}
                  </li>
                ))}
              </ol>
            </div>
          )}
      </div>

      {aggregateRankings && aggregateRankings.length > 0 && (
        <div className="aggregate-rankings">
          <h4>Genel Sıralama (Toplam Puan)</h4>
          <p className="stage-description">
            Tüm akran değerlendirmelerinin birleşik sonuçları (düşük skor daha
            iyi):
          </p>
          <div className="aggregate-list">
            {aggregateRankings.map((agg, index) => (
              <div key={index} className="aggregate-item">
                <span className="rank-position">{index + 1}</span>
                <span className="rank-model">
                  {agg.model.split("/")[1] || agg.model}
                </span>
                <span className="rank-score">
                  Ort: {agg.average_rank.toFixed(2)}
                </span>
                <span className="rank-count">({agg.rankings_count} oy)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
