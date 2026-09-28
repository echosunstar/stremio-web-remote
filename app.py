import os
import subprocess
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort

load_dotenv()

app = Flask(__name__)

# X11 Display
os.environ["DISPLAY"] = os.getenv("DISPLAY", ":0")

# Whitelist allowed keys for safety
SAFE_KEYS = {
    'space', 'Left', 'Right', 'Up', 'Down', 
    'f', 'm', 'Escape', 'Return', 'BackSpace', 'Tab'
}


def run_xdotool(*args):
    return subprocess.run(["xdotool", *args], check=False)


def run_stremio_or_fallback(key: str):
    res = subprocess.run(
        ["xdotool", "search", "--onlyvisible", "--class", "stremio", "windowactivate", "--sync", "key", key],
        check=False
    )
    if res.returncode != 0:
        run_xdotool("key", key)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mouse")
def mouse_move():
    try:
        dx = int(request.args.get("dx", 0))
        dy = int(request.args.get("dy", 0))
    except ValueError:
        abort(400)

    run_xdotool("mousemove_relative", "--", str(dx), str(dy))
    return ("", 204)


@app.route("/type", methods=["POST"])
def type_text():
    text = request.form.get("text", "")
    if text:
        run_xdotool("type", "--clearmodifiers", "--delay", "10", text)
    return ("", 204)


@app.route("/key")
def press_key():
    key = request.args.get("k", "")
    repeat_str = request.args.get("repeat", "1")
    
    try:
        repeat = max(1, min(int(repeat_str), 100))  # Sanitize bounds
    except ValueError:
        abort(400)

    # Mouse clicks
    if key in ["click 1", "click 3"]:
        btn = key.split()[1]
        run_xdotool("click", btn)

    # System controls
    elif key == "lock":
        res = subprocess.run(["xdotool", "key", "ctrl+alt+l"], check=False)
        if res.returncode != 0:
            subprocess.run(["xdotool", "key", "super+l"], check=False)

    elif key == "wake":
        run_xdotool("mousemove_relative", "1", "1")
        run_xdotool("mousemove_relative", "--", "-1", "-1")

    # App controls
    elif key == "focus":
        run_xdotool("search", "--onlyvisible", "--class", "stremio", "windowactivate")

    elif key == "restart":
        res = subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "stremio", "windowactivate", "--sync", "key", "0"],
            check=False
        )
        if res.returncode != 0:
            run_xdotool("key", "Home")

    elif key == "next_episode":
        run_stremio_or_fallback("shift+n")

    elif key == "long_back":
        subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "stremio", "windowactivate", "--sync", "key", "--repeat", "3", "--delay", "30", "Left"],
            check=False
        )

    elif key == "long_forward":
        subprocess.run(
            ["xdotool", "search", "--onlyvisible", "--class", "stremio", "windowactivate", "--sync", "key", "--repeat", "3", "--delay", "30", "Right"],
            check=False
        )

    elif key == "BackSpace" and repeat > 1:
        run_xdotool("key", "--repeat", str(repeat), "BackSpace")

    elif key in ["Return", "BackSpace", "Tab"]:
        run_xdotool("key", key)

    elif key in SAFE_KEYS:
        run_stremio_or_fallback(key)

    return ("", 204)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8282))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    app.run(host=host, port=port, debug=debug)