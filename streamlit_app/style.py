"""shared style constants and a function that injects the page's CSS.

palette inspiration is a warm cream-paper-and-deep-burgundy aesthetic, kept
deliberately analog so it doesn't feel like a dashboard. Manrope for prose,
JetBrains Mono for numbers and metrics.
"""

PALETTE = {
    "paper": "#f5efe6",
    "ink": "#1f1c1a",
    "ink_soft": "#5b524a",
    "accent": "#8b3a3a",       # burgundy
    "accent_soft": "#c98882",
    "secondary": "#b8924a",    # warm gold
    "card": "#ffffff",
    "border": "#e6dccd",
    "mute": "#b1a89b",
}


def inject_css() -> str:
    p = PALETTE
    return f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

      html, body, [class*="css"] {{
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
        background: {p["paper"]};
        color: {p["ink"]};
      }}
      .stApp {{ background: {p["paper"]}; }}
      .block-container {{ max-width: 1080px; padding-top: 2.5rem; padding-bottom: 4rem; }}

      h1, h2, h3, h4 {{
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: {p["ink"]};
      }}
      h1 {{ font-size: 2.4rem; line-height: 1.15; }}
      h2 {{ font-size: 1.45rem; margin-top: 2.4rem; }}
      h3 {{ font-size: 1.1rem; }}
      p, li {{ color: {p["ink_soft"]}; line-height: 1.55; }}

      .metric, .numeric, code, pre, .stCode, .mono {{
        font-family: 'JetBrains Mono', monospace;
      }}

      .card {{
        background: {p["card"]};
        border: 1px solid {p["border"]};
        border-radius: 6px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
      }}
      .card:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(31, 28, 26, 0.06);
      }}
      .rec-card {{ display: grid; grid-template-columns: 1.4rem 1fr auto; gap: 0.9rem; align-items: baseline; }}
      .rec-rank {{ font-family: 'JetBrains Mono', monospace; color: {p["mute"]}; font-weight: 500; }}
      .rec-title {{ color: {p["ink"]}; font-weight: 600; }}
      .rec-artist {{ color: {p["ink_soft"]}; font-size: 0.92rem; margin-top: 2px; }}
      .rec-meta {{ font-family: 'JetBrains Mono', monospace; color: {p["accent"]}; font-size: 0.82rem; }}

      .badge {{
        display: inline-block;
        padding: 1px 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: {p["accent"]};
        background: #fbeeec;
        border-radius: 999px;
        margin-right: 6px;
      }}

      .stButton > button {{
        background: {p["accent"]};
        color: #fff;
        border: none;
        border-radius: 4px;
        padding: 0.55rem 1.1rem;
        font-weight: 600;
        transition: background 0.15s ease;
      }}
      .stButton > button:hover {{ background: #6f2828; color: #fff; }}

      .stTabs [data-baseweb="tab-list"] {{ gap: 1.5rem; border-bottom: 1px solid {p["border"]}; }}
      .stTabs [data-baseweb="tab"] {{
        color: {p["ink_soft"]};
        padding: 6px 0;
        font-weight: 600;
      }}
      .stTabs [aria-selected="true"] {{ color: {p["accent"]}; border-bottom: 2px solid {p["accent"]}; }}

      table {{ font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; }}
      th {{ color: {p["ink"]}; }}
      td {{ color: {p["ink_soft"]}; }}

      hr {{ border: none; border-top: 1px solid {p["border"]}; margin: 2rem 0; }}

      .lede {{ font-size: 1.05rem; color: {p["ink_soft"]}; max-width: 70ch; line-height: 1.6; }}
    </style>
    """
