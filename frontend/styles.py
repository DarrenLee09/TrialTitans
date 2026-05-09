"""Modern SaaS CSS + font injection for the TrialTitans frontend."""
from __future__ import annotations

import streamlit as st

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
  /* Neutral surface palette */
  --bg:           #F7F8FA;
  --surface:      #FFFFFF;
  --surface-2:    #F2F4F7;
  --surface-3:    #E8ECF1;
  --border:       #E4E7EC;
  --border-strong:#D0D5DD;

  /* Ink scale */
  --ink:          #0F172A;
  --ink-2:        #344054;
  --ink-3:        #667085;
  --ink-4:        #98A2B3;

  /* Brand */
  --brand:        #2D6BFF;
  --brand-600:    #1F5AE6;
  --brand-50:     #EAF1FF;
  --brand-100:    #D6E4FF;

  /* Accents */
  --success:      #12B76A;
  --warning:      #F79009;
  --highlight:    #FEF3C7;

  /* Geometry */
  --radius-xs: 6px;
  --radius-sm: 8px;
  --radius:    12px;
  --radius-lg: 16px;

  /* Elevation */
  --shadow-xs:  0 1px 2px rgba(16,24,40,0.05);
  --shadow-sm:  0 1px 3px rgba(16,24,40,0.06), 0 1px 2px rgba(16,24,40,0.04);
  --shadow-md:  0 4px 8px -2px rgba(16,24,40,0.08), 0 2px 4px -2px rgba(16,24,40,0.04);
  --shadow-lg:  0 12px 24px -8px rgba(16,24,40,0.10), 0 4px 8px -4px rgba(16,24,40,0.04);
}

/* ---------------- Base ---------------- */
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.stApp {
  background: var(--bg) !important;
}

/* Streamlit chrome */
#MainMenu, footer { display: none !important; }
header[data-testid="stHeader"] {
  background: transparent !important;
  height: auto !important;
  box-shadow: none !important;
}
header[data-testid="stHeader"] [data-testid="stToolbar"],
header[data-testid="stHeader"] [data-testid="stDecoration"],
header[data-testid="stHeader"] [data-testid="stStatusWidget"] { display: none !important; }

/* Sidebar collapse arrow stays visible */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  display: block !important;
  visibility: visible !important;
  background: var(--surface) !important;
  color: var(--ink-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  box-shadow: var(--shadow-sm) !important;
  z-index: 1000 !important;
}

/* Layout container */
section.main > div.block-container {
  padding-top: 1.25rem !important;
  padding-bottom: 5rem !important;
  max-width: 1240px !important;
}

/* Typography */
h1, h2, h3, h4 {
  font-family: 'Inter', sans-serif !important;
  color: var(--ink);
  letter-spacing: -0.015em;
  font-weight: 600;
}
p, li { font-family: 'Inter', sans-serif; color: var(--ink-2); }
::selection { background: var(--brand-100); color: var(--ink); }

/* ---------------- Top bar ---------------- */
.tt-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-xs);
  margin: 0 0 24px;
}
.tt-topbar-left { display: flex; align-items: center; gap: 14px; }
.tt-logo {
  width: 32px; height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--brand) 0%, #6E8BFF 100%);
  display: inline-flex; align-items: center; justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -0.02em;
  box-shadow: 0 2px 6px rgba(45,107,255,0.25);
}
.tt-wordmark {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.02em;
  color: var(--ink);
}
.tt-wordmark .tt-amp { color: var(--brand); margin: 0 1px; font-weight: 600; }
.tt-tagline {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: var(--ink-3);
  border-left: 1px solid var(--border);
  padding-left: 14px;
  margin-left: 4px;
}
.tt-issue {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--ink-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  padding: 4px 10px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}

/* ---------------- Hero search row ---------------- */
.tt-hero-label {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
  margin: 4px 0 8px;
}

/* Text input — main search */
section.main [data-testid="stTextInput"] input {
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important;
  font-weight: 400 !important;
  height: 46px !important;
  background: var(--surface) !important;
  color: var(--ink) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 0 16px !important;
  box-shadow: var(--shadow-xs) !important;
  transition: border-color 140ms ease, box-shadow 140ms ease;
}
section.main [data-testid="stTextInput"] input::placeholder {
  color: var(--ink-4) !important;
  font-weight: 400 !important;
}
section.main [data-testid="stTextInput"] input:focus {
  border-color: var(--brand) !important;
  outline: none !important;
  box-shadow: 0 0 0 4px var(--brand-50) !important;
}

/* Selectbox — jurisdiction */
section.main [data-testid="stSelectbox"] > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  min-height: 46px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: var(--ink) !important;
  box-shadow: var(--shadow-xs) !important;
}
section.main [data-testid="stSelectbox"] svg { color: var(--ink-3) !important; }

/* AI toggle */
section.main [data-testid="stToggle"] { margin-top: 12px; }
section.main [data-testid="stToggle"] label {
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--ink-2) !important;
}

