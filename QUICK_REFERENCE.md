# Quick Reference Guide - IPL Toss Analyser

## 📚 What Each File Does

### 1. `backend/applogic.py` - Data Processing Engine
- **Purpose:** Loads IPL match data and pre-computes statistics
- **What it creates:**
  - `df` → DataFrame with all match data
  - `toss_match_stats` → Dict with toss/match statistics for each team
  - `bat_field_stats` → Dict with batting/fielding statistics
  - `venue_stats` → Dict with venue performance for each team
  - Visualizations (matplotlib figures)

### 2. `flask/app.py` - Backend Server & Routes
- **Purpose:** Receives requests from frontend, processes them, returns responses
- **Key Functions:**
  - `analyze_toss_comparison()` → Compare toss wins between two teams
  - `analyze_match_comparison()` → Compare match wins between two teams
  - `create_comparison_visualization()` → Create bar chart comparing teams
  - `get_single_team_stats()` → Get comprehensive stats for one team
  - `create_team_venue_heatmap()` → Create venue performance heatmap
  
- **Routes:**
  - `GET /` → Display main page (frontend.html)
  - `POST /analyze` → Analyze two teams, return comparison
  - `POST /stats` → Get single team statistics
  - `POST /venue-heatmap` → Get venue performance visualization
  - `GET /api/teams` → Get list of all teams

### 3. `templates/frontend.html` - User Interface
- **Purpose:** Display forms and results to user
- **Components:**
  - Dropdowns for team selection
  - Buttons for submitting analysis
  - Results display sections
  - JavaScript code to handle form submissions

---

## 🔄 Data Flow Explained Simply

```
FRONTEND (HTML) submits form
    ↓ JavaScript sends POST request
    ↓
FLASK (app.py) receives request
    ↓ Calls analysis function
    ↓
ANALYSIS FUNCTION queries applogic.py data
    ↓ Processes and formats results
    ↓
FLASK returns JSON response
    ↓ Includes data + base64 image
    ↓
JAVASCRIPT displays results
    ↓
USER sees comparison charts and statistics
```

---

## 🎯 Key Functions Explained

### `analyze_toss_comparison(team1, team2, venue=None)`

**Input:**
```python
team1 = "Mumbai Indians"
team2 = "Kolkata Knight Riders"
venue = "Eden Gardens"  # Optional, can be None
```

**Process:**
1. Filter `df` for matches where team1 vs team2
2. If venue specified, filter further by venue
3. Count how many times each team won toss
4. Calculate percentages
5. Determine which team has higher toss win %

**Output:**
```python
{
    'team1': 'Mumbai Indians',
    'team2': 'Kolkata Knight Riders',
    'venue': 'Eden Gardens',
    'matches': 12,
    'team1_toss_wins': 8,
    'team2_toss_wins': 4,
    'team1_toss_pct': 66.67,
    'team2_toss_pct': 33.33,
    'result': 'Mumbai Indians has HIGHER toss winning ratio'
}
```

---

### `analyze_match_comparison(team1, team2, venue=None)`

**Same as toss comparison, but counts MATCH WINS instead of toss wins**

---

### `create_comparison_visualization(team1, team2, venue=None)`

**Input:** Same as comparison functions

**Process:**
1. Call both comparison functions to get data
2. Create matplotlib figure with 2 subplots
3. LEFT chart: Toss wins comparison
4. RIGHT chart: Match wins comparison
5. Convert image to base64 string

**Output:** Base64 image string that can be embedded in HTML

---

### `get_single_team_stats(team)`

**Input:**
```python
team = "Mumbai Indians"
```

**Process:**
1. Fetch from `toss_match_stats[team]`
2. Fetch from `bat_field_stats[team]`
3. Format nicely as dictionary

**Output:**
```python
{
    'team': 'Mumbai Indians',
    'total_matches': 185,
    'toss_wins': 98,
    'toss_win_pct': 52.97,
    'match_wins': 114,
    'match_win_pct': 61.62,
    # ... more stats
}
```

---

### `create_team_venue_heatmap(team)`

**Input:**
```python
team = "Mumbai Indians"
```

**Process:**
1. Get `venue_stats[team]` (DataFrame with all venues)
2. Sort by win percentage
3. Create horizontal bar chart
4. Color code: RED (0%) to GREEN (100%)
5. Add labels showing wins/matches
6. Convert to base64 string

**Output:** Base64 image string

---

## 🔌 Flask Routes Explained

### Route: `POST /analyze`

**Frontend sends:**
```json
{
    "team1": "Mumbai Indians",
    "team2": "Kolkata Knight Riders",
    "venue": "Eden Gardens"
}
```

**Backend does:**
1. Extract team1, team2, venue from request
2. Validate input
3. Call analyze_toss_comparison()
4. Call analyze_match_comparison()
5. Call create_comparison_visualization()
6. Return JSON with all results + image

**Frontend receives:**
```json
{
    "success": true,
    "toss_analysis": { ... },
    "match_analysis": { ... },
    "graph": "data:image/png;base64,..."
}
```

---

### Route: `POST /stats`

**Frontend sends:**
```json
{
    "team": "Mumbai Indians"
}
```

**Backend does:**
1. Extract team from request
2. Call get_single_team_stats(team)
3. Return JSON with stats

---

### Route: `POST /venue-heatmap`

**Frontend sends:**
```json
{
    "team": "Mumbai Indians"
}
```

**Backend does:**
1. Extract team from request
2. Call create_team_venue_heatmap(team)
3. Return JSON with base64 image

---

## 📊 Understanding the Data

### What is `toss_match_stats`?

