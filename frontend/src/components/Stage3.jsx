import { useState } from "react";
import ReactMarkdown from "react-markdown";
import Logo from "./Logo";
import "./Stage3.css";

export default function Stage3({ finalResponse }) {
  const [copied, setCopied] = useState(false);

  if (!finalResponse) {
    return null;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(finalResponse.response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  return (
    <div className="stage stage3">
      <h3 className="stage-title">Aşama 3: Konsey Nihai Cevabı</h3>
      <div className="final-response">
        <div className="final-header">
          <div className="chairman-label">
            <Logo size={18} className="saints-logo" />
            Başkan: {finalResponse.display_name || finalResponse.model}
          </div>
          <button className="copy-btn" onClick={handleCopy} title="Kopyala">
            {copied ? (
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
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : (
              <svg
                width="18"
                height="18"
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
            <span>{copied ? "Kopyalandı!" : "Kopyala"}</span>
          </button>
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
