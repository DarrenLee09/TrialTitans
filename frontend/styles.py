"""Dark glassmorphism CSS + font injection for the TrialTitans frontend."""
from __future__ import annotations

import streamlit as st

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
  /* ---- Base surfaces ---- */
  --bg-base:       #0A0C13;
  --bg:            #0F1117;
  --bg-elev-1:     #141722;
  --bg-elev-2:     #1A1E2C;

  /* Frosted glass surfaces (semi-transparent on the dark bg) */
  --glass:         rgba(255, 255, 255, 0.035);
  --glass-2:       rgba(255, 255, 255, 0.055);
  --glass-3:       rgba(255, 255, 255, 0.085);

  /* Hairline borders */
  --line:          rgba(255, 255, 255, 0.07);
  --line-2:        rgba(255, 255, 255, 0.12);
  --line-strong:   rgba(255, 255, 255, 0.18);

  /* Ink scale (light text on dark) */
  --ink:           #ECEDEE;
  --ink-2:         #B4B7BD;
  --ink-3:         #7E8189;
  --ink-4:         #5A5D66;

  /* Brand — violet, committed */
  --brand:         #8B5CF6;
  --brand-2:       #A78BFA;
  --brand-3:       #6366F1;
  --brand-soft:    rgba(139, 92, 246, 0.14);
  --brand-softer:  rgba(139, 92, 246, 0.08);
  --brand-border:  rgba(167, 139, 250, 0.32);
  --brand-glow:    rgba(139, 92, 246, 0.42);
  --gradient-cta:  linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  --gradient-cta-hover: linear-gradient(135deg, #9B6EF7 0%, #7677F1 100%);
  --gradient-text: linear-gradient(135deg, #C4B5FD 0%, #A78BFA 60%, #818CF8 100%);

  /* Functional accents */
  --emerald:       #34D399;
  --emerald-soft:  rgba(52, 211, 153, 0.12);
  --amber:         #FBBF24;
  --highlight:     rgba(167, 139, 250, 0.22);

  /* Geometry */
  --radius-xs: 8px;
  --radius-sm: 10px;
  --radius:    14px;
  --radius-lg: 18px;

  /* Elevation (soft on dark) */
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.30);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.32), 0 1px 2px rgba(0,0,0,0.20);
  --shadow-md: 0 8px 24px -8px rgba(0,0,0,0.50), 0 2px 6px rgba(0,0,0,0.25);
  --shadow-lg: 0 24px 48px -16px rgba(0,0,0,0.55), 0 6px 12px rgba(0,0,0,0.25);
  --shadow-glow: 0 0 0 1px var(--brand-border), 0 12px 36px -12px var(--brand-glow);

  /* Backdrop blur */
  --blur: saturate(140%) blur(14px);
}

/* ---------------- Base ---------------- */
html, body, [class*="css"] {
  font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* App background: gradient mesh + noise grain over deep navy */
.stApp {
  background:
    radial-gradient(ellipse 70% 45% at 50% -8%,  rgba(139, 92, 246, 0.20), transparent 60%),
    radial-gradient(ellipse 55% 40% at 88% 110%, rgba(99, 102, 241, 0.14), transparent 60%),
    radial-gradient(ellipse 40% 35% at 8%  60%,  rgba(168, 85, 247, 0.08), transparent 60%),
    var(--bg) !important;
  background-attachment: fixed !important;
  color: var(--ink) !important;
}
.stApp::before {
  content: "";
  position: fixed; inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.35;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.06 0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E");
}
section.main, section[data-testid="stSidebar"] { position: relative; z-index: 1; }

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

/* Sidebar collapse arrow */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  display: block !important;
  visibility: visible !important;
  background: var(--glass-2) !important;
  color: var(--ink-2) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: var(--radius-sm) !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
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
  font-family: 'Geist', sans-serif !important;
  color: var(--ink);
  letter-spacing: -0.018em;
  font-weight: 600;
}
p, li { font-family: 'Geist', sans-serif; color: var(--ink-2); }
::selection { background: var(--brand); color: white; }

