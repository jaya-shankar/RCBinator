# @uthor: Sumanth Nethi
# Date: 04-29-2023
# RCBinator

import random
import numpy as np
import copy
import math
from datetime import datetime, timedelta
from collections import deque

from ipl_helper.cricbuzz_scraper import get_ipl_schedule, get_points_table, matches_played

# Recent form weightage (last 3-5 matches)
FORM_WEIGHT = 0.3
# Points and NRR weightage
POINTS_WEIGHT = 0.6
NRR_WEIGHT = 0.1

# Track the last n matches for each team
RECENT_MATCHES_WINDOW = 3

# Initialize form and track recent match results
team_form = {team: 0.5 for team in ["CSK", "DC", "GT", "MI", "PBSK", "RR", "RCB", "SRH", "KKR", "LSG"]}
recent_results = {team: deque(maxlen=RECENT_MATCHES_WINDOW) for team in ["CSK", "DC", "GT", "MI", "PBSK", "RR", "RCB", "SRH", "KKR", "LSG"]}

# Head-to-head records (historical data - can be updated)
head_to_head_advantage = {
    "CSK": {"MI": 0.45, "RCB": 0.65},  # CSK historically struggles against MI but dominates RCB
    "MI": {"CSK": 0.55, "SRH": 0.60},
    "RCB": {"CSK": 0.35, "KKR": 0.45},
    "SRH": {"RCB": 0.60, "MI": 0.40},
    "KKR": {"RCB": 0.55, "MI": 0.45},
    "DC": {"CSK": 0.45, "RCB": 0.55},
    "PBSK": {"MI": 0.40, "RCB": 0.55},
    "RR": {"SRH": 0.50, "CSK": 0.45},
    "GT": {"RR": 0.55, "LSG": 0.50},
    "LSG": {"GT": 0.50, "RR": 0.55}
}

# Precomputed NRR changes for faster calculation
NRR_CHANGES = {
    'low': 0.03,
    'medium': 0.05,
    'high': 0.08,
    'dominant': 0.12
}

# Enhanced NRR model based on match context - Optimized version
def calculate_nrr_change(team_a, team_b, winner, T):
    """Calculate a more realistic NRR change based on team strengths and match context - optimized"""
    # Get teams' current points
    points_a = T[team_a][0]
    points_b = T[team_b][0]
    
    # Points difference to determine match type
    points_diff = abs(points_a - points_b)
    
    # Use precomputed values instead of complex calculations
    if points_diff >= 8:  # Big gap in points
        nrr_change = NRR_CHANGES['high']
    elif points_diff >= 4:  # Medium gap
        nrr_change = NRR_CHANGES['medium']
    else:  # Close match
        nrr_change = NRR_CHANGES['low']
    
    # Add small randomness (reduced computation)
    if random.random() > 0.8:  # Only 20% of the time add randomness
        nrr_change *= 1.1
    
    return nrr_change


def calculate_team_form(team):
    """Calculate team form based on recent match results (wins/losses)"""
    if not recent_results[team]:  # If no recent matches, return default form
        return 0.5
    
    # Calculate form based on win/loss ratio in recent matches
    wins = sum(1 for result in recent_results[team] if result == 'W')
    form_value = wins / len(recent_results[team])
    
    # Scale to range 0.1 to 1.0
    return max(0.1, min(1.0, 0.1 + 0.9 * form_value))


def update_team_form(winner, loser):
    """Update team form based on match results by recording recent match outcomes"""
    # Record match results
    recent_results[winner].append('W')  # Winner gets a Win
    recent_results[loser].append('L')   # Loser gets a Loss
    
    # Recalculate form values based on recent results
    team_form[winner] = calculate_team_form(winner)
    team_form[loser] = calculate_team_form(loser)


def IPL(team):
    T = get_points_table()
    matches_done = matches_played()
    S = get_ipl_schedule()[matches_done:]
    op, ot = [], []
    j = 0
    while j < 10 ** 4:
        P = []
        T_temp = T.copy()
        for x in S:
            i = random.randint(0, 1)
            T_temp[x[i]] += 2
            P.append([x, x[i]])
        l_temp = sorted(list(T_temp.values()), reverse=True)

        if T_temp[team] >= l_temp[3]:
            if P not in op:
                op.append(P)
                ot.append(dict(sorted(T_temp.items(), key=lambda item: item[1], reverse=True)))
        j += 1
    return 100 * len(op) / j


def AllTeams():
    matches_done = matches_played()
    probabilities = {}
    for i in get_points_table().keys():
        probabilities[i] = IPL(i)
    return probabilities


