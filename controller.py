from renderer import Renderer
# from matrix_emulator.matrix import Matrix
from matrix_driver.matrix_driver import Matrix
import time
import threading
import json
# import matplotlib.pyplot as plt
import os
# import flask

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

OAUTH_CLIENT_ID = "96003940279-tqk350i81u593stnkvod2914vlqpf21h.apps.googleusercontent.com"
DIMENSIONS = (96, 48)  # (height, width)
DEFAULT_CONFIG = {
    "first_run": True,
    "ssid": None,
    "password": None,
    "hostname": "dotboard",
    "oauth_credentials": None,
    "apps": {
        "setup": {}
    }
}

class Controller():
    def __init__(self):
        config = None
        try:
            with open("config/config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            print("No config file found, using defaults")
            config = DEFAULT_CONFIG
        except json.decoder.JSONDecodeError:
            print("Config file is invalid, resetting to defaults")
            config = DEFAULT_CONFIG
        self.config = config

        self.matrix = Matrix(DIMENSIONS)
        self.renderer = Renderer(self.config["apps"])

        self.render_thread = threading.Thread(target=self._render_loop)
        self.render_thread.start()
        # self._run_config_server()
    
    # def _run_config_server(self):
    #     # Start the local web server
    #     sf = os.path.abspath("configuration/web/static")
    #     tf = os.path.abspath("configuration/web/templates")
    #     app = flask.Flask(__name__, static_folder=sf, template_folder=tf)

    #     @app.route('/', methods=['GET'])
    #     def home():
    #         return flask.render_template("index.html")

    #     @app.route('/apps', methods=['GET'])
    #     def get_apps():
    #         return flask.jsonify(self.config["apps"])
        
    #     @app.route('/apps', methods=['POST'])
    #     def set_apps():
    #         apps = flask.request.json
    #         self.update_apps(apps)
    #         return flask.jsonify(self.config["apps"])
        
    #     @app.route('/google_oauth', methods=['GET'])
    #     def set_up_google_oauth():
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'configuration/web/client_secret.json',
    #             scopes=['https://www.googleapis.com/auth/calendar.readonly']
    #         )
    #         creds = flow.run_local_server(port=2323)
            
    #         self.config["oauth_credentials"] = credentials_to_dict(creds)
    #         with open("config/config.json", "w") as f:
    #             json.dump(self.config, f)
    #         return flask.redirect(flask.url_for('home'))
        
        # @app.route('/oauth2callback', methods=['GET'])
        # def oauth2callback():
        #     flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        #         'configuration/web/client_secret.json',
        #         scopes=['https://www.googleapis.com/auth/calendar.readonly'],
        #         redirect_uri='http://localhost:1313/oauth2callback'
        #     )
        #     flow.fetch_token(authorization_response=flask.request.url)
        #     credentials = flow.credentials
        #     self.config["oauth_credentials"] = credentials_to_dict(credentials)
        #     with open("config/config.json", "w") as f:
        #         json.dump(self.config, f)
        #     return flask.redirect(flask.url_for('home'))
        
        # def credentials_to_dict(credentials):
        #     return {'token': credentials.token,
        #             'refresh_token': credentials.refresh_token,
        #             'token_uri': credentials.token_uri,
        #             'client_id': credentials.client_id,
        #             'client_secret': credentials.client_secret,
        #             'scopes': credentials.scopes}

        # app.run(host="localhost", port=1313)

    def _render_loop(self):
        while True:
            time.sleep(0.005)
            self.matrix.set_pixels(self.renderer.get_frame())

    def update_apps(self, app_dict):
        self.renderer.update_apps(app_dict)
        self.config["apps"] = app_dict
        with open("config/config.json", "w") as f:
            json.dump(self.config, f)

if __name__ == "__main__":
    controller = Controller()