import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

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
    --r:           14px;
    --r-sm:        8px;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --bg:          #0D1117;
      --white:       #161B22;
      --ink:         #E6EDF3;
      --ink-mid:     #B1BAC4;
      --ink-muted:   #6E7681;
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
    }
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
