from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Add backend folder to Python path so we can import applogic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Initialize Flask. 
# We set 'template_folder' to '../templates' because the folder is outside 
# the 'flask' directory and located at the project root.
app = Flask(__name__, template_folder='../templates')

# Import analysis functions from backend
# These are ALL the pre-computed statistics generated when applogic.py runs
from applogic import (
    df,  # Main dataframe with all match data
    toss_match_stats,  # Dictionary: team_name -> toss/match statistics
    bat_field_stats,  # Dictionary: team_name -> batting/fielding statistics  
    venue_stats,  # Dictionary: team_name -> DataFrame with venue performance
    TEAM_MAPPING,  # Dictionary: team_id -> team_name
    active_teams  # List of active team IDs
)

# ============================================================================
# HELPER FUNCTIONS - These convert raw stats into specific analyses
# ============================================================================

def get_team_list():
    """
    WHAT IT DOES: Returns list of all active team names
    WHY: Frontend needs this to populate dropdown selectors
    """
    return sorted([TEAM_MAPPING[team_id] for team_id in active_teams])


def analyze_toss_comparison(team1, team2, venue=None):
    """
    WHAT IT DOES: Compares TOSS WINNING RATIO between two teams
    HOW:
        1. Get all matches where both teams played each other
        2. Filter by venue if provided  
        3. Count how many tosses each team won
        4. Calculate winning percentage
    
    RETURNS: Dictionary with comparison data
    """
    # Filter matches where these two teams played against each other
    matches = df[
        ((df['team1_name'] == team1) & (df['team2_name'] == team2)) |
        ((df['team1_name'] == team2) & (df['team2_name'] == team1))
    ].copy()
    
    # Further filter by venue if user selected one
    if venue:
        matches = matches[matches['venue'] == venue]
    
    if len(matches) == 0:
        return {
            'error': f'No matches found between {team1} and {team2}',
            'team1': team1,
            'team2': team2,
            'venue': venue,
            'matches': 0
        }
    
    # Count toss wins for each team
    team1_toss_wins = (matches['toss_winner_name'] == team1).sum()
    team2_toss_wins = (matches['toss_winner_name'] == team2).sum()
    total_matches = len(matches)
    
    # Calculate percentages
    team1_toss_pct = (team1_toss_wins / total_matches * 100) if total_matches > 0 else 0
    team2_toss_pct = (team2_toss_wins / total_matches * 100) if total_matches > 0 else 0
    
    # Determine winner
    if team1_toss_pct > team2_toss_pct:
        result = f"{team1} has HIGHER toss winning ratio"
    elif team2_toss_pct > team1_toss_pct:
        result = f"{team2} has HIGHER toss winning ratio"
    else:
        result = "EQUAL toss winning ratio"
    
    return {
        'team1': team1,
        'team2': team2,
        'venue': venue if venue else 'All Venues',
        'matches': total_matches,
        'team1_toss_wins': int(team1_toss_wins),
        'team2_toss_wins': int(team2_toss_wins),
        'team1_toss_pct': round(team1_toss_pct, 2),
        'team2_toss_pct': round(team2_toss_pct, 2),
        'result': result
    }


def analyze_match_comparison(team1, team2, venue=None):
    """
    WHAT IT DOES: Compares MATCH WINNING RATIO between two teams
    HOW:
        1. Get all matches where both teams played each other
        2. Filter by venue if provided
        3. Count how many matches each team won
        4. Calculate winning percentage
        
    RETURNS: Dictionary with match win comparison data
    """
    # Filter matches where these two teams played against each other
    matches = df[
        ((df['team1_name'] == team1) & (df['team2_name'] == team2)) |
        ((df['team1_name'] == team2) & (df['team2_name'] == team1))
    ].copy()
    
    # Further filter by venue if user selected one
    if venue:
        matches = matches[matches['venue'] == venue]
    
    if len(matches) == 0:
        return {
            'error': f'No matches found between {team1} and {team2}',
            'team1': team1,
            'team2': team2,
            'venue': venue,
            'matches': 0
        }
    
    # Count match wins for each team
    team1_match_wins = (matches['match_winner_name'] == team1).sum()
    team2_match_wins = (matches['match_winner_name'] == team2).sum()
    total_matches = len(matches)
    
    # Calculate percentages
    team1_match_pct = (team1_match_wins / total_matches * 100) if total_matches > 0 else 0
    team2_match_pct = (team2_match_wins / total_matches * 100) if total_matches > 0 else 0
    
    # Determine winner
    if team1_match_pct > team2_match_pct:
        result = f"{team1} has HIGHER match winning ratio"
    elif team2_match_pct > team1_match_pct:
        result = f"{team2} has HIGHER match winning ratio"
    else:
        result = "EQUAL match winning ratio"
    
    return {
        'team1': team1,
        'team2': team2,
        'venue': venue if venue else 'All Venues',
        'matches': total_matches,
        'team1_match_wins': int(team1_match_wins),
        'team2_match_wins': int(team2_match_wins),
        'team1_match_pct': round(team1_match_pct, 2),
        'team2_match_pct': round(team2_match_pct, 2),
        'result': result
    }


