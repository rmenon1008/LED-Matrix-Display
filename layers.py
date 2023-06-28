import threading
import time

import cv2
import numpy as np

from helpers.yt_streamer import YtStreamer
from helpers.image_processing import contain, center_crop, crop_percentages

# Base class for matrix layers. Each layer is a 2D array of RGBA values that can be stacked.
# Layers have a fixed size when initialized, that matches the size of the matrix.
# Layers are updated with the get_frame() method, which returns a 2D array of RGBA values.


def tween(amount, func="ease_in"):
    amount = min(max(amount, 0), 1)
    # match func:
    #     case "ease_in":
    #         return amount**3
    #     case "ease_in_fast":
    #         return amount**4
    #     case "ease_out":
    #         return 1 - (1 - amount)**3
    #     case "ease_in_out":
    #         if amount < 0.5:
    #             return 2 * amount**3
    #         else:
    #             return 1 - 2 * (1 - amount)**3
    #     case _:
    #         return amount
    if func == "ease_in":
        return amount**3
    elif func == "ease_in_fast":
        return amount**4
    elif func == "ease_out":
        return 1 - (1-amount)**3
    elif func == "ease_in_out":
        if amount < 0.5:
            return 2 * amount**3
        else:
            return 1 - 2 * (1-amount)**3
    else:
        return amount

class Layer:
    def __init__(self, size):
        self.size = size
        self.blank = np.zeros((self.size[1], self.size[0], 4), dtype=np.uint8)
        self.pixels = self.blank.copy()

class BackgroundLayer(Layer):
    def __init__(self, queue):
        super().__init__((96, 48))
        self.queue = queue
        self.start_time = None

    def clear(self):
        self.start_time = None
        self.pixels = self.blank.copy()
        while not self.queue.empty():
            self.queue.get()
        
    def _fade(self, creation_time, enter_duration=0.8):
        time_since_creation = time.time() - creation_time
        if time_since_creation < enter_duration:
            opacity_amt = tween(time_since_creation / enter_duration, func="ease_out")
        else:
            opacity_amt = 1
        return opacity_amt

    def get_frame(self):
        while not self.queue.empty():
            self.pixels = self.queue.get()
            if self.start_time is None:
                print("Starting fade")
                self.start_time = time.time()

        pixels = self.pixels.copy()
        if self.start_time is not None:
            opacity_amt = self._fade(self.start_time)
            pixels[:,:,3] = (pixels[:,:,3] * opacity_amt).astype(np.uint8)
            
        return pixels


class NotificationLayer(Layer):
    WIDTH = 66
    MAX_HEIGHT = 15
    def __init__(self, queue):
        super().__init__((96, 48))
        self.notifications = {}
        self.queue = queue

    def clear(self):
        self.notifications = {}

    def _update_notification(self, notification):
        if notification.render.shape[1] != self.WIDTH:
            print(f"Notification has wrong width: {notification.render.shape[1]}")
            return
        if notification.render.shape[0] > self.MAX_HEIGHT:
            print(f"Notification is too tall: {notification.render.shape[0]}")
            return
        
        notification.creation_time = time.time()
        notification.expiry_time = time.time() + notification.duration
        self.notifications[notification.key] = notification

    def _slide_fade(self, creation_time, expire_time, enter_duration=0.4, exit_duration=0.4):
        time_before_expire = expire_time - time.time()
        time_since_creation = time.time() - creation_time
        if time_since_creation < enter_duration:
            height_amt = 1
            opacity_amt = tween(time_since_creation / enter_duration, func="ease_out")
        elif time_before_expire < exit_duration:
            height_amt = tween(time_before_expire / exit_duration, func="ease_in")
            opacity_amt = tween(time_before_expire / exit_duration, func="ease_in_fast")
        else:
            height_amt = 1
            opacity_amt = 1
        return height_amt, opacity_amt
    
    def get_frame(self):
        # Process the queue of updates
        while not self.queue.empty():
            notification = self.queue.get()
            self._update_notification(notification)
        
        # Check if any notifications have expired
        for key in list(self.notifications.keys()):
            notification = self.notifications[key]
            if time.time() > notification.expiry_time:
                self.notifications.pop(key)

        # Sort notifications by creation time
        notifications_sorted = sorted(self.notifications.values(), key=lambda x: x.creation_time, reverse=True)

        # Render notifications
        notification_pixels = []
        cumulative_height = 0
        for i in range(len(notifications_sorted)):
            notification = notifications_sorted[i]
            render = notification.render.copy()
            height_amt, opacity_amt = self._slide_fade(notification.creation_time, notification.expiry_time)
            render[:, :, 3] = np.uint8(render[:, :, 3] * opacity_amt)
            height = render.shape[0]
            if i != len(notifications_sorted) - 1:
                height = int(render.shape[0] * height_amt)
                render = render[:height]
            notification_pixels.append(render)
            cumulative_height += height

            if cumulative_height > self.size[1]:
                notification_pixels.pop()
                break

        if len(notification_pixels) == 0:
            return self.blank
        
        notification_pixels = np.vstack(notification_pixels)
        if len(notification_pixels) == 0:
            return self.blank

        return contain(notification_pixels, self.size, position="tl", padding=(1, 0, 0, 1))        

class WidgetLayer(Layer):
    WIDTH = 30
    MAX_HEIGHT = 15
    def __init__(self, queue):
        super().__init__((96, 48))
        self.widgets = {}
        self.queue = queue

    def clear(self):
        self.widgets = {}

    def _update_widget(self, widget):
        if widget.render.shape[1] != self.WIDTH:
            print(f"Widget has wrong width: {widget.render.shape[1]}")
            return False
        if widget.render.shape[0] > self.MAX_HEIGHT:
            print(f"Widget is too tall: {widget.render.shape[0]}")
            return False
        
        if widget.name not in self.widgets:
            widget.creation_time = time.time()
        else:
            widget.creation_time = self.widgets[widget.name].creation_time
            
        self.widgets[widget.name] = widget
        return True
    
    def _fade(self, creation_time, enter_duration=0.4):
        time_since_creation = time.time() - creation_time
        if time_since_creation < enter_duration:
            opacity_amt = tween(time_since_creation / enter_duration, func="ease_out")
        else:
            opacity_amt = 1
        return opacity_amt

    def get_frame(self):
        # Process the queue of updates
        while not self.queue.empty():
            widget = self.queue.get()
            self._update_widget(widget)

        widget_pixels = []
        cumulative_height = 0

        widgets = list(self.widgets.values())
        widgets.sort(key=lambda widget: widget.priority)

        for widget in widgets:
            render = widget.render.copy()
            opacity_amt = self._fade(widget.creation_time)
            render[:, :, 3] = np.uint8(render[:, :, 3] * opacity_amt)
            widget_pixels.append(render)
            cumulative_height += render.shape[0]

            if cumulative_height > self.size[1]:
                widget_pixels.pop()
                break

        if len(widget_pixels) == 0:
            return self.blank
        
        widget_pixels = np.vstack(widget_pixels)
        return contain(widget_pixels, self.size, position="tr", padding=(1, 1, 0, 0))
