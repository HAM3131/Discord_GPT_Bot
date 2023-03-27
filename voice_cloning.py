from resemble import Resemble
import os
from dotenv import load_dotenv

load_dotenv()
RESEMBLE_API_KEY = os.getenv("RESEMBLE_API_KEY")

uuid = 'project-uuid'
voice_uuid= 'voice-uuid'

Resemble.api_key(RESEMBLE_API_KEY)
  
name = 'Discord Voice Clone'
description = 'This is a basic attempt to clone the voices of my friends, recorded on discord.'
is_public = False
is_archived = False
is_collaborative = False
  
response = Resemble.v2.projects.create(name, description, is_public, is_collaborative, is_archived)
project = response['item']
uuid = project['uuid']

name = 'Test Voice'
response = Resemble.v2.voices.create(name)
voice = response['item']

voice_uuid = voice['uuid']
name = 'recording'
text = 'This is a test'
is_active = True
emotion = 'neutral'

with open("path/to/audio.wav", 'rb') as file:
  response = Resemble.v2.recordings.create(voice_uuid, file, name, text, is_active, emotion)
  recording = response['item']