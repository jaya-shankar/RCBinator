import requests
from bs4 import BeautifulSoup
import re


def get_ipl_page_url():
    base_url = "https://www.cricbuzz.com"
    series_url = base_url + "/cricket-series"
    response = requests.get(series_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    ipl_page_url = soup.find('a', href=re.compile(r'/cricket-series/\d+/indian-premier-league-2026'))['href']
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
    url = get_ipl_page_url() + '/matches'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find script tags containing match data JSON
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'matchDetailsMap' in script.string:
            # Count matches with "won by" which indicates completed matches
            won_count = script.string.count(' won by ')
            return won_count
    
    return 0


def get_ipl_schedule():
    url = get_ipl_page_url() + '/matches'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    schedule = []
    
    # Find script tags containing match data JSON
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'matchDetailsMap' in script.string:
            content = script.string
            
            # Extract all match entries with team info
            # Pattern: "teamSName":"TEAM" or 'teamSName':'TEAM' or teamSName":"TEAM"
            # Try different quote patterns
            team_names = re.findall(r'teamSName["\']:["\']([A-Z]+)["\']', content)
            
            if not team_names:
                # Try with escaped quotes as backup
                team_names = re.findall(r'\\"teamSName\\":\\"([A-Z]+)\\"', content)
            
            # Process teams in pairs (each match has team1 and team2)
            # Each match appears twice in the data (once in visible list, once in detail)
            # So we take every 4th pair to get unique matches
            seen = set()
            for i in range(0, len(team_names), 2):
                if i + 1 < len(team_names):
                    team1, team2 = team_names[i], team_names[i+1]
                    
                    # Normalize team names to match app expectations
                    if team1 == 'PBKS':
                        team1 = 'PBSK'
                    if team2 == 'PBKS':
                        team2 = 'PBSK'
                    
                    match_key = tuple(sorted([team1, team2]))
                    
                    if match_key not in seen:
                        schedule.append([team1, team2])
                        seen.add(match_key)
            
            break
    
    return schedule


def get_points_table():
    url = get_ipl_page_url()  + '/points-table'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    with open('ipl_helper/points_table_page.html', 'w') as f:
        f.write(soup.prettify())
    
    # Find all table rows with class 'point-table-grid'
    team_rows = soup.find_all('div', class_='point-table-grid')
    if not team_rows:
        return {}
    
    points_table = {}
    for row in team_rows:
        # Extract team abbreviation from the link text
        team_div = row.find('div', class_='text-xs')
        if not team_div:
            continue
        team = team_div.get_text().strip()
        
        # Normalize team names to match app expectations
        if team == 'PBKS':
            team = 'PBSK'
        
        # Extract all numeric values from the row
        value_divs = row.find_all('div', class_='flex justify-center items-center')
        if len(value_divs) < 6:
            continue
        
        # The order is: Matches, Won, Lost, No Result, Points, NRR
        pts = int(value_divs[4].get_text().strip())
        nrr = float(value_divs[5].get_text().strip())
        
        points_table[team] = [pts, nrr]
    
    return points_table