/* ---------------- Top bar ---------------- */
.tt-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-sm);
  margin: 0 0 28px;
}
.tt-topbar-left { display: flex; align-items: center; gap: 14px; }
.tt-logo {
  width: 32px; height: 32px;
  border-radius: 9px;
  background: var(--gradient-cta);
  display: inline-flex; align-items: center; justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 13px;
  letter-spacing: -0.02em;
  box-shadow: 0 0 0 1px var(--brand-border), 0 6px 18px -6px var(--brand-glow);
}
.tt-wordmark {
  font-family: 'Geist', sans-serif;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.025em;
  color: var(--ink);
}
.tt-wordmark .tt-amp {
  background: var(--gradient-text);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0 1px;
}
.tt-tagline {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: var(--ink-3);
  border-left: 1px solid var(--line-2);
  padding-left: 14px;
  margin-left: 4px;
}
.tt-issue {
  font-family: 'Geist Mono', monospace;
  font-size: 11px;
  color: var(--ink-2);
  background: var(--glass-2);
  border: 1px solid var(--line);
  padding: 4px 10px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}

/* ---------------- Hero search ---------------- */
.tt-hero-label {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-2);
  margin: 4px 0 10px;
}

/* Text input */
section.main [data-testid="stTextInput"] input {
  font-family: 'Geist', sans-serif !important;
  font-size: 15px !important;
  font-weight: 400 !important;
  height: 48px !important;
  background: var(--glass) !important;
  color: var(--ink) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: var(--radius-sm) !important;
  padding: 0 16px !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
  box-shadow: var(--shadow-xs) !important;
  transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
}
section.main [data-testid="stTextInput"] input::placeholder {
  color: var(--ink-4) !important;
  font-weight: 400 !important;
}
section.main [data-testid="stTextInput"] input:hover {
  border-color: var(--line-strong) !important;
}
section.main [data-testid="stTextInput"] input:focus {
  border-color: var(--brand) !important;
  outline: none !important;
  box-shadow: 0 0 0 3px var(--brand-soft), 0 0 24px -6px var(--brand-glow) !important;
  background: var(--glass-2) !important;
}

/* Selectbox */
section.main [data-testid="stSelectbox"] > div > div {
  background: var(--glass) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: var(--radius-sm) !important;
  min-height: 48px !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 14px !important;
  color: var(--ink) !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
  box-shadow: var(--shadow-xs) !important;
}
section.main [data-testid="stSelectbox"] svg { color: var(--ink-3) !important; }
section.main [data-testid="stSelectbox"] div[role="combobox"] { color: var(--ink) !important; }

/* Selectbox dropdown panel (BaseWeb popover) */
[data-baseweb="popover"] [role="listbox"] {
  background: var(--bg-elev-2) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: var(--radius-sm) !important;
  box-shadow: var(--shadow-lg) !important;
}
[data-baseweb="popover"] [role="option"] {
  color: var(--ink-2) !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 13.5px !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: var(--glass-3) !important;
  color: var(--ink) !important;
}

/* Toggle */
section.main [data-testid="stToggle"] { margin-top: 14px; }
section.main [data-testid="stToggle"] label {
  font-family: 'Geist', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--ink-2) !important;
}
section.main [data-testid="stToggle"] [data-baseweb="checkbox"] div[role="checkbox"][aria-checked="true"] {
  background: var(--brand) !important;
  border-color: var(--brand) !important;
}

/* ---------------- Example chips ---------------- */
.tt-chip-label {
  font-family: 'Geist', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-3);
  margin: 22px 0 10px;
}
.tt-chip-row {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 4px;
}
.tt-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: var(--glass);
  border: 1px solid var(--line-2);
  color: var(--ink-2);
  border-radius: 999px;
  padding: 7px 14px;
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  transition: transform 160ms ease, background 160ms ease, border-color 160ms ease, color 160ms ease, box-shadow 160ms ease;
}
.tt-chip:hover {
  background: var(--brand-soft);
  color: var(--ink);
  border-color: var(--brand-border);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px -10px var(--brand-glow);
}
.tt-chip-eg-mark {
  font-family: 'Geist Mono', monospace;
  font-size: 11px;
  color: var(--ink-4);
  font-weight: 500;
}
.tt-chip:hover .tt-chip-eg-mark { color: var(--brand-2); }

