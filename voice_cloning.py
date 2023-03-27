from resemble import Resemble
import os
from dotenv import load_dotenv

load_dotenv()
RESEMBLE_API_KEY = os.getenv("RESEMBLE_API_KEY")

Resemble.api_key(RESEMBLE_API_KEY)

