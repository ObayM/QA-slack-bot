import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_config_value(key: str, default=None):
    """
    fetches a single value from the config table by key
    """
    try:
        res = supabase.table('config').select('value').eq('key', key).single().execute()
        return res.data['value']
    except Exception:
        return default


def get_moderators() -> set:
    """
    fetches the current set of moderator ids
    """
    try:
        res = supabase.table('moderators').select('user_id').execute()
        return {item['user_id'] for item in res.data}
    
    except Exception:
        return set()


def get_onboarding_channels() -> set:
    """
    fetches channels that trigger a welcome message
    """
    try:
        res = supabase.table('onboarding_channels').select('channel_id').execute()
        return {item['channel_id'] for item in res.data}
    
    except Exception:
        return set()


def get_tiers() -> list:
    """
    fetches all tier definitions, ordered by points
    """
    try:
        return supabase.table('tiers').select('*').order('points_required').execute().data
    except Exception:
        return []

def get_achievements() -> dict:
    """
    fetches all achievement definitions as a dictionary
    """
    try:
        res = supabase.table('achievements').select('*').execute().data
        return {item['id']: item for item in res}
    except Exception:
        return {}



def get_user_stats(user_id: str) -> dict:
    """
    fetches a user's score and solution count
    """
    try:
        res = supabase.table('scores').select('score, solutions_count').eq('user_id', user_id).single().execute()
        return res.data
    except Exception:
        return {'score': 0, 'solutions_count': 0}

def get_user_achievements(user_id: str) -> set:
    """
    gets a set of achievement ids a user has earned
    """
    try:
        res = supabase.table('user_achievements').select('achievement_id').eq('user_id', user_id).execute()
        return {item['achievement_id'] for item in res.data}
    except Exception:
        return set()

def get_leaderboard(limit: int = 10) -> list:
    """retrieves the top users from the scores table."""
    try:
        return supabase.table('scores').select('user_id, score').order('score', desc=True).limit(limit).execute().data
    except Exception:
        return []



def award_solver_points(user_id: str, points: int):
    supabase.rpc('add_solver_points', {'user_id_to_update': user_id, 'points_to_add': points}).execute()

def award_contributor_points(user_id: str, points: int):
    supabase.rpc('add_contributor_points', {'user_id_to_update': user_id, 'points_to_add': points}).execute()

def grant_achievement(user_id: str, achievement_id: str):
    """
    Grants an achievement to a user and it does nothing if they already have it.
    """
    try:
        
        supabase.table('user_achievements').upsert({
            'user_id': user_id, 
            'achievement_id': achievement_id
        }).execute()

        print(f"Granted achievement '{achievement_id}' to user {user_id}")
    except Exception as e:
        print(f"Error granting achievement {achievement_id} to {user_id}: {e}")