/* ---------------- Route caption ---------------- */
.tt-route-caption {
  display: flex; gap: 10px; align-items: center;
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: var(--ink-3);
  margin: 32px 0 18px;
  font-weight: 500;
}
.tt-route-caption .tt-route-kind {
  display: inline-flex; align-items: center;
  background: var(--brand-soft);
  color: var(--brand-2);
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
  font-family: 'Geist Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border: 1px solid var(--brand-border);
}
.tt-route-caption .tt-route-count {
  margin-left: auto;
  color: var(--ink-3);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

/* ---------------- Result card (glass) ---------------- */
.tt-card {
  position: relative;
  padding: 22px 24px;
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-sm);
  margin-bottom: 14px;
  scroll-margin-top: 100px;
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease, background 180ms ease;
}
.tt-card:hover {
  border-color: var(--brand-border);
  background: var(--glass-2);
  box-shadow: 0 0 0 1px var(--brand-border), var(--shadow-md);
  transform: translateY(-1px);
}

.tt-card-meta {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.tt-meta-spacer { flex: 1; }

.tt-citation {
  font-family: 'Geist Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--brand-2);
  background: var(--brand-soft);
  border: 1px solid var(--brand-border);
  padding: 4px 10px;
  border-radius: 7px;
  letter-spacing: 0.02em;
}

.tt-live-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'Geist Mono', monospace;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--emerald);
  background: var(--emerald-soft);
  border: 1px solid rgba(52, 211, 153, 0.28);
  padding: 3px 9px 3px 8px;
  border-radius: 999px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.tt-live-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--emerald);
  box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.6);
  animation: tt-pulse 1.8s ease-out infinite;
}
@keyframes tt-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.55); }
  70%  { box-shadow: 0 0 0 7px rgba(52, 211, 153, 0); }
  100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
}

.tt-card-title {
  font-family: 'Geist', sans-serif !important;
  font-weight: 600;
  font-size: 17px;
  line-height: 1.4;
  letter-spacing: -0.012em;
  margin: 0 0 8px;
  color: var(--ink);
}

.tt-card-body {
  font-family: 'Geist', sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-2);
}
.tt-card-body mark, .tt-card-body b {
  background: var(--highlight);
  color: var(--ink);
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 4px;
}

.tt-card-rationale {
  margin-top: 14px;
  padding: 12px 14px 12px 16px;
  background: var(--brand-softer);
  border: 1px solid var(--brand-border);
  border-left: 3px solid var(--brand);
  border-radius: var(--radius-xs);
  font-size: 13px;
  line-height: 1.55;
  color: var(--ink-2);
}
.tt-card-rationale strong { color: var(--ink); font-weight: 600; }

.tt-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 14px; }
.tt-tag {
  font-family: 'Geist', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-2);
  background: var(--glass-2);
  border: 1px solid var(--line-2);
  padding: 3px 9px;
  border-radius: 7px;
}
.tt-tag::before { content: "#"; color: var(--ink-4); margin-right: 2px; }

.tt-card-source { margin-top: 14px; }
.tt-card-source a {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: var(--brand-2);
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: color 160ms ease;
}
.tt-card-source a:hover { color: var(--brand); text-decoration: underline; }

/* In-card buttons (glass) */
section.main [data-testid="stButton"] > button {
  background: var(--glass-2) !important;
  border: 1px solid var(--line-2) !important;
  color: var(--ink-2) !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 7px 13px !important;
  border-radius: var(--radius-xs) !important;
  height: auto !important;
  min-height: 0 !important;
  width: auto !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
  box-shadow: var(--shadow-xs) !important;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease !important;
}
section.main [data-testid="stButton"] > button:hover {
  background: var(--brand-soft) !important;
  border-color: var(--brand-border) !important;
  color: var(--ink) !important;
}
section.main [data-testid="stButton"] > button:focus {
  box-shadow: 0 0 0 3px var(--brand-soft), var(--shadow-xs) !important;
  outline: none !important;
}

