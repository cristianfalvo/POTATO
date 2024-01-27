from nordigen import NordigenClient
import os
from dotenv import load_dotenv


# Load secrets from .env file
load_dotenv()

client = NordigenClient(
    secret_id=os.getenv("SECRET_ID"),
    secret_key=os.getenv("SECRET_KEY")
)

# Generate access & refresh token
client.generate_token()