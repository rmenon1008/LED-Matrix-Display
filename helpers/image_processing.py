import numpy as np
import cv2

print("Loading image_processing.py")

def alpha_blend(images, background=(0, 0, 0)):
    bg_color = np.array(background, dtype=np.uint8)
    working_image = np.full(images[0][:, :, :3].shape, bg_color, dtype=np.uint8)

    for image in images:
        stripped = image[:, :, :3]
        alpha_channel = image[:, :, 3] / 255.0

        alpha_channel = np.expand_dims(alpha_channel, axis=2)
        working_image = working_image * (1 - alpha_channel) + stripped * alpha_channel

    return np.uint8(working_image)

def contain(image, container_size, position="tr", padding=(0, 0, 0, 0), crop=True):
    # Padding is top, right, bottom, left

    # Use the position to determine the x and y coordinates of the image
    assert position in ["tl", "tm", "tr", "ml", "mm", "mr", "bl", "bm", "br"]
    if position[0] == "t":
        y = padding[0]
    elif position[0] == "m":
        y = (container_size[1] - len(image)) // 2
    elif position[0] == "b":
        y = container_size[1] - len(image) - padding[2]

    if position[1] == "l":
        x = padding[3]
    elif position[1] == "m":
        x = (container_size[0] - len(image[0])) // 2
    elif position[1] == "r":
        x = container_size[0] - len(image[0]) - padding[1]

    # Crop the image if it is too large
    if crop:
        if len(image) > container_size[1]:
            image = image[:container_size[1]]
        if len(image[0]) > container_size[0]:
            image = image[:, :container_size[0]]

    # Pad the image
    try:
        padded = np.pad(image, ((y, container_size[1] - len(image) - y), (x, container_size[0] - len(image[0]) - x), (0, 0)), constant_values=0)
    except ValueError:
        return image
    return padded

        
def center_crop(image, aspect_ratio):
    height, width = image.shape[:2]
    image_aspect_ratio = width / height
    if image_aspect_ratio > aspect_ratio:
        # Crop width
        new_width = int(height * aspect_ratio)
        left = (width - new_width) // 2
        right = width - new_width - left
        return image[:, left:-right]
    elif image_aspect_ratio < aspect_ratio:
        # Crop height
        new_height = int(width / aspect_ratio)
        top = (height - new_height) // 2
        bottom = height - new_height - top
        return image[top:-bottom, :]
    else:
        return image

def crop_percentages(image, crop):
    height, width = image.shape[:2]
    x1, y1, x2, y2 = crop
    return image[int(y1 / 100 * height) : int(y2 / 100 * height),
                 int(x1 / 100 * width) : int(x2 / 100 * width)]


def ascii_print(array):
    """Print an array as ASCII art.

    Args:
        array (np.array): The array to print.
    """
    for row in array:
        for col in row:
            if col[3] == 255:
                print("█", end="")
            elif col[3] > 200:
                print("#", end="")
            elif col[3] > 100:
                print(":", end="")
            elif col[3] > 50:
                print(".", end="")
            else:
                print(" ", end="")
        print()

def adjust_brightness(image, value):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv[:,:,2] = cv2.add(value, hsv[:,:,2])
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return image