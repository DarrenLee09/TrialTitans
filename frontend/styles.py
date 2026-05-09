"""Editorial-legal CSS + font injection for the TrialTitans frontend."""
from __future__ import annotations

import streamlit as st

_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700;9..144,800&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500;6..72,600;6..72,700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
  --ink: #1A1614;
  --ink-soft: #4A413B;
  --ink-faint: #8C8278;
  --paper: #F4EDDB;
  --paper-deep: #ECE3CB;
  --paper-darker: #DFD3B5;
  --rule: #C7B89C;
  --rule-soft: #D9CDB1;
  --accent: #7A1F2B;
  --accent-soft: #B65A66;
  --accent-haze: rgba(122, 31, 43, 0.08);
  --navy: #1F2D4A;
  --highlight: rgba(193, 145, 56, 0.28);
  --radius-card: 4px;
}

/* ---------------- Base + paper background with noise ---------------- */
html, body, [class*="css"] {
  font-family: 'Newsreader', Georgia, serif;
  font-variant-numeric: oldstyle-nums;
  color: var(--ink);
}

.stApp {
  background:
    url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 240 240' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.92' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.10  0 0 0 0 0.08  0 0 0 0 0.06  0 0 0 0.06 0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)'/%3E%3C/svg%3E"),
    var(--paper) !important;
  background-blend-mode: multiply;
}

/* Streamlit chrome: keep header so the sidebar collapse arrow remains visible */
#MainMenu, footer { display: none !important; }
header[data-testid="stHeader"] {
  background: transparent !important;
  height: auto !important;
  box-shadow: none !important;
}
header[data-testid="stHeader"] [data-testid="stToolbar"] { display: none !important; }
header[data-testid="stHeader"] [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] [data-testid="stStatusWidget"] { display: none !important; }

/* Sidebar collapse/expand arrow — make sure it stays visible */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
  display: block !important;
  visibility: visible !important;
  background: var(--paper) !important;
  color: var(--ink) !important;
  border: 1px solid var(--rule) !important;
  border-radius: var(--radius-card) !important;
  z-index: 1000 !important;
}

/* Layout container */
section.main > div.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 5rem !important;
  max-width: 1280px !important;
}

/* ---------------- Typography ---------------- */
h1, h2, h3, h4, .tt-serif {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 600;
  letter-spacing: -0.015em;
  color: var(--ink);
}

p, li { font-family: 'Newsreader', serif; }

::selection { background: var(--accent); color: var(--paper); }

/* ---------------- Top bar ---------------- */
.tt-topbar {
  display: flex; align-items: flex-end; justify-content: space-between;
  border-bottom: 1px solid var(--ink);
  padding: 6px 2px 14px;
  margin: 0 0 28px;
}
.tt-topbar-left { display: flex; align-items: baseline; gap: 18px; }
.tt-wordmark {
  font-family: 'Fraunces', serif;
  font-weight: 800;
  font-size: 30px;
  letter-spacing: -0.02em;
  color: var(--ink);
  text-transform: uppercase;
}
.tt-wordmark .tt-amp {
  font-style: italic;
  font-weight: 500;
  color: var(--accent);
  margin: 0 2px;
  font-size: 0.9em;
}
.tt-tagline {
  font-family: 'Newsreader', serif;
  font-style: italic;
  color: var(--ink-soft);
  font-size: 14px;
}
.tt-issue {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 10px;
  color: var(--ink-soft);
  font-variant-numeric: lining-nums;
  white-space: nowrap;
}

/* ---------------- Hero search row ---------------- */
.tt-hero-label {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  font-size: 10px;
  color: var(--ink-soft);
  margin: 6px 0 8px;
}

/* Text input (only one in main area — the hero search) */
section.main [data-testid="stTextInput"] input {
  font-family: 'Fraunces', serif !important;
  font-size: 22px !important;
  font-weight: 500 !important;
  height: 60px !important;
  background: var(--paper-deep) !important;
  color: var(--ink) !important;
  border: 1px solid var(--ink) !important;
  border-radius: var(--radius-card) !important;
  padding: 0 18px !important;
  letter-spacing: -0.005em !important;
}
section.main [data-testid="stTextInput"] input::placeholder {
  color: var(--ink-faint) !important;
  font-style: italic !important;
  font-weight: 400 !important;
}
section.main [data-testid="stTextInput"] input:focus {
  border-color: var(--accent) !important;
  outline: 3px solid var(--accent-haze) !important;
  outline-offset: 0 !important;
}

/* Selectbox (only one in main area — jurisdiction) */
section.main [data-testid="stSelectbox"] > div > div {
  background: var(--paper-deep) !important;
  border: 1px solid var(--ink) !important;
  border-radius: var(--radius-card) !important;
  min-height: 60px !important;
  font-family: 'Newsreader', serif !important;
  font-size: 14px !important;
  color: var(--ink) !important;
}
section.main [data-testid="stSelectbox"] svg { color: var(--ink) !important; }

