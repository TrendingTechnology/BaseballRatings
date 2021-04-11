'''
Calculate Elo ratings for a set of games data. 
'''
import numpy as np
import pandas as pd 
import sqlite3
import os.path

def calculate_elos(games, K, R):
    '''
    games:  Pandas dataframe game-level data created by Parser module. Data should be filtered to
                desired timeframe for analysis.
    K:      Parameter for maximum rating change from win/loss
    R:      Parameter specifying expected margin of victory in an uneven match
    Returns: Pandas dataframe with team and date level ratings output
    '''

    # Set up processing
    teams = list(games.teamid_vis.unique())
    teams.sort()

    date = 'start'
    elos_now = {t: 1200 for t in teams}
    w_now = {t: 0 for t in teams}
    l_now = {t: 0 for t in teams}

    elos = pd.DataFrame(elos_now, index=[date]) 
    ws = pd.DataFrame(w_now, index=[date])
    ls = pd.DataFrame(l_now, index=[date])

    # Iterate through games and calculate rating updates for each encounter
    for i, game in games.iterrows():
        v = game.teamid_vis
        h = game.teamid_home
        winner = game.winner
        date = game.date

        # Elo rating
        R_v = elos_now[v]
        R_h = elos_now[h]

        # Expected score
        E_v = 1 / (1 + 10**((R_h - R_v)/R))
        E_h = 1 - E_v

        # Actual score
        S_v = 1 if winner == 'V' else 0 if winner == 'H' else 0.5
        S_h = 1 - S_v

        # Updated rating
        R_v_new = R_v + K * (S_v - E_v)
        R_h_new = R_h + K * (S_h - E_h)

        elos_now[v] = R_v_new
        elos_now[h] = R_h_new

        elos = elos.append(pd.DataFrame(elos_now, index=[date]))

        # Updated W-L record
        w_now[v] = w_now[v] + (1 if winner == 'V' else 0)
        w_now[h] = w_now[h] + (1 if winner == 'H' else 0)
        l_now[v] = l_now[v] + (0 if winner == 'V' else 1)
        l_now[h] = l_now[h] + (0 if winner == 'H' else 1)

        ws = ws.append(pd.DataFrame(w_now, index=[date]))
        ls = ls.append(pd.DataFrame(l_now, index=[date]))

    elos_long = pd.DataFrame(elos.unstack(), columns=['rating'])
    elos_long.index.names = ['teamid', 'date']
    return elos_long
    
if __name__ == '__main__':
    # Pull data from database
    db = 'gamedb.db'
    conn = sqlite3.connect(db)
    games = pd.read_sql('SELECT * FROM games', con=conn)
    games.sort_values(['date', 'gnum'], inplace=True)

    # Process games data with default parameters
    K = 12
    R = 400
    output = calculate_elos(games, K , R)

    # Save output to database
    output.to_sql('elos', conn, if_exists='replace')
    conn.close()
