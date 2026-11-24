#!/usr/bin/env python3
"""News image - Tuesday 24 November 2026, v1 morning.

Pure stdlib (struct/zlib), deterministic 1024x1024 PNG. No PIL, no network,
no timestamps, no randomness: same input -> byte-identical output.
Facts come only from NEWS_24NOV.md (55 stories, cutoff 07:15 WIB).

Hierarchy fix for this edition: the pure-[24 Nov] stories are raised
(Zelensky new-strikes warning + Moscow/Estonia as Medium 1-2, Megaspeed /
Armenia / Zaporizhzhia / Denmark / South Korea / Beijing / Huang hearing /
Huang returns / Kenya-DR Congo / Bangladesh first in Also Today, all tagged
[24 NOV]). No [23 Nov] story is relabelled as 24 Nov. No MNF or Champions
League result is claimed. Oil is "down sharply" with no exact figure.
Markets are labelled "Monday 23 Nov close".

Usage: python3 main.py [output.png]   (default: entry.png beside this file)
"""

import hashlib
import os
import struct
import sys
import zlib

W = 1024
H = 1024

BLACK = (20, 20, 20)
RED = (165, 0, 0)
GREY = (90, 90, 90)
LIGHT_RED = (255, 232, 232)
LIGHT_GREY = (242, 242, 242)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows, 5 bits each (bit 4 = leftmost pixel).
FONT = {
    ' ': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '$': (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    '%': (0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x03),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '*': (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
    '+': (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
    ',': (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    '-': (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    '.': (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    '/': (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ':': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ';': (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    '<': (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    '=': (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
    '>': (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    '@': (0x0E, 0x11, 0x01, 0x0D, 0x15, 0x15, 0x0E),
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x01, 0x01, 0x01, 0x01, 0x01, 0x11, 0x0E),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '[': (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    '\\': (0x10, 0x08, 0x08, 0x04, 0x02, 0x02, 0x01),
    ']': (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    '^': (0x04, 0x0A, 0x11, 0x00, 0x00, 0x00, 0x00),
    '_': (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
    '`': (0x04, 0x04, 0x02, 0x00, 0x00, 0x00, 0x00),
    'a': (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    'b': (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    'c': (0x00, 0x00, 0x0E, 0x11, 0x10, 0x11, 0x0E),
    'd': (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    'e': (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    'f': (0x06, 0x08, 0x1E, 0x08, 0x08, 0x08, 0x08),
    'g': (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'h': (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    'i': (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    'j': (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    'k': (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    'l': (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'm': (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    'n': (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    'o': (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    'p': (0x00, 0x00, 0x1E, 0x11, 0x11, 0x1E, 0x10),
    'q': (0x00, 0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01),
    'r': (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    's': (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    't': (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    'u': (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    'v': (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'w': (0x00, 0x00, 0x11, 0x15, 0x15, 0x15, 0x0A),
    'x': (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    'y': (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    'z': (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    '{': (0x02, 0x04, 0x04, 0x08, 0x04, 0x04, 0x02),
    '|': (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    '}': (0x08, 0x04, 0x04, 0x02, 0x04, 0x04, 0x08),
    '~': (0x00, 0x00, 0x00, 0x0E, 0x15, 0x00, 0x00),
}

# ---------------------------------------------------------------- content
# All facts from NEWS_24NOV.md only. [24 Nov] items are raised to the top
# of their sections; nothing dated [23 Nov] is relabelled.

LEADS = [
    ("NVIDIA ROARS BACK AS HUANG IS REINSTATED",
     "Nvidia board reinstates Jensen Huang as CEO, 11 days after he quit "
     "over affairs including one with an alleged Chinese spy. "
     "NVDA +31.5%, best day since 2003."),
    ("NATO SENDS AWACS TO POLAND AFTER RUSSIAN MISSILES LAND ON ITS SOIL",
     "NATO authorises a forward AWACS deployment after three Russian Kh-101 "
     "missiles crashed in SE Poland on Friday. No casualties; Poland "
     "did not invoke Article 4."),
    ("IRAN VOWS 'ALL AVAILABLE MEANS' AGAINST US NAVAL BLOCKADE",
     "Tehran vows to use all its tools against the US naval blockade, a day "
     "after Trump threatened to sink Iranian ships. US sanctions hit "
     "'shadow banking'."),
]

# [24 Nov] mediums first (raised), then the [23 Nov] mediums in order.
MEDIUM = [
    "[24 NOV] ZELENSKY: INTEL SHOWS RUSSIA PLANNING NEW STRIKES ON UKRAINE",
    "[24 NOV] MOSCOW ACCUSES ESTONIA OF ACTS 'ON VERGE OF OPEN WAR'",
    "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA - corvette Merkury sunk 22 Nov",
    "IRAN FLOGS SINGER PARASTOO AHMADI - 74 lashes for concert without hijab",
    "GAZA A 'TOXIC WASTELAND' - contamination across over 99% of Gaza",
    "BURNHAM DEFENDS EU DEAL - claims +0.5% GDP, GBP 17bn a year",
    "INDIA PLEDGES $1.62BN TO FLOOD-HIT NEPAL - $377m grant, $1.24bn credit",
    "INDONESIA FACTORY FIRE: 24 DEAD, ABOUT 30 MISSING in Cikande, Banten",
    "O'HARE GROUND STOP AT THANKSGIVING RUSH - 170+ flights delayed",
    "TRUMP BLASTS NEWSOM AT DOJ OVER 548 DEATH SENTENCES",
    "US SANCTIONS DOZENS OVER IRAN 'SHADOW BANKING' NETWORKS",
    "ISRAELI STRIKES KILL AT LEAST 3 IN GAZA, INCL. UNRWA WORKER",
]

# [24 Nov] items first (raised), then [23 Nov] items in original order.
ALSO = [
    "[24 NOV] US to blacklist Megaspeed chip firm in Nvidia scandal",
    "[24 NOV] Armenia proposes new constitution, step to peace with Azerbaijan",
    "[24 NOV] Russian attacks hit Zaporizhzhia medical facility, kill three",
    "[24 NOV] Denmark to propose mobile-phone ban in schools in 2027",
    "[24 NOV] South Korea picks new foreign minister, intel chief",
    "[24 NOV] Beijing limits drone-component sales used by Russia",
    "[24 NOV] Senate panel schedules Huang hearing for 3 December",
    "[24 NOV] Jensen Huang returns to Nvidia HQ amid applause",
    "[24 NOV] Kenya and DR Congo agree to renew ties after row",
    "[24 NOV] Bangladesh court seeks social-media curbs for under-16s",
    "Germany, Ukraine sign deal for Bundeswehr to use Kyiv's Delta system",
    "Trump orders Army to pause detonation of toxic stockpile in Iowa",
    "France condemns 'highly concerning' settler attacks in West Bank",
    "Israel defence minister: police, not army, must handle settler violence",
    "Eisenkot calls settler arson 'Jewish terrorism'; coalition talks fail",
    "WHO chief: fighting near Congo Ebola area disrupts response",
    "UK sanctions top Myanmar military leaders after ICJ genocide ruling",
    "Trump says he spoke to Nvidia's board 'directly and indirectly'",
    "Trump hosts third crypto gala for meme-coin investors",
    "Appeals court hands Trump way out of hush-money conviction",
    "Rep. Jimmy Gomez to resign after ethics panel misconduct finding",
    "US deported a US citizen to Mexico, DoJ admits in court",
    "Video of ICE detaining father and daughter sparks Seattle protests",
    "Virginia reports first measles-linked death of 2026, a child under 5",
    "Aber Kawas, first Palestinian in New York state Senate, wins 74.5%",
    "Democrats hold at least 258 House seats, most since 1992",
    "Democrats reveal details for 2028 presidential primary",
    "Drone attacks kill four near Sudan's capital, damage UN building",
    "Boat carrying mourners capsizes in Nigeria, at least 24 killed",
    "Fire tears through six hotels, dozens of shops in Nungwi, Zanzibar",
    "M6.5 deep quake in Vanuatu region, 601 km deep; no tsunami threat",
    "Lahore tops global pollution ranking again as AQI crosses 500",
    "Gas prices in Europe surge as cold snap feeds shortage fears",
    "NHS launches world's largest AI breast-cancer screening trial",
    "Capita shares plunge 70% as boss quits after pensions failure",
    "Andrew received GBP 750,000 from Turkish millionaire, court told",
    "Tyson Fury reveals schizophrenia diagnosis",
    "Miley Cyrus marries Maxx Morando in California ceremony",
    "Court bans China's BYD from selling 'Defender clone' SUV in EU",
    "UK confirmed as host of 2035 Women's World Cup; US co-host 2031",
]

MARKETS = [
    "S&P 500 7,237.17 (+4.73%)   Dow 49,595.31 (+3.01%)   Nasdaq 24,089.56 (+6.51%)",
    "Russell 2000 2,669.66 (+3.4%)   Nvidia +31.5%, best day since 2003",
    "Bitcoin ~$63,900   Gold ~$3,666/oz   Oil down sharply   Sensex -1.77% to 82,435",
]

STRIP = "NEW THIS MORNING: Zelensky warns of new strikes - Moscow accuses Estonia"

# ---------------------------------------------------------------- canvas
PIX = bytearray([255]) * (W * H * 3)


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i], PIX[i + 1], PIX[i + 2] = color


def rect(x, y, w, h, color):
    for yy in range(y, y + h):
        base = (yy * W + x) * 3
        for xx in range(w):
            i = base + xx * 3
            PIX[i], PIX[i + 1], PIX[i + 2] = color


def hline(x, y, w, color, thick=1):
    rect(x, y, w, thick, color)


def draw_char(x, y, ch, scale, color, bold=False):
    glyph = FONT.get(ch)
    if glyph is None:
        raise ValueError("no glyph for %r" % ch)
    passes = (0, 1) if bold else (0,)
    for dx in passes:
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    bx = x + dx + col * scale
                    by = y + row * scale
                    for sy in range(scale):
                        for sx in range(scale):
                            px(bx + sx, by + sy, color)


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(x, y, s, scale, color, bold=False):
    cx = x
    for ch in s:
        draw_char(cx, y, ch, scale, color, bold)
        cx += 6 * scale
    return cx


def wrap(s, width_chars):
    """Word-wrap to lines of at most width_chars characters."""
    lines, cur = [], ""
    for word in s.split(" "):
        if cur and len(cur) + 1 + len(word) > width_chars:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word) if cur else word
    if cur:
        lines.append(cur)
    return lines


def section_label(y, text):
    draw_text(24, y, text, 2, BLACK, bold=True)
    rect(24, y + 19, 64, 3, RED)
    return y + 24


def tag_red(x, y, s, scale, bold=True):
    """Redraw a leading '[24 NOV]' tag in red over the black text."""
    if s.startswith("[24 NOV]"):
        draw_text(x, y, "[24 NOV]", scale, RED, bold=bold)


# ---------------------------------------------------------------- layout
def build():
    assert len(LEADS) == 3, len(LEADS)
    assert len(MEDIUM) == 12, len(MEDIUM)
    assert len(ALSO) == 40, len(ALSO)

    # Header
    draw_text(24, 14, "THE WORLD IN ONE PAGE", 3, BLACK, bold=True)
    right = "55 STORIES"
    draw_text(W - 24 - text_w(right, 2), 18, right, 2, GREY, bold=True)
    draw_text(24, 44, "Tuesday 24 November 2026", 4, RED, bold=True)
    hline(24, 84, W - 48, BLACK, 2)

    # New-this-morning strip (pure [24 Nov] stories, raised)
    rect(24, 92, W - 48, 30, LIGHT_RED)
    draw_text(34, 99, STRIP, 2, RED, bold=True)

    # Leads
    y = section_label(132, "TOP STORIES")
    y += 6
    for head, summ in LEADS:
        draw_text(24, y, head, 2, BLACK, bold=True)
        y += 18
        for line in wrap(summ, 80):
            draw_text(24, y, line, 2, BLACK)
            y += 18
        y += 8
    leads_end = y

    hline(24, leads_end + 2, W - 48, BLACK, 1)

    # Medium (one legible scale-2 line each; [24 Nov] first, red tag)
    y = section_label(leads_end + 12, "MORE NEWS")
    y += 4
    for item in MEDIUM:
        draw_text(24, y, item, 2, BLACK, bold=True)
        tag_red(24, y, item, 2)
        y += 18
    medium_end = y

    hline(24, medium_end + 2, W - 48, BLACK, 1)

    # Also Today: 2 columns x 20 rows, scale-1 bold (legible, not packed);
    # [24 Nov] items fill the top of the left column, red tag.
    y = section_label(medium_end + 12, "ALSO TODAY")
    y += 4
    top = y
    for i, item in enumerate(ALSO):
        col = 0 if i < 20 else 1
        row = i % 20
        x = 24 if col == 0 else 524
        ry = top + row * 12
        draw_text(x, ry, item, 1, BLACK, bold=True)
        tag_red(x, ry, item, 1)
    also_end = top + 20 * 12

    # Markets (Monday 23 Nov close - labelled, never 24 Nov)
    box_y = also_end + 10
    rect(24, box_y, W - 48, 100, LIGHT_GREY)
    draw_text(34, box_y + 8, "MARKETS - ", 2, BLACK, bold=True)
    mx = 34 + text_w("MARKETS - ", 2)
    draw_text(mx, box_y + 8, "Monday 23 Nov close", 2, RED, bold=True)
    my = box_y + 30
    for line in MARKETS:
        draw_text(34, my, line, 2, BLACK)
        my += 18
    draw_text(34, box_y + 88,
              "Sources: Reuters, AP, BBC, CNN, Al Jazeera, AFP, Guardian, "
              "Oxfam/CEOBS, USGS, FAA. v1 morning - cutoff 07:15 WIB.",
              1, GREY)
    end = box_y + 100
    assert end <= H, "layout overflow: %d > %d" % (end, H)
    return {"leads_end": leads_end, "medium_end": medium_end,
            "also_end": also_end, "end": end}


# ---------------------------------------------------------------- PNG out
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = b"".join(b"\x00" + bytes(PIX[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(raw, 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png), hashlib.sha256(png).hexdigest()


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "entry.png")
    info = build()
    size, sha = write_png(out)
    print("wrote %s (%d bytes, sha256 %s)" % (out, size, sha))
    print("layout: leads_end=%d medium_end=%d also_end=%d end=%d / %d"
          % (info["leads_end"], info["medium_end"], info["also_end"],
             info["end"], H))
    print("stories: 3 lead + 12 medium + 40 also today = 55")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
