import os
import random
from PIL import Image
from typing import List, Dict, Any, Optional
import uuid

# In-memory game state storage
GAMES: Dict[str, Dict[str, Any]] = {}

CLOTHES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'clothes_tryon_dataset', 'train', 'cloth'))


def init_game(num_players: int, num_rounds: int, timer: int, n_clothes: int = 10) -> str:
    """
    Initialize a new game session and return the session_id.
    """
    session_id = str(uuid.uuid4())
    
    # Use actual dataset player names that correspond to image files
    PEOPLE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'clothes_tryon_dataset', 'train', 'image'))
    
    print(f"[init_game] Requested {num_players} players")
    
    if not os.path.exists(PEOPLE_DIR):
        print(f"Warning: PEOPLE_DIR does not exist: {PEOPLE_DIR}")
        # Fallback to fixed players only
        fixed_players = ['00002_00', '14684_00', '00154_00', '00001_00', '00003_00', '00004_00', '00005_00', '00006_00', '00007_00', '00008_00']
        players = fixed_players[:num_players]
        print(f"[init_game] Using fallback players: {players}")
    else:
        all_people = [f.replace('.jpg', '') for f in os.listdir(PEOPLE_DIR) if f.endswith('.jpg')]
        print(f"[init_game] Found {len(all_people)} people in dataset")
        
        # Use fixed players for consistency with frontend expectations
        fixed_players = ['00002_00', '14684_00', '00154_00', '00001_00', '00003_00', '00004_00', '00005_00', '00006_00', '00007_00', '00008_00']
        
        # Ensure we have enough players
        if num_players <= len(fixed_players):
            players = fixed_players[:num_players]
            print(f"[init_game] Using fixed players: {players}")
        else:
            # Use fixed players first, then sample from dataset
            available_players = [p for p in all_people if p not in fixed_players]
            print(f"[init_game] Available additional players: {len(available_players)}")
            
            if len(available_players) >= (num_players - len(fixed_players)):
                additional_players = random.sample(available_players, num_players - len(fixed_players))
                players = fixed_players + additional_players
                print(f"[init_game] Using fixed + additional players: {players}")
            else:
                # If not enough additional players, use what we have
                players = fixed_players + available_players[:num_players - len(fixed_players)]
                print(f"[init_game] Warning: Not enough players available. Using: {players}")
    
    print(f"[init_game] Final player count: {len(players)}")
    print(f"[init_game] Players: {players}")
    
    if not os.path.exists(CLOTHES_DIR):
        print(f"Warning: CLOTHES_DIR does not exist: {CLOTHES_DIR}")
        # Fallback to empty clothes list
        clothes = []
    else:
        all_clothes = [f for f in os.listdir(CLOTHES_DIR) if f.endswith('.jpg')]
        if len(all_clothes) < n_clothes:
            print(f"Warning: Only {len(all_clothes)} clothes available, requested {n_clothes}")
            clothes = all_clothes
        else:
            clothes = random.sample(all_clothes, n_clothes)
    
    GAMES[session_id] = {
        'players': players,
        'num_rounds': num_rounds,
        'timer': timer,
        'clothes': clothes,
        'current_round': 1,
        'picks': {},  # {round: {player: {other: cloth_idx}}}
        'rankings': {},  # {round: {player: [cloth_idx, ...]}}
        'leaderboard': {player: 0 for player in players},
        'used_clothes_per_round': {},  # {round: {player: set(cloth_indices)}} - track which clothes are used for each player per round
        'available_clothes_per_round': {}  # {round: {player: set(cloth_indices)}} - track available clothes for each player per round
    }
    
    print(f"[init_game] Game initialized with {len(players)} players: {players}")
    return session_id


def get_clothes(session_id: str) -> List[str]:
    """
    Get the list of clothes filenames for the session.
    """
    return GAMES[session_id]['clothes']


