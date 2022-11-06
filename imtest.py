from PIL import Image, ImageDraw, ImageFont

image = Image.new("RGBA", (800, 600), (255, 255, 255, 0))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("Chewy-Regular.ttf", 40)

draw.rounded_rectangle(((70, 50), (730, 550)), 10, fill=(30, 30, 30, 255))
draw.text(
    (100, 75),
    "Yankee-kun {}".format(2),
    fill=(255, 255, 255, 255),
    font=font,
)

draw.ellipse((400, 300), 0, outline=(19, 16, 120, 100), width=10)

image.show()