/* AI toggle in hero row */
section.main [data-testid="stToggle"] { margin-top: 18px; }
section.main [data-testid="stToggle"] label {
  font-family: 'JetBrains Mono', monospace !important;
  text-transform: uppercase !important;
  letter-spacing: 0.16em !important;
  font-size: 10px !important;
  color: var(--ink-soft) !important;
}

/* ---------------- Example chips (HTML anchors) ---------------- */
.tt-chip-label {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  font-size: 9.5px;
  color: var(--ink-faint);
  margin: 18px 0 10px;
}
.tt-chip-row {
  display: flex; flex-wrap: wrap; gap: 10px;
  margin-bottom: 4px;
}
.tt-chip {
  display: inline-block;
  background: transparent;
  border: 1px solid var(--ink);
  color: var(--ink);
  border-radius: 999px;
  padding: 7px 16px;
  font-family: 'Newsreader', serif;
  font-size: 13.5px;
  font-style: italic;
  font-weight: 400;
  text-decoration: none;
  white-space: nowrap;
  transition: background 160ms ease, color 160ms ease, border-color 160ms ease;
}
.tt-chip:hover {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
}
.tt-chip-eg-mark {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-style: normal;
  color: var(--accent);
  margin-right: 6px;
  letter-spacing: 0.06em;
  font-variant-numeric: lining-nums;
}

/* ---------------- Result list (magazine TOC feel) ---------------- */
.tt-route-caption {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 10px;
  color: var(--ink-soft);
  margin: 24px 0 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--ink);
  display: flex; gap: 14px; align-items: baseline;
  font-variant-numeric: lining-nums;
}
.tt-route-caption .tt-route-kind { color: var(--accent); font-weight: 600; }
.tt-route-caption .tt-route-count { margin-left: auto; }

.tt-card {
  padding: 26px 0 22px;
  border-bottom: 1px solid var(--rule);
  scroll-margin-top: 100px;
  position: relative;
}
.tt-card:hover .tt-card-title { color: var(--accent); }

.tt-card-meta {
  display: flex; align-items: baseline; gap: 18px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-bottom: 10px;
  font-variant-numeric: lining-nums;
}
.tt-citation { color: var(--accent); font-weight: 600; }
.tt-citation::before { content: "["; opacity: 0.6; }
.tt-citation::after { content: "]"; opacity: 0.6; }

.tt-live-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink);
  background: rgba(34,139,82,0.12);
  border: 1px solid rgba(34,139,82,0.5);
  border-radius: 999px;
  padding: 2px 9px 2px 7px;
  font-variant-numeric: lining-nums;
}
.tt-live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #228b52;
  box-shadow: 0 0 0 0 rgba(34,139,82,0.7);
  animation: tt-live-pulse 1.6s ease-out infinite;
}
@keyframes tt-live-pulse {
  0%   { box-shadow: 0 0 0 0   rgba(34,139,82,0.55); }
  70%  { box-shadow: 0 0 0 6px rgba(34,139,82, 0); }
  100% { box-shadow: 0 0 0 0   rgba(34,139,82, 0); }
}
.tt-card-meta .tt-meta-spacer {
  flex: 1; border-bottom: 1px dotted var(--rule); transform: translateY(-2px);
}

.tt-card-title {
  font-family: 'Fraunces', serif !important;
  font-weight: 600;
  font-size: 26px;
  line-height: 1.18;
  letter-spacing: -0.015em;
  margin: 0 0 10px;
  color: var(--ink);
  transition: color 180ms ease;
}

.tt-card-body {
  font-family: 'Newsreader', serif;
  font-size: 16px;
  line-height: 1.62;
  color: var(--ink-soft);
  font-variant-numeric: oldstyle-nums;
  font-weight: 400;
}
.tt-card-body mark, .tt-card-body b {
  background: var(--highlight);
  color: var(--ink);
  font-weight: 500;
  padding: 0 2px;
}

.tt-tags { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 14px; }
.tt-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--ink-soft);
}
.tt-tag::before { content: "§ "; color: var(--accent); }

.tt-card-source { margin-top: 14px; }
.tt-card-source a {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--ink-soft);
  text-decoration: none;
  border-bottom: 1px dotted var(--ink-faint);
  padding-bottom: 1px;
}
.tt-card-source a:hover { color: var(--accent); border-bottom-color: var(--accent); }

/* In-card action buttons (Pin / Read full text). Style ALL main-area buttons
   as small mono-uppercase text links — pin is the only non-anchor button in
   the main area now that chips are HTML. */
