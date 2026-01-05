import { useState, useEffect, useRef } from "react";
import { toast } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import { api } from "./api";
import "./App.css";

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const abortControllerRef = useRef(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error("Failed to load conversations:", error);
      toast.error("Sohbetler yüklenemedi. Lütfen tekrar deneyin.");
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error("Failed to load conversation:", error);
      toast.error("Sohbet yüklenemedi.");
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
      toast.success("Yeni sohbet oluşturuldu");
    } catch (error) {
      console.error("Failed to create conversation:", error);
      toast.error("Sohbet oluşturulamadı.");
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
      toast.success("Sohbet silindi");
    } catch (error) {
      console.error("Failed to delete conversation:", error);
      toast.error("Sohbet silinemedi");
    }
  };

  const handleStopGeneration = async () => {
    if (abortControllerRef.current) {
      // Abort the frontend fetch request
      abortControllerRef.current.abort();
      abortControllerRef.current = null;

      // Also notify backend to stop LLM requests
      if (currentConversationId) {
        await api.cancelRequest(currentConversationId);
      }

      setIsLoading(false);
      toast("Yanıt durduruldu", { icon: "⏹️" });
    }
  };

  const handleRegenerateMessage = async (messageIndex) => {
    if (!currentConversationId || !currentConversation) return;

    // Find the user message that prompted this response
    // The assistant message is at messageIndex, user message should be at messageIndex - 1
    const messages = currentConversation.messages;
    let userMessageIndex = messageIndex - 1;

    // Walk back to find the user message
    while (
      userMessageIndex >= 0 &&
      messages[userMessageIndex]?.role !== "user"
    ) {
      userMessageIndex--;
    }

    if (userMessageIndex < 0) {
      toast.error("Kullanıcı mesajı bulunamadı");
      return;
    }

    const userContent = messages[userMessageIndex].content;

    // Remove the old assistant response
    setCurrentConversation((prev) => ({
      ...prev,
      messages: prev.messages.slice(0, messageIndex),
    }));

    toast("Yanıt yeniden oluşturuluyor...", { icon: "🔄" });

    // Re-send the message
    await handleSendMessage(userContent);
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: "user", content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: "assistant",
        stage1: null,
        stage2: null,
        stage3: null,
        simpleResponse: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
          simple: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(
        currentConversationId,
        content,
        (eventType, event) => {
          switch (eventType) {
            case "simple_mode_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.simple = true;
                return { ...prev, messages };
              });
              toast("Tekli LLM Modu - Başkan yanıt veriyor...", { icon: "👑" });
              break;

            case "simple_mode_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.simpleResponse = event.data;
                lastMsg.loading.simple = false;
                return { ...prev, messages };
              });
              break;

            case "stage1_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage1 = true;
                lastMsg.loading.stage1Models = event.models || [];
                return { ...prev, messages };
              });
              break;

            case "stage1_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage1 = event.data;
                lastMsg.loading.stage1 = false;
                return { ...prev, messages };
              });
              break;

            case "stage2_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage2 = true;
                return { ...prev, messages };
              });
              break;

            case "stage2_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage2 = event.data;
                lastMsg.metadata = event.metadata;
                lastMsg.loading.stage2 = false;
                return { ...prev, messages };
              });
              break;

            case "stage3_start":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage3 = true;
                return { ...prev, messages };
              });
              break;

            case "stage3_complete":
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage3 = event.data;
                lastMsg.loading.stage3 = false;
                return { ...prev, messages };
              });
              break;

            case "title_complete":
              // Reload conversations to get updated title
              loadConversations();
              break;

            case "complete":
              // Stream complete, reload conversations list
              loadConversations();
              toast.success("Konsey cevabı tamamlandı");
              setIsLoading(false);
              abortControllerRef.current = null;
              break;

            case "error":
              console.error("Stream error:", event.message);
              toast.error(`Hata: ${event.message}`);
              setIsLoading(false);
              abortControllerRef.current = null;
              break;

            case "aborted":
              // User stopped the generation (frontend)
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                // Clear loading states
                if (lastMsg.loading) {
                  lastMsg.loading.stage1 = false;
                  lastMsg.loading.stage2 = false;
                  lastMsg.loading.stage3 = false;
                  lastMsg.loading.simple = false;
                }
                return { ...prev, messages };
              });
              break;

            case "cancelled":
              // Backend confirmed cancellation
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.loading) {
                  lastMsg.loading.stage1 = false;
                  lastMsg.loading.stage2 = false;
                  lastMsg.loading.stage3 = false;
                }
                return { ...prev, messages };
              });
              setIsLoading(false);
              abortControllerRef.current = null;
              break;

            default:
              console.log("Unknown event type:", eventType);
          }
        },
        abortControllerRef.current?.signal
      );
    } catch (error) {
      if (error.name === "AbortError") {
        // User cancelled - don't show error
        return;
      }
      console.error("Failed to send message:", error);
      toast.error("Mesaj gönderilemedi. Lütfen tekrar deneyin.");
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="app">
      {/* Mobile hamburger button */}
      <button
        className="sidebar-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        onStopGeneration={handleStopGeneration}
        onRegenerateMessage={handleRegenerateMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;
