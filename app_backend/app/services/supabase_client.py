from supabase import create_client, Client
from app.core.config import settings

try:
    supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase_client = None # Handle cases where Supabase might not be configured
