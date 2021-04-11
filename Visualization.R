## Packages

setwd('D:\\Lukas\\Projects\\Retrosheet')

library(tidyverse)
library(DBI)
library(ggplot2)
library(ggridges)
library(lubridate)

## Read ratings data from SQLite database
con <- dbConnect(RSQLite::SQLite(), "gamedb.db")
elos <- as_tibble(dbReadTable(con, "elos"))
dbDisconnect(con)

## Clean / prep data for use

# Import team info to attach 
teams.info <- read.csv('teamids.csv', header=FALSE, col.names = c('teamid', 'city', 'name', 'league', 'region')) %>%
  mutate(division = str_c(league, region, sep=' '))

# Attach team info and format dates
elos <- elos %>% 
  left_join(select(teams.info, teamid, division, name), by = 'teamid') %>%
  filter(date != 'start') %>%
  mutate(date = ymd(date)) %>%
  arrange(division, teamid, date) 


## Plot ratings for a selected division / time period

seasons <- 2014:2019
teams = c('SEA', 'HOU', 'ANA', 'OAK', 'TEX')
elos.sub <- elos %>% 
  mutate(season = year(date)) %>%
  filter(teamid %in% teams, season %in% seasons)

g1 <- ggplot(elos.sub, aes(x=date, y=rating)) + 
  geom_line(aes(color=name)) +
  facet_wrap(~ season, scales='free_x') + 
  xlab('') + ylab('') +
  labs(title='AL West Team Ratings: 2014-2019', subtitle = 'Parameters: K=12, R=400') +
  theme(legend.title = element_blank(), legend.position = 'bottom')

ggsave('RatingsALW.png', g1, height=5, width=7, dpi=120)


## Plot distribution of ratings for all teams

# Calculate ranks within division for sorting in graph
divisions <- c('AL West', 'AL Central', 'AL East', 'NL West', 'NL Central', 'NL East')
ranks <- elos %>% 
  group_by(division, teamid) %>%
  summarize(rating=median(rating)) %>%
  arrange(division, rating) %>%
  mutate(rank = as.factor(rank(rating)))

g2 <- elos %>% left_join(select(ranks, teamid, rank), by = c('teamid', 'division')) %>%
  ggplot(aes(y=name, x=rating)) + 
  geom_density_ridges(aes(fill=division), alpha=0.5) +
  facet_wrap(~division, scales='free_y') + 
  guides(fill=FALSE, color=FALSE) + 
  scale_x_continuous(breaks=seq(900,1450,100)) +
  scale_y_discrete(expand = c(0,0)) +
  labs(title='MLB Team Ratings 2010 - 2019',
       subtitle = 'Parameters: K=12, R=400\nWeighted by in-season days',
       x='Rating',
       y='')

ggsave('RatingDistr.png', g2, height=5, width=10, dpi=120)


