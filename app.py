"""
IPL Toss-based Match Prediction Web App
----------------------------------------
No external dependencies required — uses Python stdlib only.

Run:
    python app.py

Then open http://127.0.0.1:5000 in your browser.
"""

import csv
import json
import os
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# ──────────────────────────────────────────
# 1. Load & index the CSV data
# ──────────────────────────────────────────

CSV_FILE = os.path.join(os.path.dirname(__file__), "matches.csv")


def load_matches(path: str) -> list[dict]:
    """Read all rows from the CSV file and return them as a list of dicts."""
    matches = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    return matches


MATCHES = load_matches(CSV_FILE)

# Derive unique values for dropdowns
TEAMS = sorted(
    {m["team1"] for m in MATCHES} | {m["team2"] for m in MATCHES}
)
CITIES = sorted({m["city"] for m in MATCHES if m["city"]})
TOSS_DECISIONS = ["bat", "field"]


# ──────────────────────────────────────────
# 2. Prediction / stats logic
# ──────────────────────────────────────────

def win_stats(
    team1: str,
    team2: str,
    toss_winner: str,
    toss_decision: str,
    city: str,
) -> dict:
    """
    Return historical win statistics and a simple prediction based on
    toss outcome, head-to-head record, and venue performance.
    """
    head_to_head: dict[str, int] = defaultdict(int)
    toss_wins: dict[str, int] = defaultdict(int)  # wins after winning toss
    venue_wins: dict[str, int] = defaultdict(int)

    for m in MATCHES:
        teams = {m["team1"], m["team2"]}
        if teams != {team1, team2}:
            continue

        winner = m["winner"]
        if not winner:
            continue

        # head-to-head
        head_to_head[winner] += 1

        # toss-decision wins
        if (
            m["toss_winner"] == toss_winner
            and m["toss_decision"] == toss_decision
        ):
            toss_wins[winner] += 1

        # venue wins
        if m["city"] == city:
            venue_wins[winner] += 1

    total_h2h = sum(head_to_head.values())

    # Simple scoring heuristic (weights are illustrative)
    scores: dict[str, float] = {team1: 0.0, team2: 0.0}
    for team in (team1, team2):
        h2h_pct = head_to_head[team] / max(total_h2h, 1)
        toss_pct = toss_wins[team] / max(sum(toss_wins.values()), 1)
        venue_pct = venue_wins[team] / max(sum(venue_wins.values()), 1)
        scores[team] = 0.4 * h2h_pct + 0.35 * toss_pct + 0.25 * venue_pct

    predicted_winner = max(scores, key=scores.__getitem__)
    confidence = round(
        scores[predicted_winner]
        / max(sum(scores.values()), 0.001)
        * 100,
        1,
    )

    return {
        "predicted_winner": predicted_winner,
        "confidence_pct": confidence,
        "head_to_head": dict(head_to_head),
        "total_matches": total_h2h,
        "venue_wins": dict(venue_wins),
        "toss_condition_wins": dict(toss_wins),
    }


