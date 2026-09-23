"""Renderer-backed procedural variation; not photorealistic habitat footage."""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

PALETTES = {
    'forest': ((127, 181, 141), (45, 91, 46)),
    'savanna': ((207, 219, 162), (184, 152, 71)),
    'mountain': ((155, 183, 210), (107, 117, 120)),
    'ocean': ((34, 136, 193), (18, 65, 123)),
    'reef': ((100, 214, 226), (54, 147, 151)),
    'kelp': ((48, 141, 154), (28, 89, 82)),
    'beach': ((121, 198, 228), (233, 207, 149)),
    'rockpool': ((105, 176, 177), (84, 117, 125)),
    'desert': ((238, 194, 137), (190, 127, 73)),
    'rocks': ((175, 171, 146), (117, 107, 100)),
    'meadow': ((152, 212, 228), (119, 170, 76)),
    'garden': ((191, 215, 197), (76, 129, 72)),
    'river': ((146, 197, 211), (83, 142, 164)),
    'snow': ((174, 204, 229), (230, 238, 245)),
    'farm': ((168, 208, 221), (150, 161, 75)),
    'indoor': ((210, 196, 174), (158, 120, 88)),
}


def motion_state(plan, seconds, progress):
    action = plan['action']
    speed = {'rest': 0, 'hover': .12, 'glide': .4, 'crawl': .6, 'slither': .7,
             'walk': .85, 'explore': .65, 'scuttle': 1.1, 'swim': 1., 'run': 1.8}[action]
    story = plan['story']
    # Piecewise integrated time: pausing does not jump/reset the gait phase.
    duration = seconds / progress if progress > 0 else 1
    if story == 'enter traverse pause':
        active = min(progress, .75)
    elif story == 'pause traverse exit':
        active = max(0, progress - .25)
    else:
        active = min(progress, .35) + max(0, progress - .65)
    t = active * duration * speed
    x = {'left third': -.18, 'center': 0, 'right third': .18}[plan['composition']]
    x += math.sin(t * .55) * .07
    if story == 'traverse pause return' and progress > .65:
        x -= (progress - .65) * .16
    return t, x


def draw_habitat(plan, seconds, size=(860, 600)):
    w, h = size
    sky, ground = PALETTES[plan['environment']]
    factor = {'daylight': 1., 'sunrise': .82, 'sunset': .63, 'moonlight': .35}[plan['lighting']]
    tint = (1., .90, .76) if plan['lighting'] in {'sunrise', 'sunset'} else (1., 1., 1.)
    def color(rgb):
        return tuple(int(c * factor * t) for c, t in zip(rgb, tint))
    image = Image.new('RGBA', size)
    draw = ImageDraw.Draw(image)
    for y in range(h):
        blend = y / h
        rgb = tuple(int(a * (1 - blend) + b * blend) for a, b in zip(sky, ground))
        draw.line((0, y, w, y), fill=color(rgb))
    horizon = int(h * .60)
    draw.rectangle((0, horizon, w, h), fill=color(ground))
    rng = random.Random(plan['seed'])
    environment = plan['environment']
    if environment in {'forest', 'garden', 'meadow', 'farm', 'kelp'}:
        for i in range(9):
            x = i * w // 8 + rng.randrange(-25, 26)
            height = rng.randrange(h // 5, h // 2)
            wind = int(math.sin(seconds + i) * 8) if plan['weather'] == 'wind' else 0
            draw.line((x, horizon + 20, x + wind, horizon - height), fill=color((77, 72, 46)), width=8)
            draw.ellipse((x - 55 + wind, horizon - height - 45, x + 55 + wind, horizon - height + 55), fill=color((42, 104 + i * 3, 58)))
    elif environment in {'mountain', 'rocks', 'snow', 'desert', 'savanna'}:
        for i in range(5):
            x = i * w // 4
            peak = rng.randrange(h // 8, h // 2)
            draw.polygon([(x - 180, horizon), (x, peak), (x + 160, horizon)], fill=color(tuple(max(0, c - 20 + i * 4) for c in ground)))
    else:
        for i in range(10):
            y = horizon + i * 23
            points = [(x, y + math.sin(x / 75 + seconds + i) * 7) for x in range(0, w + 20, 20)]
            draw.line(points, fill=color(sky), width=3)
    for i in range(7):
        x = rng.randrange(w); y = rng.randrange(horizon, h - 15)
        if plan['props'] == 'rocks':
            draw.ellipse((x, y, x + 35, y + 20), fill=color((110, 112, 103)))
        else:
            draw.line((x, y + 20, x - 10, y - 15), fill=color((40, 119, 58)), width=4)
            draw.line((x, y + 20, x + 12, y - 10), fill=color((40, 119, 58)), width=4)
    if plan['weather'] == 'cloudy':
        for x in range(0, w, 190):
            draw.ellipse((x, 30, x + 240, 100), fill=color((173, 182, 188)))
    if plan['weather'] == 'fog':
        image = Image.blend(image, Image.new('RGBA', size, (188, 200, 203, 255)), .30)
    return image
