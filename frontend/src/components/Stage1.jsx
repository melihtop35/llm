import { useState } from "react";
import ReactMarkdown from "react-markdown";
import "./Stage1.css";

export default function Stage1({ responses }) {
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!responses || responses.length === 0) {
    return null;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(responses[activeTab].response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  return (
    <div className="stage stage1">
      <h3 className="stage-title">Aşama 1: Bireysel Yanıtlar</h3>

      <div className="tabs">
        {responses.map((resp, index) => (
          <button
            key={index}
            className={`tab ${activeTab === index ? "active" : ""} ${
              resp.is_failover ? "failover" : ""
            }`}
            onClick={() => setActiveTab(index)}
            title={
              resp.is_failover
                ? `Yedek: ${resp.display_name}`
                : resp.display_name
            }
          >
            {resp.display_name || resp.model}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <div className="tab-header">
          <div className="model-name">
            {responses[activeTab].display_name || responses[activeTab].model}
            {responses[activeTab].is_failover && (
              <span className="failover-info">
                {" "}
                (Yerine:{" "}
                {responses[activeTab].original_display_name ||
                  responses[activeTab].original_provider}
                )
              </span>
            )}
          </div>
          <button
            className="copy-btn-small"
            onClick={handleCopy}
            title="Kopyala"
          >
            {copied ? (
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : (
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <rect
                  x="9"
                  y="9"
                  width="13"
                  height="13"
                  rx="2"
                  ry="2"
                  strokeWidth="2"
                />
                <path
                  d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                  strokeWidth="2"
                />
              </svg>
            )}
          </button>
        </div>
        <div className="response-text markdown-content">
          <ReactMarkdown>{responses[activeTab].response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
