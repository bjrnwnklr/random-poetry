from flask import Flask
from randompoetry import PoemFormRegistry, CorpusRegistry

app = Flask(__name__)

pfr = PoemFormRegistry.from_json('poemforms.json')
cr = CorpusRegistry()

# this has to be at the bottom to avoid circular references
from app import routes