/* Expander */
section.main [data-testid="stExpander"] summary {
  font-family: 'Geist', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  color: var(--ink-2) !important;
  padding: 8px 0 !important;
  background: transparent !important;
  border: none !important;
}
section.main [data-testid="stExpander"] summary:hover { color: var(--brand-2) !important; }
section.main [data-testid="stExpander"] details { background: transparent !important; border: none !important; }
section.main [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
  background: var(--glass) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: var(--radius-sm) !important;
  padding: 14px 16px !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 13.5px !important;
  color: var(--ink-2) !important;
  line-height: 1.6 !important;
  margin-top: 8px !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
}

/* ---------------- Sidebar (Case File) ---------------- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(20, 23, 34, 0.72) 0%, rgba(15, 17, 23, 0.86) 100%) !important;
  border-right: 1px solid var(--line) !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
}
section[data-testid="stSidebar"] .block-container {
  padding-top: 28px !important;
  padding-left: 22px !important;
  padding-right: 22px !important;
}

.tt-sidebar-eyebrow {
  font-family: 'Geist Mono', monospace;
  font-size: 10.5px;
  font-weight: 500;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.10em;
  margin-bottom: 6px;
}
.tt-sidebar-title {
  font-family: 'Geist', sans-serif;
  font-weight: 600;
  font-size: 19px;
  letter-spacing: -0.015em;
  color: var(--ink);
  margin: 0 0 4px;
  display: flex; align-items: center; gap: 8px;
}
.tt-sidebar-title .tt-badge {
  font-family: 'Geist Mono', monospace;
  font-weight: 600;
  font-size: 11px;
  color: var(--brand-2);
  background: var(--brand-soft);
  border: 1px solid var(--brand-border);
  border-radius: 999px;
  padding: 2px 8px;
}
.tt-sidebar-rule { height: 1px; background: var(--line); margin: 14px 0 18px; }
.tt-sidebar-empty {
  font-family: 'Geist', sans-serif;
  font-size: 13.5px;
  color: var(--ink-3);
  line-height: 1.55;
  background: var(--glass);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-sm);
  padding: 18px;
  text-align: center;
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
}

.tt-pinned-item {
  padding: 12px 14px;
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  transition: border-color 160ms ease, background 160ms ease;
}
.tt-pinned-item:hover {
  border-color: var(--brand-border);
  background: var(--glass-2);
}
.tt-pinned-cite {
  font-family: 'Geist Mono', monospace;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--brand-2);
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}
.tt-pinned-title {
  font-family: 'Geist', sans-serif;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.35;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] [data-testid="stButton"] > button,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: var(--glass-2) !important;
  color: var(--ink-2) !important;
  border: 1px solid var(--line-2) !important;
  border-radius: var(--radius-sm) !important;
  font-family: 'Geist', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 10px 14px !important;
  height: auto !important;
  backdrop-filter: var(--blur) !important;
  -webkit-backdrop-filter: var(--blur) !important;
  box-shadow: var(--shadow-xs) !important;
  transition: all 160ms ease !important;
}
section[data-testid="stSidebar"] [data-testid="stButton"] > button:hover,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: var(--brand-soft) !important;
  border-color: var(--brand-border) !important;
  color: var(--ink) !important;
}
/* Primary CTA: gradient export memo */
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: var(--gradient-cta) !important;
  color: white !important;
  border: 1px solid var(--brand-border) !important;
  box-shadow: 0 0 0 1px var(--brand-border), 0 8px 22px -8px var(--brand-glow) !important;
  font-weight: 600 !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: var(--gradient-cta-hover) !important;
  color: white !important;
  transform: translateY(-1px);
  box-shadow: 0 0 0 1px var(--brand-border), 0 12px 28px -8px var(--brand-glow) !important;
}