section.main [data-testid="stButton"] > button {
  background: transparent !important;
  border: none !important;
  color: var(--ink-soft) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  padding: 4px 0 !important;
  height: auto !important;
  min-height: 0 !important;
  width: auto !important;
  text-align: left !important;
  font-weight: 500 !important;
  box-shadow: none !important;
}
section.main [data-testid="stButton"] > button:hover {
  color: var(--accent) !important;
  background: transparent !important;
}
section.main [data-testid="stButton"] > button:focus {
  box-shadow: none !important;
  outline: none !important;
}

section.main [data-testid="stExpander"] summary {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  letter-spacing: 0.18em !important;
  text-transform: uppercase !important;
  color: var(--ink-soft) !important;
  padding: 4px 0 !important;
  background: transparent !important;
  border: none !important;
}
section.main [data-testid="stExpander"] summary:hover { color: var(--accent) !important; }
section.main [data-testid="stExpander"] details { background: transparent !important; border: none !important; }
section.main [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
  background: var(--paper-deep) !important;
  border: 1px solid var(--rule) !important;
  border-radius: var(--radius-card) !important;
  padding: 14px 18px !important;
  font-family: 'Newsreader', serif !important;
  font-size: 14.5px !important;
  color: var(--ink) !important;
  line-height: 1.6 !important;
  margin-top: 8px !important;
}

/* ---------------- Sidebar (Case File) ---------------- */
section[data-testid="stSidebar"] {
  background:
    url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 240 240' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.92' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.10  0 0 0 0 0.08  0 0 0 0 0.06  0 0 0 0.08 0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)'/%3E%3C/svg%3E"),
    var(--paper-deep) !important;
  background-blend-mode: multiply !important;
  border-right: 1px solid var(--ink) !important;
}
section[data-testid="stSidebar"] .block-container {
  padding-top: 28px !important;
  padding-left: 22px !important;
  padding-right: 22px !important;
}

.tt-sidebar-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  font-size: 9.5px;
  color: var(--ink-faint);
  margin-bottom: 4px;
}
.tt-sidebar-title {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 24px;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin: 0 0 4px;
  display: flex; align-items: baseline; gap: 10px;
}
.tt-sidebar-title .tt-badge {
  font-family: 'JetBrains Mono', monospace;
  font-variant-numeric: lining-nums;
  font-weight: 500;
  font-size: 12px;
  color: var(--accent);
  background: transparent;
  border: 1px solid var(--accent);
  border-radius: 999px;
  padding: 1px 9px;
  letter-spacing: 0.04em;
}
.tt-sidebar-rule { height: 1px; background: var(--ink); margin: 14px 0 18px; }
.tt-sidebar-empty {
  font-family: 'Newsreader', serif;
  font-style: italic;
  font-size: 14px;
  color: var(--ink-soft);
  line-height: 1.55;
}

.tt-pinned-item {
  padding: 12px 0;
  border-bottom: 1px dotted var(--rule);
}
.tt-pinned-cite {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 600;
  font-variant-numeric: lining-nums;
  margin-bottom: 4px;
}
.tt-pinned-title {
  font-family: 'Fraunces', serif;
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.25;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] [data-testid="stButton"] > button,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: transparent !important;
  color: var(--ink) !important;
  border: 1px solid var(--ink) !important;
  border-radius: var(--radius-card) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10.5px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.18em !important;
  padding: 10px 12px !important;
  height: auto !important;
  font-weight: 500 !important;
  transition: background 160ms ease, color 160ms ease;
}
section[data-testid="stSidebar"] [data-testid="stButton"] > button:hover,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: var(--ink) !important;
  color: var(--paper) !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
  background: var(--accent) !important;
  color: var(--paper) !important;
  border-color: var(--accent) !important;
}
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button:hover {
  background: var(--ink) !important;
  border-color: var(--ink) !important;
}

.tt-unpin-marker { display: none; }
.tt-unpin-marker + div [data-testid="stButton"] > button {
  background: transparent !important;
  color: var(--ink-faint) !important;
  border: none !important;
  font-size: 9.5px !important;
  letter-spacing: 0.14em !important;
  padding: 2px 0 8px !important;
  text-align: left !important;
}
.tt-unpin-marker + div [data-testid="stButton"] > button:hover {
  color: var(--accent) !important;
}