# ──────────────────────────────────────────
# 3. Inline HTML frontend
# ──────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>IPL Toss Predictor</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }}
    .card {{
      background: rgba(255,255,255,0.07);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 18px;
      padding: 36px 40px;
      max-width: 600px;
      width: 100%;
      color: #e0e0e0;
    }}
    h1 {{ font-size: 1.7rem; color: #f5c518; margin-bottom: 6px; }}
    p.subtitle {{ font-size: 0.9rem; color: #a0aec0; margin-bottom: 28px; }}
    label {{ display: block; margin-bottom: 6px; font-size: 0.85rem; color: #cbd5e0; font-weight: 600; }}
    select {{
      width: 100%; padding: 10px 12px; border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.2);
      background: rgba(255,255,255,0.1); color: #fff;
      font-size: 0.95rem; margin-bottom: 20px; cursor: pointer;
    }}
    select option {{ background: #1a1a2e; }}
    button {{
      width: 100%; padding: 12px; border: none; border-radius: 10px;
      background: linear-gradient(90deg, #f5c518, #e67e22);
      color: #1a1a2e; font-size: 1rem; font-weight: 700; cursor: pointer;
      transition: opacity 0.2s;
    }}
    button:hover {{ opacity: 0.88; }}
    #result {{
      margin-top: 28px; padding: 20px; border-radius: 12px;
      background: rgba(245, 197, 24, 0.08);
      border: 1px solid rgba(245, 197, 24, 0.3);
      display: none;
    }}
    #result h2 {{ color: #f5c518; font-size: 1.2rem; margin-bottom: 12px; }}
    .stat-row {{ display: flex; justify-content: space-between; margin: 6px 0; font-size: 0.9rem; }}
    .stat-label {{ color: #a0aec0; }}
    .stat-value {{ font-weight: 600; color: #fff; }}
    .winner-badge {{
      display: inline-block; background: #f5c518; color: #1a1a2e;
      padding: 4px 14px; border-radius: 20px; font-weight: 700;
      font-size: 1.05rem; margin-bottom: 16px;
    }}
    #error {{
      margin-top: 16px; color: #fc8181; font-size: 0.9rem; display: none;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>🏏 IPL Toss Predictor</h1>
    <p class="subtitle">Select match details to get a data-driven win prediction.</p>

    <label for="team1">Team 1</label>
    <select id="team1">{team_options}</select>

    <label for="team2">Team 2</label>
    <select id="team2">{team_options}</select>

    <label for="toss_winner">Toss Winner</label>
    <select id="toss_winner">{team_options}</select>

    <label for="toss_decision">Toss Decision</label>
    <select id="toss_decision">
      <option value="bat">Bat</option>
      <option value="field">Field</option>
    </select>

    <label for="city">Venue City</label>
    <select id="city">{city_options}</select>

    <button onclick="predict()">Predict Winner</button>

    <div id="error"></div>

    <div id="result">
      <h2>Prediction</h2>
      <div class="winner-badge" id="predicted_winner"></div>
      <div class="stat-row">
        <span class="stat-label">Confidence</span>
        <span class="stat-value" id="confidence"></span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Total H2H Matches</span>
        <span class="stat-value" id="total_matches"></span>
      </div>
      <div class="stat-row">
        <span class="stat-label">H2H Wins</span>
        <span class="stat-value" id="h2h_wins"></span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Wins at Venue</span>
        <span class="stat-value" id="venue_wins"></span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Wins with Same Toss Outcome</span>
        <span class="stat-value" id="toss_wins"></span>
      </div>
    </div>
  </div>

  <script>
    async function predict() {{
      const team1 = document.getElementById('team1').value;
      const team2 = document.getElementById('team2').value;
      const toss_winner = document.getElementById('toss_winner').value;
      const toss_decision = document.getElementById('toss_decision').value;
      const city = document.getElementById('city').value;

      const errEl = document.getElementById('error');
      errEl.style.display = 'none';

      if (team1 === team2) {{
        errEl.textContent = 'Team 1 and Team 2 must be different.';
        errEl.style.display = 'block';
        document.getElementById('result').style.display = 'none';
        return;
      }}
      if (toss_winner !== team1 && toss_winner !== team2) {{
        errEl.textContent = 'Toss winner must be one of the two selected teams.';
        errEl.style.display = 'block';
        document.getElementById('result').style.display = 'none';
        return;
      }}

      const params = new URLSearchParams({{team1, team2, toss_winner, toss_decision, city}});
      const res = await fetch('/api/predict?' + params.toString());
      const data = await res.json();

      if (data.error) {{
        errEl.textContent = data.error;
        errEl.style.display = 'block';
        document.getElementById('result').style.display = 'none';
        return;
      }}

      document.getElementById('predicted_winner').textContent = '🏆 ' + data.predicted_winner;
      document.getElementById('confidence').textContent = data.confidence_pct + '%';
      document.getElementById('total_matches').textContent = data.total_matches;

      const h2h = data.head_to_head;
      document.getElementById('h2h_wins').textContent =
        team1 + ': ' + (h2h[team1] || 0) + '  |  ' + team2 + ': ' + (h2h[team2] || 0);

      const vw = data.venue_wins;
      document.getElementById('venue_wins').textContent =
        team1 + ': ' + (vw[team1] || 0) + '  |  ' + team2 + ': ' + (vw[team2] || 0);

      const tw = data.toss_condition_wins;
      document.getElementById('toss_wins').textContent =
        team1 + ': ' + (tw[team1] || 0) + '  |  ' + team2 + ': ' + (tw[team2] || 0);

      document.getElementById('result').style.display = 'block';
    }}
  </script>
</body>
</html>
"""


def build_html() -> str:
    team_opts = "\n".join(
        f'      <option value="{t}">{t}</option>' for t in TEAMS
    )
    city_opts = "\n".join(
        f'      <option value="{c}">{c}</option>' for c in CITIES
    )
    return HTML_TEMPLATE.format(team_options=team_opts, city_options=city_opts)


# ──────────────────────────────────────────
# 4. HTTP request handler (stdlib only)
# ──────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler — no external libraries required."""

    def log_message(self, fmt, *args):  # quiet the default access log
        print(f"  {self.address_string()} - {fmt % args}")

    def _send(self, code: int, content_type: str, body: str | bytes):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self._send(200, "text/html; charset=utf-8", build_html())

        elif parsed.path == "/api/teams":
            self._send(
                200,
                "application/json",
                json.dumps({
                    "teams": TEAMS,
                    "cities": CITIES,
                    "toss_decisions": TOSS_DECISIONS,
                }),
            )

        elif parsed.path == "/api/predict":
            params = parse_qs(parsed.query)

            def p(key):
                return params.get(key, [""])[0].strip()

            team1 = p("team1")
            team2 = p("team2")
            toss_winner = p("toss_winner")
            toss_decision = p("toss_decision")
            city = p("city")

            # Basic validation
            all_teams = set(TEAMS)
            errors = []
            if team1 not in all_teams:
                errors.append(f"Unknown team1: '{team1}'")
            if team2 not in all_teams:
                errors.append(f"Unknown team2: '{team2}'")
            if team1 == team2:
                errors.append("team1 and team2 must be different")
            if toss_winner not in {team1, team2}:
                errors.append("toss_winner must be team1 or team2")
            if toss_decision not in TOSS_DECISIONS:
                errors.append(f"toss_decision must be one of {TOSS_DECISIONS}")
            if city not in CITIES:
                errors.append(f"Unknown city: '{city}'")

            if errors:
                self._send(
                    400,
                    "application/json",
                    json.dumps({"error": "; ".join(errors)}),
                )
                return

            result = win_stats(team1, team2, toss_winner, toss_decision, city)
            self._send(200, "application/json", json.dumps(result))

        else:
            self._send(404, "text/plain", "Not found")


# ──────────────────────────────────────────
# 5. Entry point
# ──────────────────────────────────────────

if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 5000
    server = HTTPServer((HOST, PORT), Handler)
    print(f"🏏 IPL Toss Predictor running at http://{HOST}:{PORT}")
    print("   Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
