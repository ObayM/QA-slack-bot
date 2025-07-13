import os
from supabase import create_client, Client

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_app_settings():
    """
    Loads the necessary config data at startup
    """
    try:
        config_data = supabase.table('config').select('key, value').execute().data
        moderator_data = supabase.table('moderators').select('user_id').execute().data

        # turn the data into a dict
        app_config = {item['key']: item['value'] for item in config_data}
        app_config['SOLVER_POINTS'] = int(app_config.get('SOLVER_POINTS', 5))
        app_config['CONTRIBUTOR_POINTS'] = int(app_config.get('CONTRIBUTOR_POINTS', 1))
        app_config['LEADERBOARD_LIMIT'] = int(app_config.get('LEADERBOARD_LIMIT', 10))

        # used sets because they are faster for lookups
        moderator_ids = {item['user_id'] for item in moderator_data}

        return app_config, moderator_ids
    
    except Exception as e:
        print(f"Something went wrong with supabase: {e}")


def add_points(user_id: str, points: int):
    """
    This adds the specified number of points to using the 'increment_score' database function
    """
    try:
        supabase.rpc(
            'increment_score', 
            {'user_id_to_update': user_id, 'points_to_add': points}
        ).execute()

    except Exception as e:
        print(f"Error adding points for user {user_id} in Supabase: {e}")

def get_leaderboard(limit: int = 10):
    """
    this gets the list of the users sorted by the most points
    """
    try:
        response = supabase.table('scores').select('user_id, score').order('score', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching leaderboard from Supabase: {e}")
        return []
    