def MyTeam(team, T, matches_done, S, for_position, simulations=100_000):
    def calculate_strength(team_data, team_name):
        """Calculate team strength based on points, NRR and recent form - simplified for speed"""
        points, nrr = team_data
        # Simple calculation for better performance
        normalized_points = points / 28  # Normalize to 0-1 (max 28 points possible)
        normalized_nrr = (nrr + 1.5) / 3  # Normalize to 0-1 (simplified range)
        
        # Get current form value based on recent matches
        current_form = team_form[team_name]
        
        # Fast calculation with fewer operations
        strength = (POINTS_WEIGHT * normalized_points) + (NRR_WEIGHT * normalized_nrr) + (FORM_WEIGHT * current_form)
        return max(0.1, min(1.0, strength))  # Clamp between 0.1 and 1.0

    def get_team_position(table, team_name):
        sorted_teams = sorted(table.values(), key=lambda x: (-x[0], -x[1]))
        for pos, t in enumerate(sorted_teams, 1):
            if (t[0], t[1]) == (table[team_name][0], table[team_name][1]):
                return pos
        return len(sorted_teams)
    
    # Reset recent results and form at the start of simulation
    for t in team_form:
        recent_results[t].clear()
        team_form[t] = 0.5
    
    no_remaining = len(S)

    if no_remaining == 0:
        pos = get_team_position(T, team)
        return (100.0 if pos <= for_position else 0.0, [], [])

    # Precompute match probabilities with enhanced model
    match_probs = []
    for match in S:
        team_a, team_b = match
        strength_a = calculate_strength(T[team_a], team_a)
        strength_b = calculate_strength(T[team_b], team_b)
        
        # Base probability from team strengths
        base_prob_a = strength_a / (strength_a + strength_b)
        
        # Apply head-to-head advantage if available
        h2h_modifier = 0
        if team_a in head_to_head_advantage and team_b in head_to_head_advantage[team_a]:
            h2h_modifier = head_to_head_advantage[team_a][team_b] - 0.5  # Convert from win% to advantage
        
        # Final probability
        prob_a = base_prob_a + h2h_modifier
        # Ensure probability is between 0.1 and 0.9 (no sure things in cricket)
        prob_a = max(0.1, min(0.9, prob_a))
        
        match_probs.append(prob_a)

    # Exhaustive search for <18 matches (weighted) - reduced from 22 for speed
    if no_remaining < 18:
        total_outcomes = 1 << no_remaining
        success = 0.0
        example_out = None
        example_tab = None

        for outcome in range(total_outcomes):
            # Reset form for each complete tournament scenario
            for t in team_form:
                recent_results[t].clear()
                team_form[t] = 0.5
                
            temp_T = copy.deepcopy(T)
            scenario = []
            scenario_prob = 1.0  # Track probability of this outcome
            
            for match_idx in range(no_remaining):
                team_a, team_b = S[match_idx]
                bit_pos = no_remaining - 1 - match_idx
                result = (outcome >> bit_pos) & 1
                
                # Recalculate match probability using current form values
                strength_a = calculate_strength(temp_T[team_a], team_a)
                strength_b = calculate_strength(temp_T[team_b], team_b)
                base_prob_a = strength_a / (strength_a + strength_b)
                
                # Apply head-to-head adjustment
                h2h_modifier = 0
                if team_a in head_to_head_advantage and team_b in head_to_head_advantage[team_a]:
                    h2h_modifier = head_to_head_advantage[team_a][team_b] - 0.5
                
                match_prob = max(0.1, min(0.9, base_prob_a + h2h_modifier))
                
                # Update probability for this outcome
                if result == 0:
                    scenario_prob *= match_prob
                    winner = team_a
                    loser = team_b
                else:
                    scenario_prob *= (1 - match_prob)
                    winner = team_b
                    loser = team_a
                
                # Calculate dynamic NRR change (optimized)
                nrr_change = calculate_nrr_change(team_a, team_b, winner, temp_T)
                
                # Update table
                temp_T[winner][0] += 2
                temp_T[winner][1] += nrr_change
                temp_T[loser][1] -= nrr_change
                scenario.append(((team_a, team_b), winner))
                
                # Update team form based on this match result
                update_team_form(winner, loser)

            # Check qualification
            sorted_teams = sorted(temp_T.values(), key=lambda x: (-x[0], -x[1]))
            cutoff = sorted_teams[for_position-1] if len(sorted_teams) >= for_position else (0, 0)
            team_entry = temp_T[team]
            
            if (team_entry[0] > cutoff[0]) or (team_entry[0] == cutoff[0] and team_entry[1] >= cutoff[1]):
                success += scenario_prob
                if not example_out:
                    example_out = scenario
                    example_tab = dict(sorted(temp_T.items(), key=lambda x: (-x[1][0], -x[1][1])))

        return (success * 100, example_out, example_tab)

    # Monte Carlo for ≥18 matches - optimized version
    else:
        teams = list(T.keys())
        team_idx = {t: i for i, t in enumerate(teams)}
        target_i = team_idx[team]
        matches = [(team_idx[m[0]], team_idx[m[1]]) for m in S]
        num_matches = len(matches)

        points = np.array([T[t][0] for t in teams], dtype=np.float32)
        nrr = np.array([T[t][1] for t in teams], dtype=np.float32)
        
        # Use optimized number of samples
        samples = min(simulations, 100_000)  # Cap samples for performance
        
        # Create arrays to track form and results for each team in each simulation
        team_forms = np.full((samples, len(teams)), 0.5, dtype=np.float32)
        
        # We'll use a different approach for Monte Carlo to track recent results
        # Instead of deques, we'll use a sliding window approach with fixed arrays
        # This is more efficient for vectorized operations
        
        # Array to store the outcomes for later form calculation
        match_winners = np.zeros((samples, num_matches), dtype=np.int32)

        # Generate outcomes using precomputed probabilities initially
        outcomes = np.random.binomial(1, match_probs, size=(samples, num_matches))

        pt = np.tile(points, (samples, 1))
        pt[pt > 22] = 22  # Cap points
        nr = np.tile(nrr, (samples, 1))

        # Process matches in batches for better performance
        for m_idx, (a, b) in enumerate(matches):
            team_a = teams[a]
            team_b = teams[b]
            
            # Recalculate match probabilities based on current form
            # We'll simplify this for performance, using the precomputed probabilities
            # In a more accurate model, we would recalculate for each sample
            
            a_wins = outcomes[:, m_idx].astype(bool)
            b_wins = ~a_wins
            
            # Update points
            pt[a_wins, a] += 2
            pt[b_wins, b] += 2
            
            # Update NRR (simplified)
            nr[a_wins, a] += 0.05
            nr[a_wins, b] -= 0.05
            nr[b_wins, b] += 0.05
            nr[b_wins, a] -= 0.05
            
            # Record match winners for form calculation
            match_winners[a_wins, m_idx] = a
            match_winners[b_wins, m_idx] = b
            
            # Update form based on the last RECENT_MATCHES_WINDOW matches
            if m_idx >= RECENT_MATCHES_WINDOW:
                # Look back at the last few matches for each team
                for sim in range(samples):
                    for t_idx in range(len(teams)):
                        # Count recent wins for this team
                        recent_win_count = 0
                        recent_match_count = 0
                        
                        # Check the last few matches involving this team
                        for prev_m_idx in range(max(0, m_idx - RECENT_MATCHES_WINDOW), m_idx):
                            prev_match = matches[prev_m_idx]
                            if t_idx in prev_match:  # If this team played in this match
                                recent_match_count += 1
                                if match_winners[sim, prev_m_idx] == t_idx:  # If this team won
                                    recent_win_count += 1
                        
                        # Update form if team played any recent matches
                        if recent_match_count > 0:
                            win_ratio = recent_win_count / recent_match_count
                            team_forms[sim, t_idx] = max(0.1, min(1.0, 0.1 + 0.9 * win_ratio))

        # Calculate rankings with weighted points/NRR (points dominate)
        composite = pt * 1000 + nr  # Points dominate by 1000:1 ratio
        rankings = np.argsort(-composite, axis=1)
        positions = np.argmax(rankings == target_i, axis=1)
        success_mask = positions < for_position
        success_count = np.sum(success_mask)

        # Example outcome
        example_out, example_tab = None, None
        if success_count > 0:
            idx = np.where(success_mask)[0][0]
            pt_ex = points.copy()
            nr_ex = nrr.copy()
            scenario = []
            
            # Reset form tracking for the example scenario
            for t in team_form:
                recent_results[t].clear()
                team_form[t] = 0.5
            
            for m_idx, (a, b) in enumerate(matches):
                result = outcomes[idx, m_idx]
                team_a = teams[a]
                team_b = teams[b]
                
                if result:
                    winner = team_a
                    loser = team_b
                else:
                    winner = team_b
                    loser = team_a
                
                # Calculate a representative NRR change
                nrr_change = calculate_nrr_change(team_a, team_b, winner, {
                    team_a: (float(pt_ex[a]), float(nr_ex[a])),
                    team_b: (float(pt_ex[b]), float(nr_ex[b]))
                })
                
                scenario.append(((team_a, team_b), winner))
                
                if result:
                    pt_ex[a] += 2
                    nr_ex[a] += nrr_change
                    nr_ex[b] -= nrr_change
                else:
                    pt_ex[b] += 2
                    nr_ex[b] += nrr_change
                    nr_ex[a] -= nrr_change
                
                # Update team form for next calculations
                update_team_form(winner, loser)

            sorted_t = sorted(zip(pt_ex, nr_ex, teams), 
                            key=lambda x: (-x[0], -x[1]))
            example_tab = {t: (float(p), float(n)) for p, n, t in sorted_t}
            example_out = scenario

        return (success_count / samples * 100, example_out, example_tab)
