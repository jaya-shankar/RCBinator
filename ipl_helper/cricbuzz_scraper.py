import requests
from bs4 import BeautifulSoup
import random
import re
import numpy as np
import copy


def get_ipl_page_url():
    base_url = "https://www.cricbuzz.com"
    series_url = base_url + "/cricket-series"
    response = requests.get(series_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    ipl_page_url = soup.find('a', title='Indian Premier League 2026')['href']
    if not ipl_page_url:
        return None
    ipl_page_url = base_url + ipl_page_url
    return ipl_page_url

def get_abbreviations(team_names):
    abbreviations = []
    for name in team_names:
        abbreviation = ''.join([word[0] for word in name.split()])
        if abbreviation == 'SH':
            abbreviation = 'SRH'
        elif abbreviation == 'PK':
            abbreviation = 'PBSK'
        abbreviations.append(abbreviation)
    return abbreviations

def matches_played():
    url = get_ipl_page_url()  + '/matches'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    matches = soup.find_all('div', class_='cb-series-matches')
    schedule = [x.get_text() for x in matches]
    return sum([1 for x in schedule if 'won' in x])


def get_ipl_schedule():
    url = get_ipl_page_url()  + '/matches'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    matches = soup.find_all('div', class_='cb-series-matches')
    schedule = [x.get_text() for x in matches]
    schedule = [x.split(',')[0].strip() for x in schedule]
    schedule = [list(map(lambda x: x.strip(), x.split('vs'))) for x in schedule]
    schedule = [get_abbreviations(x) for x in schedule][:-4]

    return schedule


def get_points_table():
    url = get_ipl_page_url()  + '/points-table'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    teams = soup.find('table', class_='table cb-srs-pnts')
    table = [x.get_text() for x in teams.find_all('td', class_='cb-srs-pnts-name')]
    table = [''.join([word[0] for word in x.split()]) for x in table]
    table = [x.replace('SH', 'SRH') for x in table]
    table = [x.replace('PK', 'PBSK') for x in table]
    table = [re.sub(r'[^a-zA-Z]', '', text) for text in table]
    points = [x.get_text() for x in teams.find_all('td', class_='cb-srs-pnts-td')][5::7]
    nrr = [x.get_text() for x in teams.find_all('td', class_='cb-srs-pnts-td')][6::7]

    points = [int(x) for x in points]
    nrr = [float(x) for x in nrr]
    points_table = {}
    for team,pts,nrr in zip(table, points, nrr):
        points_table[team] = [pts,nrr]
    
    return points_table
