"""
IPL Toss Predictor and Analysis
This script performs comprehensive analysis on IPL match data including:
1. Team name consolidation and historical data merging
2. Data cleaning (removing draws and unplayed matches)
3. Visualization of toss win vs match win percentages
4. Batting first vs fielding first win analysis
5. Venue-based win percentage heatmaps
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# ============= STEP 1: TEAM MAPPING AND CONSOLIDATION =============

# Map team IDs to their names and handle name changes/bans
TEAM_MAPPING = {
    1: 'Royal Challengers Bangalore',
    2: 'Mumbai Indians',
    3: 'Kolkata Knight Riders',
    4: 'Delhi Capitals',
    5: 'Rajasthan Royals',
    6: 'Punjab Kings',
    129: 'Sunrisers Hyderabad',  # formerly Deccan Chargers
    134: 'Chennai Super Kings',
    252: 'Rajasthan Royals',  # duplicate mapping
    494: 'Sunrisers Hyderabad',  # consolidated
    614: 'Gujarat Titans',
    615: 'Lucknow Super Giants',
    1414: 'Kochi Tuskers Kerala',  # disbanded 2011
    1419: 'Pune Warriors India'     # disbanded 2013
}

# Teams that were added recently (post 2021) - independent status
NEW_TEAMS_THRESHOLD = 2022
NEWLY_ADDED_TEAMS = {614, 615}  # Gujarat Titans, Lucknow Super Giants

# Teams to consolidate (merging old to new)
CONSOLIDATION_MAP = {
    252: 5,  # Map to Rajasthan Royals
    494: 129,  # Map to Sunrisers Hyderabad
    1414: 1414,  # Keep as is (disbanded)
    1419: 1419   # Keep as is (disbanded)
}

print("=" * 80)
print("STEP 1: LOADING AND CLEANING DATA")
print("=" * 80)

# Load data
df = pd.read_csv('ipl_matches_data.csv')
print(f"\nInitial records: {len(df)}")
print(f"Date range: {df['match_date'].min()} to {df['match_date'].max()}")

# STEP 1.1: Remove unplayed matches and draws
print(f"\nMatches before filtering out draws: {len(df)}")
df = df[df['result'] == 'win'].copy()
print(f"Matches after removing draws/unplayed: {len(df)}")
df = df.dropna(subset=['match_winner'])
print(f"Matches with valid winner: {len(df)}")

# STEP 1.2: Add team names
df['team1_name'] = df['team1'].map(TEAM_MAPPING)
df['team2_name'] = df['team2'].map(TEAM_MAPPING)
df['match_winner_name'] = df['match_winner'].map(TEAM_MAPPING)
df['toss_winner_name'] = df['toss_winner'].map(TEAM_MAPPING)

# STEP 1.3: Consolidate teams (merge banned teams with replacements)
print("\n--- Team Consolidation ---")
for old_team_id, new_team_id in CONSOLIDATION_MAP.items():
    if old_team_id != new_team_id:  # Skip self-mapping
        old_name = TEAM_MAPPING.get(old_team_id, f"Team {old_team_id}")
        new_name = TEAM_MAPPING.get(new_team_id, f"Team {new_team_id}")
        if old_team_id not in [1414, 1419]:  # Don't consolidate disbanded teams
            print(f"  Consolidating {old_name} (ID: {old_team_id}) → {new_name} (ID: {new_team_id})")
            df.loc[df['team1'] == old_team_id, 'team1'] = new_team_id
            df.loc[df['team2'] == old_team_id, 'team2'] = new_team_id
            df.loc[df['match_winner'] == old_team_id, 'match_winner'] = new_team_id
            df.loc[df['toss_winner'] == old_team_id, 'toss_winner'] = new_team_id

# Rebuild team names after consolidation
df['team1_name'] = df['team1'].map(TEAM_MAPPING)
df['team2_name'] = df['team2'].map(TEAM_MAPPING)
df['match_winner_name'] = df['match_winner'].map(TEAM_MAPPING)
df['toss_winner_name'] = df['toss_winner'].map(TEAM_MAPPING)

# STEP 1.4: Identify and flag newly added teams
df['season_int'] = df['season'].astype(str).str.split('/').str[0].astype(int)
df['is_new_team_flag'] = False

for team_id in NEWLY_ADDED_TEAMS:
    # Mark first appearance of new teams
    first_season = df[df['team1'] == team_id]['season_int'].min()
    if pd.isna(first_season):
        first_season = df[df['team2'] == team_id]['season_int'].min()
    
    if first_season >= NEW_TEAMS_THRESHOLD:
        print(f"  New team identified: {TEAM_MAPPING[team_id]} (First appeared in {int(first_season)})")

# Final unique teams after consolidation
active_teams = sorted([
    t for t in set(df['team1'].unique()) | set(df['team2'].unique())
    if t not in [1414, 1419]  # Exclude disbanded teams
])

print(f"\nActive teams for analysis: {len(active_teams)}")
for team_id in active_teams:
    team_name = TEAM_MAPPING.get(team_id, f"Team {team_id}")
    team_matches = len(df[(df['team1'] == team_id) | (df['team2'] == team_id)])
    print(f"  - {team_name}: {team_matches} matches")

# Remove disbanded teams from analysis
df = df[~df['team1'].isin([1414, 1419]) & ~df['team2'].isin([1414, 1419])].copy()
print(f"\nFinal records for analysis: {len(df)}")

print("\n" + "=" * 80)
print("STEP 2: TOSS WIN vs MATCH WIN ANALYSIS")
print("=" * 80)

# Create toss and match win statistics
toss_match_stats = {}

for team_id in active_teams:
    team_name = TEAM_MAPPING[team_id]
    
    # Get all matches where this team participated
    team_matches = df[(df['team1'] == team_id) | (df['team2'] == team_id)].copy()
    
    # Mark if team won toss
    team_matches['team_won_toss'] = team_matches['toss_winner'] == team_id
    
    # Mark if team won match
    team_matches['team_won_match'] = team_matches['match_winner'] == team_id
    
    # Calculate statistics
    total_matches = len(team_matches)
    toss_wins = (team_matches['team_won_toss']).sum()
    match_wins = (team_matches['team_won_match']).sum()
    match_wins_after_toss_win = (team_matches['team_won_toss'] & team_matches['team_won_match']).sum()
    
    if toss_wins > 0:
        win_pct_after_toss_win = (match_wins_after_toss_win / toss_wins) * 100
    else:
        win_pct_after_toss_win = 0
    
    overall_win_pct = (match_wins / total_matches) * 100 if total_matches > 0 else 0
    
    toss_match_stats[team_name] = {
        'total_matches': total_matches,
        'toss_wins': toss_wins,
        'match_wins': match_wins,
        'match_wins_after_toss_win': match_wins_after_toss_win,
        'toss_win_pct': (toss_wins / total_matches * 100) if total_matches > 0 else 0,
        'match_win_pct': overall_win_pct,
        'win_pct_after_toss_win': win_pct_after_toss_win
    }
    
    print(f"\n{team_name}:")
    print(f"  Total Matches: {total_matches}")
    print(f"  Toss Wins: {toss_wins} ({toss_match_stats[team_name]['toss_win_pct']:.1f}%)")
    print(f"  Match Wins: {match_wins} ({overall_win_pct:.1f}%)")
    print(f"  Match Wins after Toss Win: {match_wins_after_toss_win}/{toss_wins} ({win_pct_after_toss_win:.1f}%)")
    print(f"  Luck Factor: {win_pct_after_toss_win - overall_win_pct:+.1f}% diff")

print("\n" + "=" * 80)
print("STEP 3: BATTING FIRST vs FIELDING FIRST ANALYSIS")
print("=" * 80)

bat_field_stats = {}

for team_id in active_teams:
    team_name = TEAM_MAPPING[team_id]
    
    # Get all matches where this team participated
    team_matches = df[(df['team1'] == team_id) | (df['team2'] == team_id)].copy()
    
    # Check if team batted first (decided to bat after winning toss or toss winner chose to bat)
    # toss_decision: 'bat' or 'field'
    team_matches['team_batted_first'] = False
    
    # If team won toss and decided to bat
    team_batted_after_win = team_matches[(team_matches['toss_winner'] == team_id) & 
                                         (team_matches['toss_decision'] == 'bat')]
    
    # If team lost toss but opponent fielded (meaning team batted)
    team_batted_after_loss = team_matches[(team_matches['toss_winner'] != team_id) & 
                                          (team_matches['toss_decision'] == 'field')]
    
    team_batted_matches = pd.concat([team_batted_after_win, team_batted_after_loss])
    team_fielded_matches = team_matches[~team_matches.index.isin(team_batted_matches.index)]
    
    # Calculate wins
    bat_first_wins = (team_batted_matches['match_winner'] == team_id).sum()
    field_first_wins = (team_fielded_matches['match_winner'] == team_id).sum()
    
    bat_first_total = len(team_batted_matches)
    field_first_total = len(team_fielded_matches)
    
    bat_field_stats[team_name] = {
        'bat_first_matches': bat_first_total,
        'bat_first_wins': bat_first_wins,
        'bat_first_win_pct': (bat_first_wins / bat_first_total * 100) if bat_first_total > 0 else 0,
        'field_first_matches': field_first_total,
        'field_first_wins': field_first_wins,
        'field_first_win_pct': (field_first_wins / field_first_total * 100) if field_first_total > 0 else 0
    }
    
    print(f"\n{team_name}:")
    print(f"  Bat First: {bat_first_wins}/{bat_first_total} ({bat_field_stats[team_name]['bat_first_win_pct']:.1f}%)")
    print(f"  Field First: {field_first_wins}/{field_first_total} ({bat_field_stats[team_name]['field_first_win_pct']:.1f}%)")
    print(f"  Preference: {'Batting' if bat_field_stats[team_name]['bat_first_win_pct'] > bat_field_stats[team_name]['field_first_win_pct'] else 'Fielding'}")

print("\n" + "=" * 80)
print("STEP 4: VENUE-BASED ANALYSIS")
print("=" * 80)

# Analyze wins by venue for each team
venue_stats = {}

for team_id in active_teams:
    team_name = TEAM_MAPPING[team_id]
    
    team_matches = df[(df['team1'] == team_id) | (df['team2'] == team_id)].copy()
    
    # Group by venue
    venue_performance = team_matches.groupby('venue').apply(
        lambda x: pd.Series({
            'matches': len(x),
            'wins': (x['match_winner'] == team_id).sum()
        })
    ).reset_index()
    
    venue_performance['win_pct'] = (venue_performance['wins'] / venue_performance['matches'] * 100)
    venue_performance = venue_performance[venue_performance['matches'] >= 2]  # Only venues with 2+ matches
    
    venue_stats[team_name] = venue_performance
    
    print(f"\n{team_name} - Top venues:")
    if len(venue_performance) > 0:
        top_venues = venue_performance.nlargest(3, 'win_pct')
        for idx, row in top_venues.iterrows():
            print(f"  {row['venue']}: {row['wins']}/{row['matches']} ({row['win_pct']:.1f}%)")
    else:
        print("  Not enough venue data")

# Save data for visualization
print("\n" + "=" * 80)
print("GENERATING VISUALIZATIONS...")
print("=" * 80)

# ============= VISUALIZATION 1: TOSS WIN vs MATCH WIN (ALL TEAMS) =============
fig1, axes1 = plt.subplots(4, 3, figsize=(20, 16))
fig1.suptitle('Team Toss Win % vs Match Win %\n(Red: Toss Win % | Teal: Match Win %)', 
              fontsize=18, fontweight='bold', y=0.995)

axes1 = axes1.flatten()
sorted_teams = sorted(toss_match_stats.keys())

for idx, team_name in enumerate(sorted_teams):
    ax = axes1[idx]
    stats = toss_match_stats[team_name]
    
    x_pos = [0, 1]
    values = [stats['toss_win_pct'], stats['match_win_pct']]
    colors = ['#FF6B6B', '#4ECDC4']
    
    bars = ax.bar(x_pos, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add percentage labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Add data labels with better positioning
    ax.text(0.5, -0.22, f'Toss: {stats["toss_wins"]}/{stats["total_matches"]}  |  Match: {stats["match_wins"]}/{stats["total_matches"]}',
            ha='center', transform=ax.transAxes, fontsize=9, style='italic', weight='bold')
    
    ax.set_ylabel('Percentage (%)', fontsize=10, fontweight='bold')
    ax.set_title(team_name, fontsize=11, fontweight='bold', pad=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Toss Win %', 'Match Win %'], fontsize=9, fontweight='bold')
    ax.set_ylim([0, 110])
    ax.grid(axis='y', alpha=0.4, linestyle='--', linewidth=0.8)
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.6, linewidth=1)

# Hide extra subplots
for idx in range(len(sorted_teams), len(axes1)):
    axes1[idx].axis('off')

plt.tight_layout(rect=[0, 0.02, 1, 0.99])
plt.subplots_adjust(left=0.08, right=0.95, top=0.93, bottom=0.08, hspace=0.35, wspace=0.3)
plt.savefig('01_toss_vs_match_win.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 01_toss_vs_match_win.png")
plt.close(fig1)  # Close the figure instead of showing

# ============= VISUALIZATION 2: BATTING FIRST vs FIELDING FIRST (ALL TEAMS) =============
fig2, axes2 = plt.subplots(4, 3, figsize=(20, 16))
fig2.suptitle('Team Win % - Batting First vs Fielding First\n(Blue: Bat First | Orange: Field First)', 
              fontsize=18, fontweight='bold', y=0.995)

axes2 = axes2.flatten()

for idx, team_name in enumerate(sorted_teams):
    ax = axes2[idx]
    stats = bat_field_stats[team_name]
    
    x_pos = [0, 1]
    values = [stats['bat_first_win_pct'], stats['field_first_win_pct']]
    colors = ['#3498DB', '#E67E22']
    
    bars = ax.bar(x_pos, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add percentage labels
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Add data labels with better positioning
    ax.text(0.5, -0.22, f'Bat: {stats["bat_first_wins"]}/{stats["bat_first_matches"]}  |  Field: {stats["field_first_wins"]}/{stats["field_first_matches"]}',
            ha='center', transform=ax.transAxes, fontsize=9, style='italic', weight='bold')
    
    ax.set_ylabel('Win Percentage (%)', fontsize=10, fontweight='bold')
    ax.set_title(team_name, fontsize=11, fontweight='bold', pad=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['Bat First', 'Field First'], fontsize=9, fontweight='bold')
    ax.set_ylim([0, 110])
    ax.grid(axis='y', alpha=0.4, linestyle='--', linewidth=0.8)
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.6, linewidth=1)

# Hide extra subplots
for idx in range(len(sorted_teams), len(axes2)):
    axes2[idx].axis('off')

plt.tight_layout(rect=[0, 0.02, 1, 0.99])
plt.subplots_adjust(left=0.08, right=0.95, top=0.93, bottom=0.08, hspace=0.35, wspace=0.3)
plt.savefig('02_bat_first_vs_field_first.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 02_bat_first_vs_field_first.png")
plt.close(fig2)  # Close the figure instead of showing

# ============= VISUALIZATION 3: VENUE HEATMAPS (ONE PER TEAM) =============
print("\nGenerating venue heatmaps for each team...")

for team_name in sorted_teams:
    venue_data = venue_stats[team_name]
    
    if len(venue_data) > 0:
        # Create heatmap with better sizing
        fig_height = max(8, len(venue_data) * 0.6)
        fig, ax = plt.subplots(figsize=(16, fig_height))
        
        # Sort by win percentage
        venue_data_sorted = venue_data.sort_values('win_pct', ascending=True)
        
        # Create color map
        colors_hm = plt.cm.RdYlGn(venue_data_sorted['win_pct'] / 100)
        
        bars = ax.barh(range(len(venue_data_sorted)), venue_data_sorted['win_pct'], 
                      color=colors_hm, edgecolor='black', linewidth=1.2, height=0.7)
        
        # Add labels with better positioning
        for idx, (bar, row) in enumerate(zip(bars, venue_data_sorted.itertuples())):
            width = bar.get_width()
            label_text = f"{row.wins}/{row.matches} matches ({row.win_pct:.1f}%)"
            ax.text(width + 2, idx, label_text, va='center', fontsize=10, fontweight='bold')
        
        ax.set_yticks(range(len(venue_data_sorted)))
        ax.set_yticklabels(venue_data_sorted['venue'], fontsize=10, fontweight='bold')
        ax.set_xlabel('Win Percentage (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{team_name}\nVenue-Based Win Percentage (Red: Low % → Green: High %)', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlim([0, 120])
        ax.grid(axis='x', alpha=0.4, linestyle='--', linewidth=0.8)
        
        # Improve layout
        plt.tight_layout(rect=[0, 0, 0.98, 0.96])
        plt.subplots_adjust(left=0.25, right=0.95, top=0.94, bottom=0.08)
        
        filename = f'03_venue_heatmap_{team_name.replace(" ", "_")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {filename}")
        plt.close()  # Close the figure instead of showing

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE!")
print("=" * 80)
print("\nGenerated Files:")
print("  1. 01_toss_vs_match_win.png - Toss Win vs Match Win for all teams")
print("  2. 02_bat_first_vs_field_first.png - Batting First vs Fielding First analysis")
print(f"  3. 03_venue_heatmap_*.png - Individual venue heatmaps for {len(sorted_teams)} teams")

print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)

# Find interesting statistics
print("\nBest Toss-to-Match Converters (Luck):")
luck_sorted = sorted(toss_match_stats.items(), 
                    key=lambda x: x[1]['win_pct_after_toss_win'] - x[1]['match_win_pct'], 
                    reverse=True)
for team_name, stats in luck_sorted[:5]:
    luck = stats['win_pct_after_toss_win'] - stats['match_win_pct']
    print(f"  {team_name}: +{luck:.1f}% {'(High luck)' if luck > 10 else ''}")

print("\nBest Batting First Teams:")
bat_sorted = sorted(bat_field_stats.items(), key=lambda x: x[1]['bat_first_win_pct'], reverse=True)
for team_name, stats in bat_sorted[:5]:
    print(f"  {team_name}: {stats['bat_first_win_pct']:.1f}%")

print("\nBest Fielding First Teams:")
field_sorted = sorted(bat_field_stats.items(), key=lambda x: x[1]['field_first_win_pct'], reverse=True)
for team_name, stats in field_sorted[:5]:
    print(f"  {team_name}: {stats['field_first_win_pct']:.1f}%")
