import numpy as np
import cv2

print("Loading text.py")

import helpers.image_processing as imp
from fonts.fonts import SIX_TALL, ICONS

def _vertical_center_padding(max_height, height):
    bottom = (max_height - height) // 2
    top = max_height - height - bottom
    return bottom, top

def _render_glyph(glyph, glyph_depth=1, color=(255, 255, 255, 255)):
    output = np.full((len(glyph), len(glyph[0]), 4), np.array(color), dtype=np.uint8)
    output[:, :, 3] = (np.array(glyph) / glyph_depth) * color[3]
    return output

def _get_length(string, text_font, icon_font, outline=False):
    length = 0
    for char in string:
        if char in text_font.glyphs:
            glyph = text_font.glyphs[char]
        elif char in icon_font.glyphs:
            glyph = icon_font.glyphs[char]
        else:
            glyph = text_font.glyphs["?"]
        length += len(glyph[0])
        length += text_font.char_spacing
    length -= text_font.char_spacing
    if outline:
        length += 2
    return length

def render_string(
    string,
    text_font=SIX_TALL,
    icon_font=ICONS,
    line_br=False,
    ellipsis=False,
    crop=True,
    color=(255, 255, 255, 255),
    outline_color=None,
    container_size=None,
    container_pos="tl",
    container_padding=(0, 0, 0, 0),
    relative_vert_offset=0
):
    """Render a string using a font.

    Args:
        string (str): The string to render.
        text_font (dict, optional): The font to use for text characters. Defaults to SIX_TALL.
        icon_font (dict, optional): The font to use for icon characters. Defaults to ICONS.
        color (tuple, optional): The color to use for all characters. Defaults to (255, 255, 255, 255).
        outline_color (tuple, optional): The color to use for the outline of all characters. Defaults to None.
        container_size (tuple, optional): The size of the container to render the string in. Defaults to None.
        container_pos (str, optional): The position inside the container to render the string in. Defaults to "tl" (top, left).
        container_padding (tuple, optional): The padding of the container to render the string in. Defaults to (0, 0, 0, 0).

    Returns:
        np.array: The rendered string.
    """
    
    # Split the string into words
    words = string.split(" ")

    # Render each word
    rendered_words = []
    for word in words:
        # Check if the word is an icon
        if word in icon_font.glyphs:
            rendered_words.append(_render_glyph(icon_font.glyphs[word], color=color))

        # Otherwise, render the word as text
        else:
            if text_font.upper:
                word = word.upper()
            if text_font.lower:
                word = word.lower()
            for char in word:
                if char in text_font.glyphs:
                    glyph = text_font.glyphs[char]
                else:
                    glyph = text_font.glyphs["?"]
                
                rendered_words.append(_render_glyph(glyph, color=color))
                rendered_words.append(np.zeros((len(glyph), text_font.char_spacing, 4), dtype=np.uint8))

        if " " in text_font.glyphs:
            rendered_words.append(_render_glyph(text_font.glyphs[" "], color=color))

    # Find the height of the tallest character
    max_height = max(char.shape[0] for char in rendered_words)

    # Add the required vertical padding to each character (centered baseline)
    padded_words = []
    for char in rendered_words:
        top, bottom = _vertical_center_padding(max_height, char.shape[0] - text_font.baseline - relative_vert_offset)
        padded_words.append(np.pad(char, ((top, bottom), (0, 0), (0, 0)), mode="constant", constant_values=0))
    
    # Combine the characters into a single array
    pixels = np.hstack(padded_words)

    # Remove extra whitespace from the left and right sides
    pixels = pixels[:, np.where(pixels[:, :, 3].any(axis=0))[0][0]:np.where(pixels[:, :, 3].any(axis=0))[0][-1] + 1, :]

    # Add an outline if required
    if outline_color is not None:
        pixels = np.pad(pixels, ((1, 1), (1, 1), (0, 0)), mode="constant", constant_values=0)
        kernel = np.array([
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ], dtype=np.uint8)
        
        # Add the outline
        mat = np.where(pixels[:, :, 3] == 0, 0, 1).astype(np.uint8)
        dilated = cv2.dilate(mat, kernel, iterations=1)
        outline = dilated - mat
        for i in range(4):
            pixels[:, :, i] = np.where(outline == 0, pixels[:, :, i], outline * outline_color[i])

    # Check if the string should be ellipsized
    if ellipsis:
        # Check if the string is too long
        s = string
        length = _get_length(s, text_font, icon_font, outline=outline_color is not None)
        if length > container_size[0]:
            while length > container_size[0]:
                # Remove the last character
                s = s[:-1]
                length = _get_length(s + "~", text_font, icon_font, outline=outline_color is not None)
            
            # Render the ellipsized string
            s = s.strip()
            pixels = render_string(s + "~", text_font, icon_font, line_br=line_br, ellipsis=False, crop=crop, color=color, outline_color=outline_color, container_size=container_size, container_pos=container_pos, container_padding=container_padding)

    # Add the required padding to the container
    if container_size is not None:
        pixels = imp.contain(pixels, container_size, container_pos, container_padding, crop=crop)

    return pixels

# if __name__ == "__main__":
#     # Render a string
#     pixels = render_string("![CALENDAR] 2 min", container_size=(50, 50), container_pos="tl", container_padding=(0, 0, 0, 0), color=(255, 255, 255, 255))

#     # Print the pixels as ASCII art
#     ascii_print(pixels)