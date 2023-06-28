import json

print("Loading fonts.py")

class Font:
    def __init__(self, font_dict):
        self.height = font_dict["height"]
        self.glyphs = font_dict["glyphs"]

        self.char_spacing = font_dict.get("char_spacing", 0)
        self.upper = font_dict.get("upper", False)
        self.lower = font_dict.get("lower", False)
        self.baseline = font_dict.get("baseline", 0)

    def to_json(self):
        return json.dumps({
            "height": self.height,
            "upper": self.upper,
            "lower": self.lower,
            "glyphs": self.glyphs
        })

class FileFont(Font):
    def __init__(self, font_dict):
        # Generate the glyphs from the file
        with open(font_dict["glyph_file"]) as f:
            raw_glyphs = json.load(f)
            glyphs = {}
            for char_int in raw_glyphs:
                raw_glyph = raw_glyphs[char_int]
                if isinstance(raw_glyph, list):
                    glyph = []

                    for item in raw_glyph:
                        binary = bin(item)[2:][::-1]
                        binary = binary + "0" * (16 - len(binary))
                        row = []
                        for c in range(len(binary)):
                            row.append(int(binary[c]))
                        glyph.append(row)

                    # Crop the glyph to the first and last non-empty columns
                    left_col = 0
                    right_col = len(glyph[0])
                    for col in range(len(glyph[0])):
                        if any(glyph[row][col] for row in range(len(glyph))):
                            left_col = col
                            break
                    for col in range(len(glyph[0]) - 1, -1, -1):
                        if any(glyph[row][col] for row in range(len(glyph))):
                            right_col = col
                            break
                    glyph = [row[left_col:right_col + 1] for row in glyph]

                    # Remove empty rows
                    top_row = len(glyph) - font_dict.get("height", 0) - 4
                    bottom_row = len(glyph) - 4
                    glyph = glyph[top_row:bottom_row]
                    
                    if "char_map" in font_dict and char_int in font_dict["char_map"]:
                        char = font_dict["char_map"][char_int]
                    else:
                        char = chr(int(char_int))
                    glyphs[char] = glyph

            # Add a space glyph if there isn't one
            if " " not in glyphs and "space_width" in font_dict:
                height = font_dict["height"]
                space_glyph = [[0] * font_dict["space_width"] for _ in range(height)]
                glyphs[" "] = space_glyph

            # Add a half-space glyph if there isn't one
            if "`" not in glyphs:
                height = font_dict["height"]
                space_glyph = [[] for _ in range(height)]
                glyphs["`"] = space_glyph
    
        font_dict["glyphs"] = glyphs
        super().__init__(font_dict)


FOUR_TALL = FileFont({
    "height": 4,
    "upper": True,
    "char_spacing": 1,
    "space_width": 2,
    "glyph_file": "./fonts/four_tall.json",
})

SIX_TALL = FileFont({
    "height": 6,
    "char_spacing": 1,
    "space_width": 2,
    "baseline": 1,
    "glyph_file": "./fonts/six_tall.json",
})

ICONS = FileFont({
    "height": 7,
    "char_spacing": 1,
    "space_width": 2,
    "char_map": {
        "65": "![CLOUDY]",
        "66": "![RAIN]",
        "67": "![PARTLY_CLOUDY_DAY]",
        "68": "![CLEAR_DAY]",
        "69": "![SNOW]",
        "70": "![FOG]",
        "71": "![WIND]",
        "72": "![SLEET]",
        "73": "![PARTLY_CLOUDY_NIGHT]",
        "74": "![CLEAR_NIGHT]",
    },
    "glyph_file": "./fonts/weather_icons.json",
})
