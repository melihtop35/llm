import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import Stage1 from "./Stage1";
import Stage2 from "./Stage2";
import Stage3 from "./Stage3";
import Logo from "./Logo";
import "./ChatInterface.css";

export default function ChatInterface({
  conversation,
  onSendMessage,
  onStopGeneration,
  onRegenerateMessage,
  isLoading,
}) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput("");
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <Logo size={64} className="saints-logo" glow />
          <h2>LLM Konseyi'ne Hoş Geldiniz</h2>
          <p>Başlamak için yeni bir sohbet oluşturun</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {conversation.messages.length === 0 ? (
          <div className="empty-state">
            <Logo size={64} className="saints-logo" glow />
            <h2>Sohbete Başlayın</h2>
            <p>Konseyin bilgeliğinden yararlanmak için bir soru sorun</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === "user" ? (
                <div className="user-message">
                  <div className="message-label">Siz</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Konseyi</div>

                  {/* Simple Mode (no experts, only chairman) */}
                  {msg.loading?.simple && (
                    <div className="stage-loading simple-mode">
                      <div className="spinner"></div>
                      <span>Başkan yanıt hazırlıyor...</span>
                    </div>
                  )}
                  {msg.simpleResponse && (
                    <div className="simple-response">
                      <div className="simple-header">
                        <span className="simple-icon">
                          <Logo size={20} />
                        </span>
                        <span className="simple-title">
                          {msg.simpleResponse.display_name}
                        </span>
                        <span className="simple-badge">Tekli Mod</span>
                      </div>
                      <div className="simple-content">
                        <ReactMarkdown>
                          {msg.simpleResponse.response}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {!msg.simpleResponse && (
                    <>
                      {/* Stage 1 */}
                      {msg.loading?.stage1 && (
                        <div className="stage-loading">
                          <div className="stage-loading-header">
                            <div className="spinner"></div>
                            <span>
                              Aşama 1: Bireysel yanıtlar toplanıyor...
                            </span>
                          </div>
                          {msg.loading?.stage1Models &&
                            msg.loading.stage1Models.length > 0 && (
                              <div className="active-models">
                                {msg.loading.stage1Models.map((model, i) => (
                                  <span key={i} className="model-badge">
                                    {model}
                                  </span>
                                ))}
                              </div>
                            )}
                        </div>
                      )}
                      {msg.stage1 && <Stage1 responses={msg.stage1} />}

                      {/* Stage 2 */}
                      {msg.loading?.stage2 && (
                        <div className="stage-loading">
                          <div className="stage-loading-header">
                            <div className="spinner"></div>
                            <span>
                              Aşama 2: Akran değerlendirmesi yapılıyor...
                            </span>
                          </div>
                        </div>
                      )}
                      {msg.stage2 && (
                        <Stage2
                          rankings={msg.stage2}
                          labelToModel={msg.metadata?.label_to_model}
                          aggregateRankings={msg.metadata?.aggregate_rankings}
                        />
                      )}

                      {/* Stage 3 */}
                      {msg.loading?.stage3 && (
                        <div className="stage-loading">
                          <div className="stage-loading-header">
                            <div className="spinner"></div>
                            <span>Aşama 3: Nihai sentez hazırlanıyor...</span>
                          </div>
                        </div>
                      )}
                      {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}

                      {/* Regenerate Button - show after all stages complete */}
                      {msg.stage3 && !isLoading && onRegenerateMessage && (
                        <button
                          className="regenerate-button"
                          onClick={() => onRegenerateMessage(index)}
                          title="Bu yanıtı yeniden oluştur"
                        >
                          <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M1 4v6h6" />
                            <path d="M23 20v-6h-6" />
                            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
                          </svg>
                          Yeniden Oluştur
                        </button>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <Logo size={28} className="saints-logo" />
            <span>Konsey toplanıyor...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          className="message-input"
          placeholder="Konseye sorunuzu sorun... (Shift+Enter yeni satır, Enter gönder)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />

        {isLoading ? (
          <button
            type="button"
            className="stop-button"
            onClick={onStopGeneration}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <rect x="6" y="5" width="4" height="14" rx="1.5" />
              <rect x="14" y="5" width="4" height="14" rx="1.5" />
            </svg>
            Durdur
          </button>
        ) : (
          <button
            type="submit"
            className="send-button"
            disabled={!input.trim()}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
            Gönder
          </button>
        )}
      </form>
    </div>
  );
}
