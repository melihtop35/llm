import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import "./index.css";
import App from "./App.jsx";
import Settings from "./components/Settings.jsx";
import Analytics from "./components/Analytics.jsx";
import { ThemeProvider } from "./theme/ThemeProvider";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: "var(--bg-card)",
              color: "var(--text-primary)",
              border: "1px solid rgba(var(--ui-accent-rgb), 0.3)",
              borderRadius: "12px",
              boxShadow: "var(--shadow-gold)",
            },
            success: {
              iconTheme: {
                primary: "var(--accent-gold)",
                secondary: "var(--bg-card)",
              },
            },
            error: {
              iconTheme: {
                primary: "var(--accent-danger)",
                secondary: "var(--bg-card)",
              },
            },
          }}
        />
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>
);
