# MM AFK LEVELER(Template + OCR)

A lightweight Python automation script for browser games and UI flows that clicks
on-screen buttons such as **Continue**, **Play**, **Drop**, **Claim**, and **Open**.

The bot uses:
- **Template matching (OpenCV)** as the primary method (fast & reliable)
- **OCR fallback (EasyOCR)** when templates fail (font/size changes)

No GPU, no Paddle, no virtual environment required.

---

## Features

- Template-first detection (fast)
- OCR fallback for dynamic text
- Supports overlay popups
- Priority-based clicking
- Hotkey-controlled (start / pause / exit)
- Works with browser games
- Uses fixed or selectable screen regions (ROIs)

---

## Requirements

- Python **3.9+**
- Windows (tested)
- Display scaling set to **100%**

---

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
