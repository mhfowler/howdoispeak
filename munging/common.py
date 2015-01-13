import os, json

# PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
# when building with setup.py use the line below, for some very confusing reason I can't figure out
PROJECT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

secrets_file_path = os.path.join(PROJECT_PATH, "secrets.json")
secrets_json = open(secrets_file_path).read()
SECRETS = json.loads(secrets_json)

