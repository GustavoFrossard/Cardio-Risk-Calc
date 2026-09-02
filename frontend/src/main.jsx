import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// Paleta escura reutilizada tanto pela preferência do sistema quanto pelo
// toggle manual (atributo data-theme="dark" no <html>).
const darkVars = `
    --bg:          #0D1117;
    --white:       #161B22;
    --ink:         #E6EDF3;
    --ink-mid:     #B1BAC4;
    --ink-muted:   #8B929E;
    --blue:        #4493F8;
    --blue-soft:   #1A2842;
    --blue-mid:    #79B8FF;
    --red:         #F85149;
    --red-soft:    #3D1B1B;
    --green:       #3FB950;
    --green-soft:  #162320;
    --amber:       #D29922;
    --amber-soft:  #2D2208;
    --bg-soft:     #1C2128;
    --border:      #30363D;
    --bar-bg:      rgba(22,27,34,0.94);
    --blue-border: rgba(68,147,248,0.38);
    --amber-border:rgba(210,153,34,0.45);
    --green-border:rgba(63,185,80,0.40);
    --red-border:  rgba(248,81,73,0.40);
`;

const style = document.createElement("style");
style.textContent = `
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
    --bg-soft:     #EDF0F5;
    --border:      #E4E7EE;
    --bar-bg:      rgba(255,255,255,0.94);
    --blue-border: #BDD3FB;
    --amber-border:#FCD34D;
    --green-border:#A7D4BB;
    --red-border:  #F5B0AA;
    --r:           14px;
    --r-sm:        8px;
  }

  /* Preferência do sistema (quando o usuário não escolheu manualmente) */
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
    ${darkVars}
    }
  }

  /* Escolha manual do usuário — vence sobre a preferência do sistema */
  :root[data-theme="dark"] {
    ${darkVars}
  }

  html {
    color-scheme: light dark;
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
    height: 6px;
    border-radius: 3px;
    background: var(--border);
    outline: none;
    cursor: pointer;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--blue);
    cursor: pointer;
    box-shadow: 0 1px 5px rgba(26,107,240,0.35);
    border: 2px solid white;
  }
  input[type=range]::-moz-range-thumb {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: var(--blue);
    cursor: pointer;
    border: 2px solid white;
    box-shadow: 0 1px 5px rgba(26,107,240,0.35);
  }

  button, select, input, textarea {
    font-family: 'Outfit', sans-serif;
  }

  * {
    -webkit-tap-highlight-color: transparent;
  }
`;
document.head.appendChild(style);

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
