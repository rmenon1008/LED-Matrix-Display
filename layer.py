from yt_streamer import YtStreamer
import threading
import cv2
import time
import numpy as np
import text
import time
from image_processing import contain, center_crop, crop_percentages

# Base class for matrix layers. Each layer is a 2D array of RGBA values that can be stacked.
# Layers have a fixed size when initialized, that matches the size of the matrix.
# Layers are updated with the get_frame() method, which returns a 2D array of RGBA values.

class Layer:
    def __init__(self, size):
        self.size = size
        self.pixels = np.zeros((size[1], size[0], 4), dtype=np.uint8)
        self.thread = threading.Thread(target=self._refresh)
        self.thread.start()

    def _refresh(self):
        pass

    def get_frame(self):
        return self.pixels

class YtStreamLayer(Layer):
    def __init__(self, size, yt_url, desired_width, crop=None):
        self.yt_url = yt_url
        self.desired_width = desired_width
        self.crop = crop
        super().__init__(size)
    
    def _refresh(self):
        self.streamer = YtStreamer(self.yt_url, self.desired_width)
        while True:
            frame = self.streamer.next_frame()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            if self.crop:
                frame = crop_percentages(frame, self.crop)
            frame = center_crop(frame, self.size[0]/self.size[1])
            frame = cv2.resize(frame, self.size, interpolation=cv2.INTER_AREA)
            self.pixels = frame
        
# class TimeLayer(Layer):
#     def __init__(self, size):
#         super().__init__(size)
    
#     def refresh(self):
#         while True:
#             time_str = time.strftime("%-I:%M")
#             string = time_str
#             time_pixels = np.uint8(text.render_string(string, font=font.NUMBERS_FOUR_TALL, size=self.size, position="tr", offset=(1, 1)))
#             time_pixels = cv2.cvtColor(time_pixels, cv2.COLOR_GRAY2RGBA)

#             # Set alpha to 0 for black pixels
#             time_pixels[time_pixels[:, :, 0] == 0] = [0, 0, 0, 0]
#             time_pixels[time_pixels[:, :, 0] == 255] = [255, 255, 255, 255]

#             self.pixels = time_pixels
#             time.sleep(1)

class NotificationLayer(Layer):
    WIDTH = 60
    MAX_HEIGHT = 10
    def __init__(self):
        self.notifications = []
        super().__init__((96, 48))

    def add_notification(self, notification):
        if notification.render.shape[1] != self.WIDTH:
            return False
        if notification.render.shape[0] > self.MAX_HEIGHT:
            return False
        
        notification.creation_time = time.time()
        notification.expiry_time = time.time() + notification.duration
        self.notifications.append(notification)
        return True
    
    def _refresh(self):
        while True:
            # Check if any notifications have expired
            for notification in self.notifications:
                if time.time() > notification.expiry_time:
                    self.notifications.remove(notification)

            # Sort notifications by creation time
            self.notifications.sort(key=lambda notification: notification.creation_time)

            # Render notifications
            notification_pixels = []
            cumulative_height = 0
            for notification in self.notifications:
                render = notification.render
                notification_pixels.append(render)
                cumulative_height += render.shape[0]

                if cumulative_height > self.size[1]:
                    notification_pixels.pop()
                    break
            if len(notification_pixels) > 0:
                notification_pixels = np.vstack(notification_pixels)

                self.pixels = contain(notification_pixels, self.size, position="tl")

            time.sleep(1)
        

class WidgetLayer(Layer):
    WIDTH = 36
    MAX_HEIGHT = 10
    def __init__(self):
        self.widgets = {}
        super().__init__((96, 48))

    def update_widget(self, widget):
        if widget.render.shape[1] != self.WIDTH:
            print(f"Widget has wrong width: {widget.render.shape[1]}")
            return False
        if widget.render.shape[0] > self.MAX_HEIGHT:
            print(f"Widget is too tall: {widget.render.shape[0]}")
            return False
        
        self.widgets[widget.name] = widget
        return True

    def _refresh(self):
        while True:
            widget_pixels = []
            cumulative_height = 0

            widgets = list(self.widgets.values())
            widgets.sort(key=lambda widget: widget.priority)

            for widget in widgets:
                render = widget.render
                widget_pixels.append(render)
                cumulative_height += render.shape[0]

                if cumulative_height > self.size[1]:
                    widget_pixels.pop()
                    break

            if len(widget_pixels) == 0:
                time.sleep(2)
                continue
            
            widget_pixels = np.vstack(widget_pixels)
            self.pixels = contain(widget_pixels, self.size, position="tr")

            time.sleep(1)
