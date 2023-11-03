from helpers.image_processing import alpha_blend
from apps import Time, Weather, YtStream, AstronautIo
import time

class Renderer:
    def __init__(self, config):
        self.config = config

        self.apps = []
        self.setup_apps(config.get("apps", []))

        self.foreground_color = None
        self.background_color = None
        self.last_color_update = 0

        print(self.apps)

    def setup_apps(self, app_list):
        for app in app_list:
            app_obj = self.get_app(app)
            if app_obj:
                self.apps.append(app_obj)
            else:
                print(f"Invalid app: {app}")
        
    def get_app(self, app_dict):
        name = app_dict.get("name", None)
        options = app_dict.get("options", {})
        options["_global_settings"] = {
            x: self.config[x] for x in self.config if x != "apps"
        }
        if name == "time":
            return Time(**options)
        elif name == "weather":
            return Weather(**options)
        elif name == "yt_stream":
            return YtStream(**options)
        elif name == "astronaut_io":
            return AstronautIo(**options)
        else:
            return None
        
    def update_colors(self):
        ALPHA = 0.15
        self.last_color_update = time.time()
        fg, bg = self.apps[0].get_colors()
        self.foreground_color = fg * ALPHA + self.foreground_color * (1-ALPHA) if self.foreground_color is not None else fg
        self.background_color = bg * ALPHA + self.background_color * (1-ALPHA) if self.background_color is not None else bg
    
    def get_frame(self):
        if time.time() - self.last_color_update > 1/20:
            self.update_colors()
        return alpha_blend([app.get_frame() for app in self.apps], color_replace=(self.foreground_color, self.background_color))