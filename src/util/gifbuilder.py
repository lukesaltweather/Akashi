from PIL import Image

BG_COLOR = 0xF8F5F1


class ImageHelper:
    def __init__(self):
        self.image = Image.new("RGBA", (1200, 600), color=BG_COLOR)

    def add_tl(self, color=False):
        if color:
            pass
        else:
            self.image.paste(Image.open("image/tl.png"), (0, 150))

    def get_bytes(self):
        return self.image.tobytes("PNG")
