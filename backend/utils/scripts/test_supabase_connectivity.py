import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_supabase_connectivity():
    # Fetch Supabase URL and Key from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not set.")
        return

    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)

        # Test querying the agent_runs table
        response = supabase.table("agent_runs").select("*").limit(1).execute()

        if response.data:
            print("Supabase connectivity test successful.")
            print("Sample data from agent_runs table:", response.data)
        elif response.error:
            print("Error: Supabase returned an error.")
            print("Error details:", response.error)

    except Exception as e:
        print("Error: An exception occurred while testing Supabase connectivity.")
        print(str(e))

if __name__ == "__main__":
    test_supabase_connectivity()