.tt-unpin-marker { display: none; }
.tt-unpin-marker + div [data-testid="stButton"] > button {
  background: transparent !important;
  color: var(--ink-3) !important;
  border: none !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  font-size: 12px !important;
  padding: 4px 0 8px !important;
  text-align: left !important;
}
.tt-unpin-marker + div [data-testid="stButton"] > button:hover {
  background: transparent !important;
  color: #FCA5A5 !important;
}

/* ---------------- AI memo rail (glass card) ---------------- */
.tt-memo {
  position: sticky;
  top: 24px;
  padding: 26px 28px 28px;
  background: var(--glass-2);
  border: 1px solid var(--line-2);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-md);
  overflow: hidden;
}
.tt-memo::before {
  content: "";
  position: absolute;
  inset: -1px -1px auto -1px;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--brand-border) 30%, var(--brand-border) 70%, transparent);
  opacity: 0.7;
}
.tt-memo-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: 'Geist Mono', monospace;
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--brand-2);
  background: var(--brand-soft);
  border: 1px solid var(--brand-border);
  padding: 4px 10px 4px 11px;
  border-radius: 999px;
  margin-bottom: 14px;
}
.tt-memo-eyebrow::before {
  content: "";
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--brand);
  box-shadow: 0 0 6px var(--brand-glow);
}
.tt-memo h2 {
  font-family: 'Geist', sans-serif !important;
  font-weight: 600;
  font-size: 22px;
  letter-spacing: -0.018em;
  margin: 0 0 6px;
  color: var(--ink);
  background: var(--gradient-text);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.tt-memo-byline {
  font-family: 'Geist', sans-serif;
  font-size: 13px;
  color: var(--ink-3);
  margin: 0 0 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
.tt-memo-byline em { color: var(--ink-2); font-style: normal; font-weight: 500; }

.tt-memo-body {
  font-family: 'Geist', sans-serif;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ink-2);
}
.tt-memo-body p { margin: 0 0 12px; color: var(--ink-2); }
.tt-memo-body strong { color: var(--ink); font-weight: 600; }

.tt-memo-list {
  margin: 6px 0 14px;
  padding: 0;
  list-style: none;
}
.tt-memo-list li {
  position: relative;
  padding: 4px 0 4px 22px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-2);
}
.tt-memo-list li::before {
  content: "";
  position: absolute;
  left: 6px; top: 13px;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--brand-2);
  box-shadow: 0 0 6px var(--brand-glow);
}

.tt-memo .tt-cite-pill {
  font-family: 'Geist Mono', monospace;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--brand-2);
  background: var(--brand-soft);
  border: 1px solid var(--brand-border);
  border-radius: 5px;
  padding: 1px 6px;
  text-decoration: none;
  margin: 0 1px;
  transition: background 140ms ease, color 140ms ease;
}
.tt-memo .tt-cite-pill:hover {
  background: var(--brand);
  color: white;
}

.tt-memo-fallback {
  font-family: 'Geist', sans-serif;
  font-size: 13.5px;
  color: var(--ink-3);
  line-height: 1.55;
  background: var(--glass);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
}
.tt-memo-fallback code {
  font-family: 'Geist Mono', monospace;
  font-size: 12px;
  background: var(--glass-3);
  border: 1px solid var(--line-2);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--ink);
}

