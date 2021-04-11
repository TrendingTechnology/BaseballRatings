'''
Script for parsing Retrosheet game log files, transforming them into useable tables and saving to a SQLite database. 
'''

import pandas as pd 
import sqlite3
import os.path

from Formats import (
    gl_format,
    gl_informats,
    games_format
)

class Parser():
    def __init__(self, new=False, db='gamedb.db'):
        # Setup SQL db connection
        self.db = db
        
        # Setup data (if first time)
        if new:
            self.exec('DROP TABLE IF EXISTS games')
            self.exec('CREATE TABLE games (season, date, gnum, teamid, opponent, gid, host, outs, winner, runs_scored, runs_allowed, line, line_opp)')

    def exec(self, *query):
        ''' Create connection to database and execute specified query '''
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            result = c.execute(*query)
            conn.commit()
            return result

    def parse_file(self, path, season):
        # Read file
        df = pd.read_csv(path, header=None, names=gl_format, dtype=gl_informats)
        df.fillna('', inplace=True)

        # Iterate through file by line
        for _, row in df.iterrows():
            
            # Determine winner
            winner = ''
            if row.forfeit != '':
                winner = row.forfeit
            elif row.score_vis > row.score_home:
                winner = 'V'
            elif row.score_home > row.score_vis:
                winner = 'H'
            else:
                winner = 'T'
            
            # Parse visiting team
            teamid = row.teamid_vis
            insert = (
                season,                         #season
                row.date,                       #date
                row.gnum_vis,                   #game number (for multiheaders)
                row.teamid_vis,                 #teamid
                row.teamid_home,                #opponent
                teamid + row.date + row.gnum_vis,   #gid
                'V',                            #host
                row.outs,                       #outs
                {'V': 'W', 'H': 'L', 'T': 'T'}[winner], #winner
                row.score_vis,                  #runs_scored
                row.score_home,                 #runs_allowed
                row.line_vis,                   #line
                row.line_home                   #line_opp
            )
            self.exec('INSERT INTO games VALUES(' + ','.join(['?'] * len(games_format)) + ')', insert)

            # Parse home team
            teamid = row.teamid_home
            insert = (
                season,                         #season
                row.date,                       #date
                row.gnum_home,                  #game number (for multiheaders)
                row.teamid_home,                #teamid
                row.teamid_vis,                 #opponent
                teamid + row.date + row.gnum_home,  #gid
                'H',                            #host
                row.outs,                       #outs
                {'H': 'W', 'V': 'L', 'T': 'T'}[winner], #winner
                row.score_home,                 #runs_scored
                row.score_vis,                  #runs_allowed
                row.line_home,                  #line
                row.line_vis                    #line_opp
            )
            self.exec('INSERT INTO games VALUES(' + ','.join(['?'] * len(games_format)) + ')', insert)

if __name__ == '__main__':
    p = Parser(new=True)
    infolder = r'gl2010_19'
    for yr in range(2010, 2020):
        file = os.join(infolder, 'GL' + yr + '.txt')
        p.parse_file(path, year)