```python
toss_match_stats = {
    'Mumbai Indians': {
        'total_matches': 185,           # Total matches played
        'toss_wins': 98,                # Total toss wins
        'match_wins': 114,              # Total match wins
        'match_wins_after_toss_win': 68,# Matches won after winning toss
        'toss_win_pct': 52.97,          # Percentage of tosses won
        'match_win_pct': 61.62,         # Percentage of matches won
        'win_pct_after_toss_win': 69.39 # % wins when toss was won first
    },
    'Kolkata Knight Riders': {
        # ... similar structure
    },
    # ... all other teams
}
```

### What is `venue_stats`?

```python
venue_stats = {
    'Mumbai Indians': DataFrame with columns:
        ['venue', 'matches', 'wins', 'win_pct']
    # Each row represents one venue where team played (2+ matches)
    
    Example rows:
    venue                      matches  wins  win_pct
    Eden Gardens               12       8     66.67
    Wankhede Stadium           20       14    70.00
    MA Chidambaram Stadium     15       7     46.67
    # ... more venues
}
```

---

## 🎨 JavaScript in Frontend

### Form Submission Handler

```javascript
document.getElementById('analysisForm').addEventListener('submit', async (e) => {
    e.preventDefault();  // Prevent page reload
    
    // Get form values
    const team1 = document.getElementById('team1Select').value;
    const team2 = document.getElementById('team2Select').value;
    const venue = document.getElementById('venueSelect').value;
    
    // Validate
    if (!team1 || !team2) return showError('Please select both teams');
    
    // Send to Flask
    const formData = new FormData();
    formData.append('team1', team1);
    formData.append('team2', team2);
    formData.append('venue', venue);
    
    const response = await fetch('/analyze', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    
    // Display results
    displayAnalysisResults(data);
});
```

### Display Results Function

```javascript
function displayAnalysisResults(data) {
    // Build HTML with results
    const html = `
        <div class="result-card">
            <h4>Toss Analysis</h4>
            <p>${data.toss_analysis.result}</p>
        </div>
        <div class="result-card">
            <h4>Match Analysis</h4>
            <p>${data.match_analysis.result}</p>
        </div>
        <img src="${data.graph}" alt="Comparison">
    `;
    
    // Insert into page
    document.getElementById('analysisContent').innerHTML = html;
}
```

---

## 🔍 Example: How Venue Filter Works

**User scenario:** Compare MI vs KKR at Eden Gardens

**Step 1 - Frontend:**
```javascript
team1 = "Mumbai Indians"
team2 = "Kolkata Knight Riders"
venue = "Eden Gardens"
// Send to /analyze
```

**Step 2 - Flask in app.py:**
```python
@app.route('/analyze', methods=['POST'])
def analyze():
    team1 = "Mumbai Indians"
    team2 = "Kolkata Knight Riders"
    venue = "Eden Gardens"
    
    # Calls the function
    toss_result = analyze_toss_comparison(team1, team2, venue)
```

**Step 3 - analyze_toss_comparison() function:**
```python
# Filter all matches where MI vs KKR
matches = df[
    ((df['team1_name'] == "Mumbai Indians") & (df['team2_name'] == "Kolkata Knight Riders")) |
    ((df['team1_name'] == "Kolkata Knight Riders") & (df['team2_name'] == "Mumbai Indians"))
].copy()

# Filter by venue
matches = matches[matches['venue'] == "Eden Gardens"]

# Count toss wins
mi_toss_wins = (matches['toss_winner_name'] == "Mumbai Indians").sum()
kkr_toss_wins = (matches['toss_winner_name'] == "Kolkata Knight Riders").sum()

# Calculate percentages
mi_pct = (mi_toss_wins / len(matches) * 100)
kkr_pct = (kkr_toss_wins / len(matches) * 100)

# Return results
return {
    'venue': 'Eden Gardens',
    'matches': len(matches),
    'team1_toss_wins': mi_toss_wins,
    'team1_toss_pct': mi_pct,
    'team2_toss_wins': kkr_toss_wins,
    'team2_toss_pct': kkr_pct,
    # ... etc
}
```

**Step 4 - Frontend displays:**
- Results card showing MI vs KKR toss stats at Eden Gardens
- Chart comparing their performances

---

## 🚀 How to Run

1. **Make sure Flask is installed:**
   ```bash
   pip install flask pandas matplotlib seaborn
   ```

2. **Open terminal in project directory**

3. **Run Flask app:**
   ```bash
   python flask/app.py
   ```

4. **Open browser:**
   ```
   http://localhost:5000
   ```

5. **Use the application** to analyze teams!

---

## 💡 Key Points to Remember

1. **applogic.py runs once** when app.py imports it - loads and processes all data upfront
2. **Flask routes are fast** because they just query pre-computed dictionaries
3. **Base64 encoding** allows us to send images as JSON strings
4. **No database needed** - all data loaded from CSV into DataFrame in memory
5. **AJAX/Fetch** allows form submission without page reload
6. **JSON responses** make it easy for JavaScript to parse and display results

---

## 🎯 What Each Button Does

| Button | Route | Function Called | Returns |
|--------|-------|-----------------|---------|
| Analyse Winning Probability | `/analyze` | `analyze_toss_comparison()` + `analyze_match_comparison()` + `create_comparison_visualization()` | JSON with stats + image |
| View Historical Stats | `/stats` | `get_single_team_stats()` | JSON with team stats |
| View Venue Heatmap | `/venue-heatmap` | `create_team_venue_heatmap()` | JSON with base64 image |

---

This system is designed to be:
- ✅ **Fast** - pre-computed data
- ✅ **Responsive** - no page reloads
- ✅ **Visual** - charts and heatmaps
- ✅ **Flexible** - compare globally or by venue
- ✅ **User-friendly** - simple dropdowns and buttons