/* ---------------- Empty state explainer ---------------- */
.tt-explainer {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 36px;
}
.tt-mode-card {
  padding: 22px;
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-sm);
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease, background 180ms ease;
}
.tt-mode-card:hover {
  border-color: var(--brand-border);
  background: var(--glass-2);
  box-shadow: 0 0 0 1px var(--brand-border), var(--shadow-md);
  transform: translateY(-2px);
}
.tt-mode-num {
  display: inline-flex;
  align-items: center; justify-content: center;
  width: 30px; height: 30px;
  font-family: 'Geist Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: white;
  background: var(--gradient-cta);
  border-radius: 9px;
  margin-bottom: 14px;
  box-shadow: 0 0 0 1px var(--brand-border), 0 6px 14px -6px var(--brand-glow);
}
.tt-mode-card h4 {
  font-family: 'Geist', sans-serif !important;
  font-weight: 600;
  font-size: 16px;
  margin: 0 0 6px;
  color: var(--ink);
  letter-spacing: -0.012em;
}
.tt-mode-card p {
  font-family: 'Geist', sans-serif;
  font-size: 13.5px;
  color: var(--ink-3);
  line-height: 1.55;
  margin: 0 0 14px;
}
.tt-mode-eg {
  display: inline-block;
  font-family: 'Geist Mono', monospace;
  font-size: 11.5px;
  color: var(--ink-2);
  background: var(--glass-2);
  border: 1px solid var(--line-2);
  border-radius: 6px;
  padding: 3px 9px;
}

/* ---------------- Skeleton loading ---------------- */
.tt-skel {
  padding: 22px 24px;
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-sm);
  margin-bottom: 14px;
}
.tt-skel-bar {
  height: 12px;
  background: linear-gradient(90deg, var(--glass) 25%, var(--glass-3) 50%, var(--glass) 75%);
  background-size: 400% 100%;
  animation: tt-shimmer 1.4s infinite ease-in-out;
  border-radius: 4px;
}
@keyframes tt-shimmer { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }

/* ---------------- No-results ---------------- */
.tt-no-results {
  margin-top: 28px;
  padding: 44px 24px;
  background: var(--glass);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  text-align: center;
}
.tt-no-results h3 {
  font-family: 'Geist', sans-serif !important;
  font-weight: 600;
  font-size: 19px;
  color: var(--ink);
  margin: 0 0 8px;
  letter-spacing: -0.012em;
}
.tt-no-results p {
  font-family: 'Geist', sans-serif;
  font-size: 14px;
  color: var(--ink-3);
  max-width: 540px;
  margin: 0 auto;
  line-height: 1.6;
}
.tt-no-results em {
  font-family: 'Geist Mono', monospace;
  font-style: normal;
  font-size: 12.5px;
  background: var(--glass-2);
  border: 1px solid var(--line-2);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--ink-2);
}

/* Spinner — match brand */
.stSpinner > div > div { border-top-color: var(--brand) !important; }

/* ---------------- Case-file view (Organizer) ---------------- */
.tt-case-summary {
  padding: 22px 24px;
  background: var(--glass-2);
  border: 1px solid var(--line-2);
  border-radius: var(--radius);
  backdrop-filter: var(--blur);
  -webkit-backdrop-filter: var(--blur);
  box-shadow: var(--shadow-sm);
  margin: 16px 0 24px;
}
.tt-case-summary h3 {
  font-family: 'Geist Mono', monospace !important;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-size: 11px;
  font-weight: 600;
  color: var(--brand-2);
  margin: 0 0 10px;
}
.tt-case-summary p {
  font-family: 'Geist', sans-serif;
  font-size: 14.5px;
  line-height: 1.65;
  color: var(--ink);
  margin: 0;
  white-space: pre-wrap;
}
.tt-section-label {
  font-family: 'Geist Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-2);
  margin: 28px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

/* ---------------- Misc ---------------- */
[data-testid="stHorizontalBlock"] { gap: 1rem; }
[data-baseweb="input"] { background: transparent !important; }
[data-testid="stMarkdownContainer"] a { color: var(--brand-2); }
[data-testid="stMarkdownContainer"] a:hover { color: var(--brand); }
hr { border-color: var(--line) !important; }

/* Scrollbar (webkit) */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--glass-3);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background: var(--line-strong); background-clip: padding-box; }
</style>
"""


def inject() -> None:
    """Inject CSS + fonts on every rerun (cheap; ensures live edits land)."""
    st.markdown(_CSS, unsafe_allow_html=True)
