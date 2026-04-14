import pandas as pd

df = pd.read_csv('ipl_matches_data.csv')
print('Seasons available:')
print(sorted(df['season'].unique()))

print('\nTeams by season:')
for season in sorted(df['season'].unique()):
    teams = set(df[df['season']==season]['team1'].unique()) | set(df[df['season']==season]['team2'].unique())
    print(f'Season {season}: Teams {sorted(teams)}')

print('\nAll unique teams:', sorted(set(df['team1'].unique()) | set(df['team2'].unique())))