/* ---------------- Example chips ---------------- */
.tt-chip-label {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-3);
  margin: 18px 0 10px;
}
.tt-chip-row {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 4px;
}
.tt-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--ink-2);
  border-radius: 999px;
  padding: 6px 14px;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  box-shadow: var(--shadow-xs);
  transition: all 140ms ease;
}
.tt-chip:hover {
  background: var(--brand-50);
  color: var(--brand-600);
  border-color: var(--brand-100);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.tt-chip-eg-mark {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--ink-4);
  font-weight: 500;
}
.tt-chip:hover .tt-chip-eg-mark { color: var(--brand); }

/* ---------------- Route caption ---------------- */
.tt-route-caption {
  display: flex; gap: 10px; align-items: center;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: var(--ink-3);
  margin: 28px 0 16px;
  font-weight: 500;
}
.tt-route-caption .tt-route-kind {
  display: inline-flex; align-items: center;
  background: var(--brand-50);
  color: var(--brand-600);
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.tt-route-caption .tt-route-count {
  margin-left: auto;
  color: var(--ink-3);
  font-size: 13px;
}

/* ---------------- Result card ---------------- */
.tt-card {
  padding: 20px 22px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-xs);
  margin-bottom: 14px;
  scroll-margin-top: 100px;
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}
.tt-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.tt-card-meta {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.tt-citation {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--brand-600);
  background: var(--brand-50);
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.02em;
}

.tt-card-title {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600;
  font-size: 17px;
  line-height: 1.4;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
  color: var(--ink);
}

.tt-card-body {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-2);
}
.tt-card-body mark, .tt-card-body b {
  background: var(--highlight);
  color: var(--ink);
  font-weight: 600;
  padding: 0 3px;
  border-radius: 3px;
}

.tt-card-rationale {
  margin-top: 12px;
  padding: 10px 14px;
  background: var(--surface-2);
  border-left: 3px solid var(--brand);
  border-radius: var(--radius-xs);
  font-size: 13px;
  line-height: 1.55;
  color: var(--ink-2);
}
.tt-card-rationale strong { color: var(--ink); font-weight: 600; }

.tt-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.tt-tag {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  padding: 3px 9px;
  border-radius: 6px;
}
.tt-tag::before { content: "#"; color: var(--ink-4); margin-right: 2px; }

.tt-card-source { margin-top: 12px; }
.tt-card-source a {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: var(--brand-600);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.tt-card-source a:hover { text-decoration: underline; }

/* In-card buttons */
section.main [data-testid="stButton"] > button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--ink-2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 6px 12px !important;
  border-radius: var(--radius-xs) !important;
  height: auto !important;
  min-height: 0 !important;
  width: auto !important;
  box-shadow: var(--shadow-xs) !important;
  transition: all 140ms ease !important;
}
section.main [data-testid="stButton"] > button:hover {
  background: var(--surface-2) !important;
  border-color: var(--border-strong) !important;
  color: var(--ink) !important;
}
section.main [data-testid="stButton"] > button:focus {
  box-shadow: 0 0 0 3px var(--brand-50) !important;
  outline: none !important;
}

/* Expander */
section.main [data-testid="stExpander"] summary {
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--ink-2) !important;
  padding: 8px 0 !important;
  background: transparent !important;
  border: none !important;
}
section.main [data-testid="stExpander"] summary:hover { color: var(--brand-600) !important; }
section.main [data-testid="stExpander"] details { background: transparent !important; border: none !important; }
section.main [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 14px 16px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13.5px !important;
  color: var(--ink-2) !important;
  line-height: 1.6 !important;
  margin-top: 8px !important;
}

/* ---------------- Sidebar (Case File) ---------------- */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container {
  padding-top: 28px !important;
  padding-left: 22px !important;
  padding-right: 22px !important;
}

.tt-sidebar-eyebrow {
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  font-weight: 500;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 6px;
}
.tt-sidebar-title {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 18px;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin: 0 0 4px;
  display: flex; align-items: center; gap: 8px;
}
.tt-sidebar-title .tt-badge {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 11px;
  color: var(--brand-600);
  background: var(--brand-50);
  border-radius: 999px;
  padding: 2px 8px;
}
.tt-sidebar-rule { height: 1px; background: var(--border); margin: 14px 0 18px; }
.tt-sidebar-empty {
  font-family: 'Inter', sans-serif;
  font-size: 13.5px;
  color: var(--ink-3);
  line-height: 1.55;
  background: var(--surface-2);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-sm);
  padding: 16px;
  text-align: center;
}

.tt-pinned-item {
  padding: 12px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  transition: border-color 140ms ease;
}
.tt-pinned-item:hover { border-color: var(--border-strong); }
.tt-pinned-cite {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--brand-600);
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}
.tt-pinned-title {
  font-family: 'Inter', sans-serif;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.35;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] [data-testid="stButton"] > button,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: var(--surface) !important;
  color: var(--ink-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 9px 14px !important;
  height: auto !important;
  box-shadow: var(--shadow-xs) !important;
  transition: all 140ms ease !important;
}
section[data-testid="stSidebar"] [data-testid="stButton"] > button:hover,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: var(--surface-2) !important;
  border-color: var(--border-strong) !important;
  color: var(--ink) !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: var(--brand) !important;
  color: white !important;
  border-color: var(--brand) !important;
  box-shadow: 0 1px 2px rgba(45,107,255,0.25) !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: var(--brand-600) !important;
  border-color: var(--brand-600) !important;
  color: white !important;
}

