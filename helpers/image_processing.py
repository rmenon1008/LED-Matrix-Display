import numpy as np
import cv2

def alpha_blend(images, background=(0, 0, 0), color_replace=None):
    bg_color = np.array(background, dtype=np.uint8)
    working_image = np.full(images[0][:, :, :3].shape, bg_color, dtype=np.uint8)
    first = True

    for image in images:
        stripped = image[:, :, :3]
        alpha_channel = image[:, :, 3] / 255.0

        if color_replace is not None and not first:
            stripped = np.where(stripped == [1, 1, 1], color_replace[1], stripped)
            stripped = np.where(stripped == [254, 254, 254], color_replace[0], stripped)

        alpha_channel = np.expand_dims(alpha_channel, axis=2)
        working_image = working_image * (1 - alpha_channel) + stripped * alpha_channel
        first = False

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

def adjust_saturation(img, factor):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = np.clip(s * factor, 0, 255).astype(np.uint8)
    hsv = cv2.merge([h, s, v])
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

def adjust_temperature(img, factor):
    b, g, r = cv2.split(img)
    r = np.clip(r * factor, 0, 255).astype(np.uint8)
    b = np.clip(b / factor, 0, 255).astype(np.uint8)
    img = cv2.merge([b, g, r])
    return img

def image_adjustment(image, whitepoint=[255, 255, 255], blackpoint=[0, 0, 0], saturation=1.0, temperature=1.0):
    # Apply whitepoint and blackpoint
    image = image.astype(np.float32)
    whitepoint = np.array(whitepoint, dtype=np.float32)
    blackpoint = np.array(blackpoint, dtype=np.float32)
    image = (image - blackpoint) / (whitepoint - blackpoint)
    image = np.clip(image, 0, 1)
    image = (image * 255).astype(np.uint8)

    # Apply saturation and temperature
    image = adjust_saturation(image, saturation)
    image = adjust_temperature(image, temperature)

    return image

def get_fg_bg_colors(img):
    def brightness(rgb):
        return np.sqrt(np.dot(rgb, rgb))

    img = adjust_saturation(img, 1.2)
    pixels = np.float32(img.reshape(-1, 3))
    n_colors = 2
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
    flags = cv2.KMEANS_RANDOM_CENTERS
    _, _, palette = cv2.kmeans(pixels, n_colors, None, criteria, 10, flags)
    lightest = np.argmax([brightness(p) for p in palette])
    darkest = np.argmin([brightness(p) for p in palette])
    palette = np.uint8(palette)
    l = palette[lightest][:3]
    d = palette[darkest][:3]
    # Convert to HSV
    l = cv2.cvtColor(np.uint8([[l]]), cv2.COLOR_BGR2HSV)[0][0]
    d = cv2.cvtColor(np.uint8([[d]]), cv2.COLOR_BGR2HSV)[0][0]
    
    # Grab the HS and add V of 10
    l = np.array([l[0], l[1], 220])
    d = np.array([d[0], d[1], 35])

    # Convert back to BGR
    l = cv2.cvtColor(np.uint8([[l]]), cv2.COLOR_HSV2BGR)[0][0]
    d = cv2.cvtColor(np.uint8([[d]]), cv2.COLOR_HSV2BGR)[0][0]
    return l, d

def debug_show_image(image):
    cv2.imshow("image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()