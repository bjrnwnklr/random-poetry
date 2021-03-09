from flask import Flask
from randompoetry import PoemFormRegistry, CorpusRegistry

app = Flask(__name__)

from app import routes

pfr = PoemFormRegistry.from_json('poemforms.json')
cr = CorpusRegistry()