.tt-unpin-marker { display: none; }
.tt-unpin-marker + div [data-testid="stButton"] > button {
  background: transparent !important;
  color: var(--ink-3) !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 12px !important;
  padding: 4px 0 8px !important;
  text-align: left !important;
}
.tt-unpin-marker + div [data-testid="stButton"] > button:hover {
  background: transparent !important;
  color: #B42318 !important;
}

/* ---------------- AI memo (answer-first layout) ---------------- */
.tt-memo {
  position: sticky;
  top: 24px;
  padding: 24px 28px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}
.tt-memo-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--brand-600);
  background: var(--brand-50);
  padding: 4px 10px;
  border-radius: 999px;
  margin-bottom: 14px;
}
.tt-memo-eyebrow::before {
  content: "";
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--brand);
}
.tt-memo h2 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600;
  font-size: 20px;
  letter-spacing: -0.01em;
  margin: 0 0 4px;
  color: var(--ink);
}
.tt-memo-byline {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: var(--ink-3);
  margin: 0 0 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}
.tt-memo-byline em { color: var(--ink-2); font-style: normal; font-weight: 500; }
.tt-memo-body {
  font-family: 'Inter', sans-serif;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ink-2);
}
.tt-memo-body p { margin: 0 0 12px; }
.tt-memo-body strong { color: var(--ink-1); font-weight: 700; letter-spacing: 0.01em; }
.tt-memo-list {
  margin: 4px 0 14px;
  padding-left: 18px;
  list-style: none;
}
.tt-memo-list li {
  position: relative;
  margin: 0 0 8px;
  padding-left: 4px;
}
.tt-memo-list li::before {
  content: "";
  position: absolute;
  left: -12px;
  top: 0.7em;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--brand-600);
}

.tt-memo .tt-cite-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--brand-600);
  background: var(--brand-50);
  border-radius: 4px;
  padding: 1px 6px;
  text-decoration: none;
  margin: 0 1px;
  transition: background 140ms ease;
}
.tt-memo .tt-cite-pill:hover {
  background: var(--brand);
  color: white;
}

.tt-memo-fallback {
  font-family: 'Inter', sans-serif;
  font-size: 13.5px;
  color: var(--ink-3);
  line-height: 1.55;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
}
.tt-memo-fallback code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  background: var(--surface-3);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--ink);
}

/* ---------------- Empty state explainer ---------------- */
.tt-explainer {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 32px;
}
.tt-mode-card {
  padding: 22px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-xs);
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}
.tt-mode-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.tt-mode-num {
  display: inline-flex;
  align-items: center; justify-content: center;
  width: 28px; height: 28px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--brand-600);
  background: var(--brand-50);
  border-radius: 8px;
  margin-bottom: 14px;
}
.tt-mode-card h4 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600;
  font-size: 16px;
  margin: 0 0 6px;
  color: var(--ink);
  letter-spacing: -0.01em;
}
.tt-mode-card p {
  font-family: 'Inter', sans-serif;
  font-size: 13.5px;
  color: var(--ink-3);
  line-height: 1.55;
  margin: 0 0 14px;
}
.tt-mode-eg {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: var(--ink-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 3px 9px;
}

/* ---------------- Skeleton loading ---------------- */
.tt-skel {
  padding: 20px 22px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-xs);
  margin-bottom: 14px;
}
.tt-skel-bar {
  height: 12px;
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface-3) 50%, var(--surface-2) 75%);
  background-size: 400% 100%;
  animation: tt-shimmer 1.4s infinite ease-in-out;
  border-radius: 4px;
}
@keyframes tt-shimmer { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }

/* ---------------- No-results ---------------- */
.tt-no-results {
  margin-top: 28px;
  padding: 40px 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-align: center;
}
.tt-no-results h3 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600;
  font-size: 18px;
  color: var(--ink);
  margin: 0 0 8px;
  letter-spacing: -0.01em;
}
.tt-no-results p {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: var(--ink-3);
  max-width: 520px;
  margin: 0 auto;
  line-height: 1.6;
}
.tt-no-results em {
  font-family: 'JetBrains Mono', monospace;
  font-style: normal;
  font-size: 12.5px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--ink-2);
}

/* ---------------- Misc ---------------- */
[data-testid="stHorizontalBlock"] { gap: 1rem; }
[data-baseweb="input"] { background: transparent !important; }
[data-testid="stMarkdownContainer"] a { color: var(--brand-600); }
hr { border-color: var(--border) !important; }
</style>
"""


def inject() -> None:
    """Inject CSS + fonts on every rerun (cheap; ensures live edits land)."""
    st.markdown(_CSS, unsafe_allow_html=True)
