import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// ─── Global CSS Variables & Reset ────────────────────────────────────────────
const style = document.createElement("style");
style.textContent = `
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :root {
    --bg:          #F7F8FA;
    --white:       #FFFFFF;
    --ink:         #0D1117;
    --ink-mid:     #3D4451;
    --ink-muted:   #8B909A;
    --blue:        #1A6BF0;
    --blue-soft:   #EBF1FE;
    --blue-mid:    #5B94F5;
    --red:         #E03131;
    --red-soft:    #FFF0F0;
    --green:       #0E7B52;
    --green-soft:  #EDFAF4;
    --amber:       #C47A00;
    --amber-soft:  #FFF8E6;
    --border:      #E4E7EE;
    --r:           14px;
    --r-sm:        8px;
  }

  html, body, #root {
    min-height: 100vh;
    background: var(--bg);
  }

  body {
    font-family: 'Outfit', sans-serif;
    color: var(--ink);
    -webkit-font-smoothing: antialiased;
    display: flex;
    justify-content: center;
  }

  input[type=range] {
    -webkit-appearance: none;
    width: 100%;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
    outline: none;
    cursor: pointer;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--blue);
    cursor: pointer;
    box-shadow: 0 1px 5px rgba(26,107,240,0.3);
  }
`;
document.head.appendChild(style);

// ─── Mount ────────────────────────────────────────────────────────────────────
const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