def get_available_clothes_for_player(session_id: str, round_num: int, target_player: str) -> List[int]:
    """
    Get available clothes indices for a specific player in a round.
    This ensures no duplicate clothes are picked for the same player.
    """
    game = GAMES[session_id]
    
    if round_num not in game['used_clothes_per_round']:
        game['used_clothes_per_round'][round_num] = {}
    
    if target_player not in game['used_clothes_per_round'][round_num]:
        game['used_clothes_per_round'][round_num][target_player] = set()
    
    used_clothes = game['used_clothes_per_round'][round_num][target_player]
    all_clothes_indices = set(range(len(game['clothes'])))
    available_indices = list(all_clothes_indices - used_clothes)
    
    return available_indices


def make_pick(session_id: str, round_num: int, player: str, picks: Dict[str, int]) -> None:
    """
    Store the picks for a player in a given round.
    picks: {other_player: cloth_idx}
    """
    game = GAMES[session_id]
    if round_num not in game['picks']:
        game['picks'][round_num] = {}
    
    # Validate picks to ensure no duplicates for the same target player
    for target_player, cloth_idx in picks.items():
        if round_num not in game['used_clothes_per_round']:
            game['used_clothes_per_round'][round_num] = {}
        if target_player not in game['used_clothes_per_round'][round_num]:
            game['used_clothes_per_round'][round_num][target_player] = set()
        
        # Check if this cloth is already used for this target player
        if cloth_idx in game['used_clothes_per_round'][round_num][target_player]:
            print(f"Warning: Cloth {cloth_idx} already used for {target_player} in round {round_num}")
            # Find an alternative available cloth
            available_clothes = get_available_clothes_for_player(session_id, round_num, target_player)
            if available_clothes:
                alternative_cloth = available_clothes[0]
                picks[target_player] = alternative_cloth
                print(f"Replaced with alternative cloth {alternative_cloth}")
            else:
                print(f"Error: No available clothes for {target_player}")
                continue
        
        # Mark this cloth as used for this target player
        game['used_clothes_per_round'][round_num][target_player].add(cloth_idx)
    
    game['picks'][round_num][player] = picks


def make_ranking(session_id: str, round_num: int, player: str, ranking: List[int]) -> None:
    """
    Store the ranking for a player in a given round.
    ranking: [cloth_idx, ...] (ordered)
    """
    game = GAMES[session_id]
    if round_num not in game['rankings']:
        game['rankings'][round_num] = {}
    
    # Get actual clothes picked for this player (including duplicates)
    picks = game['picks'].get(round_num, {})
    received_clothes = []
    
    # Get all clothes picked for this player (keep duplicates)
    for other_player in game['players']:
        if other_player != player and other_player in picks and player in picks[other_player]:
            cloth_idx = picks[other_player][player]
            received_clothes.append(cloth_idx)
    
    # Store the ranking with the actual received clothes (including duplicates)
    game['rankings'][round_num][player] = ranking
    
    # After all rankings for the round, update leaderboard
    if len(game['rankings'][round_num]) == len(game['players']):
        aggregate_scores(session_id, round_num)


def get_leaderboard(session_id: str) -> Dict[str, int]:
    """
    Get the current leaderboard for the session.
    """
    return GAMES[session_id]['leaderboard']


def aggregate_scores(session_id: str, round_num: int) -> None:
    """
    Aggregate scores for a round and update the leaderboard.
    """
    game = GAMES[session_id]
    picks = game['picks'][round_num]
    rankings = game['rankings'][round_num]
    leaderboard = game['leaderboard']
    players = game['players']
    
    for player, ranking in rankings.items():
        n = len(ranking)
        for rank, cloth_idx in enumerate(ranking):
            points = n - rank
            # Find all players who picked this cloth for the current player
            for other in players:
                if other != player and other in picks and player in picks[other]:
                    if picks[other][player] == cloth_idx:
                        leaderboard[other] += points


def get_game_state(session_id: str) -> Dict[str, Any]:
    """
    Get the full game state (for debugging or admin).
    """
    return GAMES[session_id]


def get_image_path(filename: str) -> str:
    """
    Get the absolute path to a cloth image.
    """
    return os.path.abspath(os.path.join(CLOTHES_DIR, filename))


def remove_game(session_id: str) -> None:
    """
    Remove a game session (cleanup).
    """
    if session_id in GAMES:
        del GAMES[session_id] 