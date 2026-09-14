import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/themes.css";
import "./styles/tokens.css";
import "./styles/global.css";
import "./styles/layout.css";
import { iniciarTema } from "./config/theme";
import { App } from "./App";

iniciarTema();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