def create_comparison_visualization(team1, team2, venue=None):
    """
    WHAT IT DOES: Creates a visual graph comparing two teams
    HOW:
        1. Call both toss and match comparison functions
        2. Create a matplotlib figure with side-by-side bar charts
        3. Convert the image to base64 so it can be sent to frontend as JSON
        
    RETURNS: Base64 encoded image string
    """
    toss_data = analyze_toss_comparison(team1, team2, venue)
    match_data = analyze_match_comparison(team1, team2, venue)
    
    if 'error' in toss_data:
        return None
    
    # Create figure with 2 subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # TOSS COMPARISON CHART
    teams = [team1, team2]
    toss_wins = [toss_data['team1_toss_wins'], toss_data['team2_toss_wins']]
    colors = ['#FF6B6B', '#4ECDC4']
    
    bars1 = ax1.bar(teams, toss_wins, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Toss Wins', fontsize=12, fontweight='bold')
    ax1.set_title(f'Toss Wins Comparison\n{toss_data["venue"]}', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add percentage labels
    for bar, pct in zip(bars1, [toss_data['team1_toss_pct'], toss_data['team2_toss_pct']]):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # MATCH COMPARISON CHART
    match_wins = [match_data['team1_match_wins'], match_data['team2_match_wins']]
    
    bars2 = ax2.bar(teams, match_wins, color=['#3498DB', '#E67E22'], alpha=0.7, edgecolor='black', linewidth=2)
    ax2.set_ylabel('Match Wins', fontsize=12, fontweight='bold')
    ax2.set_title(f'Match Wins Comparison\n{match_data["venue"]}', fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add percentage labels
    for bar, pct in zip(bars2, [match_data['team1_match_pct'], match_data['team2_match_pct']]):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    # Convert to base64
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_base64


def get_single_team_stats(team):
    """
    WHAT IT DOES: Returns comprehensive statistics for a single team
    HOW:
        1. Fetch pre-computed stats from global dictionaries
        2. Format them nicely for display
        
    RETURNS: Dictionary with team statistics
    """
    if team not in toss_match_stats:
        return {'error': f'Team {team} not found'}
    
    toss_stats = toss_match_stats[team]
    bat_field = bat_field_stats[team]
    
    return {
        'team': team,
        'total_matches': toss_stats['total_matches'],
        'toss_wins': int(toss_stats['toss_wins']),
        'toss_win_pct': round(toss_stats['toss_win_pct'], 2),
        'match_wins': int(toss_stats['match_wins']),
        'match_win_pct': round(toss_stats['match_win_pct'], 2),
        'match_wins_after_toss_win': int(toss_stats['match_wins_after_toss_win']),
        'win_pct_after_toss_win': round(toss_stats['win_pct_after_toss_win'], 2),
        'bat_first_win_pct': round(bat_field['bat_first_win_pct'], 2),
        'field_first_win_pct': round(bat_field['field_first_win_pct'], 2),
        'bat_first_wins': int(bat_field['bat_first_wins']),
        'field_first_wins': int(bat_field['field_first_wins'])
    }


def create_team_venue_heatmap(team):
    """
    WHAT IT DOES: Creates a horizontal bar chart showing team performance at all venues
    HOW:
        1. Get venue_stats[team] which has all venues with their win percentages
        2. Create a horizontal bar chart sorted by win percentage
        3. Color code: Red (low %) to Green (high %)
        4. Convert to base64 image
        
    RETURNS: Base64 encoded image string
    """
    if team not in venue_stats:
        return None
    
    venue_data = venue_stats[team]
    
    if len(venue_data) == 0:
        return None
    
    # Sort by win percentage
    venue_data_sorted = venue_data.sort_values('win_pct', ascending=True)
    
    # Create figure
    fig_height = max(8, len(venue_data_sorted) * 0.5)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    
    # Create colormap (Red -> Green)
    colors = plt.cm.RdYlGn(venue_data_sorted['win_pct'] / 100)
    
    # Create horizontal bars
    bars = ax.barh(range(len(venue_data_sorted)), venue_data_sorted['win_pct'], 
                   color=colors, edgecolor='black', linewidth=1.2, height=0.7)
    
    # Add labels
    for idx, (bar, row) in enumerate(zip(bars, venue_data_sorted.itertuples())):
        width = bar.get_width()
        label_text = f"{row.wins}/{row.matches} ({row.win_pct:.1f}%)"
        ax.text(width + 2, idx, label_text, va='center', fontsize=10, fontweight='bold')
    
    # Set labels and title
    ax.set_yticks(range(len(venue_data_sorted)))
    ax.set_yticklabels(venue_data_sorted['venue'], fontsize=9)
    ax.set_xlabel('Win Percentage (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'{team} - Venue-Based Win Percentage\n(Red: Low % → Green: High %)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim([0, 120])
    ax.grid(axis='x', alpha=0.4, linestyle='--')
    
    plt.tight_layout()
    
    # Convert to base64
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_base64


# ============================================================================
# FLASK ROUTES - These receive requests from frontend and return responses
# ============================================================================

# HOME PAGE ROUTE
# When user visits http://localhost:5000/, Flask renders frontend.html
@app.route('/')
def index():
    """
    WHAT IT DOES: Displays the main HTML page
    WHY: This is the entry point when user opens the application
    """
    return render_template('frontend.html')


# OUTCOME ANALYSIS ROUTE
# This receives POST request from "Analyse Winning Probability" button
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    WHAT IT DOES: 
        1. Receives form data from frontend (team1, team2, optional venue)
        2. Calls comparison functions to analyze data
        3. Creates visualization
        4. Returns JSON response with data and graph
        
    FLOW:
        Frontend form → /analyze route → Analysis functions → Visualization → JSON response → Frontend displays
    """
    try:
        # GET DATA FROM FRONTEND FORM
        team1 = request.form.get('team1', '').strip()
        team2 = request.form.get('team2', '').strip()
        venue = request.form.get('venue', '').strip()
        
        # If venue is empty string, treat as None (no venue filter)
        if not venue:
            venue = None
        
        # VALIDATE INPUT
        if not team1 or not team2:
            return jsonify({'error': 'Please select both teams'}), 400
        
        if team1 == team2:
            return jsonify({'error': 'Please select different teams'}), 400
        
        # PERFORM ANALYSIS
        toss_result = analyze_toss_comparison(team1, team2, venue)
        match_result = analyze_match_comparison(team1, team2, venue)
        
        if 'error' in toss_result:
            return jsonify({'error': toss_result['error']}), 404
        
        # CREATE VISUALIZATION
        graph_img = create_comparison_visualization(team1, team2, venue)
        
        # RETURN RESPONSE AS JSON
        return jsonify({
            'success': True,
            'toss_analysis': toss_result,
            'match_analysis': match_result,
            'graph': f'data:image/png;base64,{graph_img}' if graph_img else None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# QUICK STATS ROUTE  
# This receives POST request from "View Historical Stats" button
@app.route('/stats', methods=['POST'])
def get_stats():
    """
    WHAT IT DOES:
        1. Receives selected team from frontend
        2. Fetches pre-computed statistics for that team
        3. Returns JSON with stats
        
    FLOW:
        Frontend form → /stats route → get_single_team_stats() → JSON response → Frontend displays
    """
    try:
        team = request.form.get('team', '').strip()
        
        if not team:
            return jsonify({'error': 'Please select a team'}), 400
        
        # FETCH STATS
        stats = get_single_team_stats(team)
        
        if 'error' in stats:
            return jsonify(stats), 404
        
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# VENUE HEATMAP ROUTE
# This receives POST request from heatmap visualization button
@app.route('/venue-heatmap', methods=['POST'])
def venue_heatmap():
    """
    WHAT IT DOES:
        1. Receives selected team from frontend
        2. Creates venue-based performance heatmap
        3. Returns image as base64
        
    FLOW:
        Frontend button → /venue-heatmap route → create_team_venue_heatmap() → Image as JSON → Frontend displays
    """
    try:
        team = request.form.get('team', '').strip()
        
        if not team:
            return jsonify({'error': 'Please select a team'}), 400
        
        # CREATE HEATMAP
        heatmap_img = create_team_venue_heatmap(team)
        
        if heatmap_img is None:
            return jsonify({'error': f'No venue data available for {team}'}), 404
        
        return jsonify({
            'success': True,
            'team': team,
            'image': f'data:image/png;base64,{heatmap_img}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# API ROUTE FOR TEAM LIST
# This is used by frontend to populate dropdown menus
@app.route('/api/teams', methods=['GET'])
def api_teams():
    """
    WHAT IT DOES:
        1. Returns list of all active teams as JSON
        2. Frontend uses this to populate dropdown selectors
    """
    return jsonify({'teams': get_team_list()})


if __name__ == '__main__':
    # Start the development server on all network interfaces at port 5000.
    # 'debug=True' allows the server to automatically reload when code changes.
    app.run(host='0.0.0.0', port=5000, debug=True) 
    