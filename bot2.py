import cv2
import numpy as np
import mss
import pyautogui
import time
import os
from pynput import keyboard
import easyocr

pyautogui.FAILSAFE = True  # move mouse to top-left to abort

# ===================== SETTINGS =====================
RUNNING = False
LOOP_SLEEP = 0.02
TEMPLATE_THRESH = 0.75
OCR_CONF_MIN = 0.40

# ===================== SAVED ROIS (YOUR BEST COORDS) =====================
ROI = {
    "overlay": (501, 390, 1120, 848),
    "claim_open": (551, 380, 1049, 821),
    "main": (456, 666, 1040, 850),
}

# priority order
PRIORITY = [
    ("overlay", ["continue"]),
    ("claim_open", ["claim", "open"]),
    ("main", ["continue", "play", "drop"]),
]

BUTTONS = ["continue", "play", "drop", "claim", "open"]

# ===================== PATHS =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# ===================== LOAD TEMPLATES =====================
TEMPLATES = {}
for name in BUTTONS:
    path = os.path.join(TEMPLATE_DIR, f"{name}.png")
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            TEMPLATES[name] = img

print("Loaded templates:", list(TEMPLATES.keys()))
print("ROIs loaded:", ROI)

# ===================== OCR (FALLBACK) =====================
reader = easyocr.Reader(["en"], gpu=False)

def ocr_find(gray, wanted_words):
    results = reader.readtext(gray, detail=1, paragraph=False)
    for box, text, conf in results:
        if conf < OCR_CONF_MIN:
            continue
        txt = text.lower().replace(" ", "")
        for w in wanted_words:
            if w in txt:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                cx = int(sum(xs) / len(xs))
                cy = int(sum(ys) / len(ys))
                return cx, cy
    return None

# ===================== HOTKEYS =====================
# You can still re-pick ROIs if you ever need to:
# F6 overlay, F7 claim/open, F8 main, then pick corners with F2 twice.

picking = None
points = []

def on_key(key):
    global RUNNING, picking, points
    try:
        if key == keyboard.Key.f9:
            RUNNING = True
            print("RUNNING")
        elif key == keyboard.Key.f10:
            RUNNING = False
            print("PAUSED")
        elif key == keyboard.Key.esc:
            print("EXIT")
            os._exit(0)

        elif key == keyboard.Key.f6:
            picking = "overlay"; points = []; print("Pick OVERLAY ROI (F2 top-left, F2 bottom-right)")
        elif key == keyboard.Key.f7:
            picking = "claim_open"; points = []; print("Pick CLAIM/OPEN ROI (F2 top-left, F2 bottom-right)")
        elif key == keyboard.Key.f8:
            picking = "main"; points = []; print("Pick MAIN ROI (F2 top-left, F2 bottom-right)")

        elif key == keyboard.Key.f2 and picking:
            points.append(pyautogui.position())
            if len(points) == 2:
                (x1, y1), (x2, y2) = points
                ROI[picking] = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                print(picking, "ROI =", ROI[picking])
                picking = None
                points = []

    except:
        pass

keyboard.Listener(on_press=on_key).start()

# ===================== MAIN LOOP =====================
with mss.mss() as sct:
    while True:
        if RUNNING and all(ROI.values()):
            for region, targets in PRIORITY:
                x1, y1, x2, y2 = ROI[region]

                img = np.array(
                    sct.grab({
                        "left": x1,
                        "top": y1,
                        "width": x2 - x1,
                        "height": y2 - y1
                    })
                )

                gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

                # ---- TEMPLATE FIRST (SAFE: never crash if ROI smaller) ----
                matched = False
                for name in targets:
                    tpl = TEMPLATES.get(name)
                    if tpl is None:
                        continue

                    h_img, w_img = gray.shape[:2]
                    h_tpl, w_tpl = tpl.shape[:2]
                    if h_tpl > h_img or w_tpl > w_img:
                        continue  # ROI too small for this template

                    res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
                    _, score, _, loc = cv2.minMaxLoc(res)

                    if score >= TEMPLATE_THRESH:
                        cx = loc[0] + w_tpl // 2
                        cy = loc[1] + h_tpl // 2
                        pyautogui.click(x1 + cx, y1 + cy)
                        time.sleep(0.05)
                        matched = True
                        break

                if matched:
                    break

                # ---- OCR FALLBACK ----
                ocr_hit = ocr_find(gray, targets)
                if ocr_hit:
                    cx, cy = ocr_hit
                    pyautogui.click(x1 + cx, y1 + cy)
                    time.sleep(0.05)
                    break

        time.sleep(LOOP_SLEEP)