/* ---------------- AI memo (answer-first layout) ---------------- */
.tt-memo {
  padding: 36px 44px 40px;
  margin: 16px 0 28px;
  background:
    url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 240 240' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.92' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.10  0 0 0 0 0.08  0 0 0 0 0.06  0 0 0 0.06 0'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)'/%3E%3C/svg%3E"),
    var(--paper-deep);
  background-blend-mode: multiply;
  border: 1px solid var(--ink);
  border-radius: var(--radius-card);
}
.tt-memo-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.22em;
  font-size: 10px;
  color: var(--ink-soft);
  margin-bottom: 6px;
}
.tt-memo h2 {
  font-family: 'Fraunces', serif !important;
  font-weight: 700;
  font-size: 36px;
  letter-spacing: -0.02em;
  margin: 0 0 4px;
  color: var(--ink);
}
.tt-memo-byline {
  font-family: 'Newsreader', serif;
  font-style: italic;
  font-size: 13px;
  color: var(--ink-soft);
  margin: 0 0 18px;
  border-bottom: 1px solid var(--ink);
  padding-bottom: 14px;
}
.tt-memo-body {
  font-family: 'Newsreader', serif;
  font-size: 17.5px;
  line-height: 1.72;
  color: var(--ink);
  font-variant-numeric: oldstyle-nums;
  text-align: justify;
  hyphens: auto;
}
.tt-memo-body p { margin: 0 0 14px; }
.tt-memo-body > p:first-of-type::first-letter,
.tt-memo-body::first-letter {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 4.4em;
  line-height: 0.84;
  float: left;
  padding: 8px 10px 0 0;
  color: var(--accent);
}

.tt-memo .tt-cite-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.06em;
  background: transparent;
  border-bottom: 1px dotted var(--accent);
  padding: 0 1px;
  text-decoration: none;
  margin: 0 1px;
  font-variant-numeric: lining-nums;
}
.tt-memo .tt-cite-pill:hover {
  background: var(--accent);
  color: var(--paper);
  border-bottom-color: var(--accent);
}

.tt-memo-fallback {
  font-family: 'Newsreader', serif;
  font-style: italic;
  font-size: 14px;
  color: var(--ink-soft);
  line-height: 1.6;
}
.tt-memo-fallback code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  background: var(--paper-darker);
  padding: 1px 5px;
  border-radius: 2px;
  color: var(--ink);
}

/* "Cited statutes" divider between memo and source cards */
.tt-sources-divider {
  display: flex; align-items: baseline; gap: 14px;
  margin: 36px 0 6px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--ink);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--ink);
  font-variant-numeric: lining-nums;
}
.tt-sources-divider .tt-sources-count {
  margin-left: auto; color: var(--accent); font-weight: 600;
}

/* ---------------- Empty / explainer cards ---------------- */
.tt-explainer {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  margin-top: 36px;
  border-top: 1px solid var(--ink);
}
.tt-mode-card {
  padding: 22px 24px 26px;
  border-right: 1px solid var(--rule);
}
.tt-mode-card:last-child { border-right: none; }
.tt-mode-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  letter-spacing: 0.18em;
  color: var(--ink-faint);
  margin-bottom: 8px;
  font-variant-numeric: lining-nums;
}
.tt-mode-card h4 {
  font-family: 'Fraunces', serif !important;
  font-weight: 600;
  font-size: 22px;
  margin: 0 0 8px;
  color: var(--ink);
  letter-spacing: -0.01em;
}
.tt-mode-card p {
  font-family: 'Newsreader', serif;
  font-size: 14px;
  color: var(--ink-soft);
  line-height: 1.55;
  margin: 0 0 14px;
}
.tt-mode-eg {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 999px;
  padding: 3px 10px;
  letter-spacing: 0.04em;
  font-variant-numeric: lining-nums;
}

/* ---------------- Skeleton loading ---------------- */
.tt-skel {
  padding: 26px 0 22px;
  border-bottom: 1px solid var(--rule);
}
.tt-skel-bar {
  height: 12px;
  background: linear-gradient(90deg, var(--paper-darker) 25%, var(--rule-soft) 50%, var(--paper-darker) 75%);
  background-size: 400% 100%;
  animation: tt-shimmer 1.4s infinite ease-in-out;
  border-radius: 2px;
}
@keyframes tt-shimmer { 0% { background-position: 100% 50%; } 100% { background-position: 0 50%; } }

/* ---------------- No-results ---------------- */
.tt-no-results {
  margin-top: 32px;
  padding: 32px 0;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--ink);
  text-align: center;
}
.tt-no-results h3 {
  font-family: 'Fraunces', serif !important;
  font-style: italic;
  font-weight: 500;
  font-size: 28px;
  color: var(--ink);
  margin: 0 0 10px;
}
.tt-no-results p {
  font-family: 'Newsreader', serif;
  font-style: italic;
  font-size: 15px;
  color: var(--ink-soft);
  max-width: 520px;
  margin: 0 auto;
  line-height: 1.55;
}

/* ---------------- Misc Streamlit overrides ---------------- */
[data-testid="stHorizontalBlock"] { gap: 1.5rem; }
[data-baseweb="input"] { background: transparent !important; }
[data-testid="stMarkdownContainer"] a { color: var(--accent); }
hr { border-color: var(--rule) !important; }
</style>
"""


def inject() -> None:
    """Inject CSS + fonts on every rerun (cheap; ensures live edits land)."""
    st.markdown(_CSS, unsafe_allow_html=True)
