#!/usr/bin/env python3
"""
rpi-wifi-led — control an LED on a Raspberry Pi GPIO over WiFi.

Runs a tiny web server on the Pi. Open the Pi's IP address in any browser
on your Mac/PC (on the same network) to toggle the LED and set brightness.
No internet connection is required — only a shared local network.

Wiring (default): LED on GPIO18 (BCM) = physical pin 12.
    GPIO18 ──[ 330Ω resistor ]──►|── GND
                              LED (long leg = +, toward the resistor/GPIO)

GPIO18 supports hardware PWM, which gives smooth, flicker-free brightness.
"""
import os
from flask import Flask, jsonify, request, Response

# gpiozero is the modern, recommended GPIO library on Raspberry Pi OS.
# PWMLED lets us control brightness (0.0–1.0), not just on/off.
from gpiozero import PWMLED

# BCM pin number. GPIO18 = physical pin 12. Change here if you wire elsewhere.
LED_PIN = int(os.environ.get("LED_PIN", "18"))

led = PWMLED(LED_PIN)

app = Flask(__name__)

# Effects map to gpiozero's built-in background animations. "none" = solid.
EFFECTS = ("none", "blink", "breathe", "strobe")

# In-memory state so the UI can reflect the current value after a refresh.
state = {"on": False, "brightness": 1.0, "effect": "none"}


def apply_state():
    """Push the current state object to the physical LED.

    For solid output we set led.value directly — its setter cancels any
    running blink/pulse thread. For effects we hand off to gpiozero's
    background animations (each call also stops the previous one).
    """
    if not state["on"] or state["effect"] == "none":
        led.value = state["brightness"] if state["on"] else 0.0
    elif state["effect"] == "blink":
        led.blink(on_time=0.5, off_time=0.5, background=True)
    elif state["effect"] == "strobe":
        led.blink(on_time=0.05, off_time=0.05, background=True)
    elif state["effect"] == "breathe":
        led.pulse(fade_in_time=1.0, fade_out_time=1.0, background=True)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pi WiFi LED</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, -apple-system, sans-serif; max-width: 420px;
         margin: 40px auto; padding: 0 20px; text-align: center; }
  h1 { font-size: 1.4rem; }
  .bulb { font-size: 5rem; transition: opacity .15s, filter .15s; }
  button { font-size: 1.1rem; padding: 12px 28px; border: 0; border-radius: 12px;
           cursor: pointer; background: #2d7ff9; color: #fff; }
  button.off { background: #555; }
  input[type=range] { width: 100%; margin: 24px 0 8px; }
  .row { margin: 24px 0; }
  .effects { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
  .effects button { font-size: .95rem; padding: 8px 16px; background: #e6e6e6;
                    color: #222; }
  .effects button.active { background: #2d7ff9; color: #fff; }
  small { opacity: .6; }
</style>
</head>
<body>
  <h1>Raspberry Pi WiFi LED</h1>
  <div class="bulb" id="bulb">&#128161;</div>
  <div class="row">
    <button id="toggle">Loading…</button>
  </div>
  <div class="row">
    <label for="bright">Brightness</label>
    <input type="range" id="bright" min="0" max="100" value="100">
    <div><span id="pct">100</span>%</div>
  </div>
  <div class="row effects">
    <button data-fx="none">Solid</button>
    <button data-fx="blink">Blink</button>
    <button data-fx="breathe">Breathe</button>
    <button data-fx="strobe">Strobe</button>
  </div>
  <small>GPIO pin (BCM): __LED_PIN__</small>
<script>
const bulb = document.getElementById('bulb');
const toggle = document.getElementById('toggle');
const bright = document.getElementById('bright');
const pct = document.getElementById('pct');
const fxButtons = document.querySelectorAll('.effects button');

function render(s) {
  toggle.textContent = s.on ? 'Turn OFF' : 'Turn ON';
  toggle.className = s.on ? '' : 'off';
  bright.value = Math.round(s.brightness * 100);
  pct.textContent = bright.value;
  bulb.style.opacity = s.on ? (0.25 + 0.75 * s.brightness) : 0.15;
  bulb.style.filter = s.on ? 'none' : 'grayscale(1)';
  // Brightness only applies to solid mode; dim the slider during effects.
  const solid = (s.effect || 'none') === 'none';
  bright.disabled = !solid;
  fxButtons.forEach(b => b.classList.toggle(
    'active', s.on && b.dataset.fx === (s.effect || 'none')));
}

async function send(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined
  });
  render(await r.json());
}

toggle.onclick = () => send('/toggle');
bright.oninput = () => { pct.textContent = bright.value; };
bright.onchange = () => send('/brightness', {value: bright.value / 100});
fxButtons.forEach(b => b.onclick = () => send('/effect', {name: b.dataset.fx}));

// Load initial state.
fetch('/state').then(r => r.json()).then(render);
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return Response(PAGE.replace("__LED_PIN__", str(LED_PIN)), mimetype="text/html")


@app.route("/state")
def get_state():
    return jsonify(state)


@app.route("/toggle", methods=["POST"])
def toggle():
    state["on"] = not state["on"]
    state["effect"] = "none"
    apply_state()
    return jsonify(state)


@app.route("/on", methods=["POST"])
def on():
    state["on"] = True
    state["effect"] = "none"
    apply_state()
    return jsonify(state)


@app.route("/off", methods=["POST"])
def off():
    state["on"] = False
    state["effect"] = "none"
    apply_state()
    return jsonify(state)


@app.route("/brightness", methods=["POST"])
def brightness():
    data = request.get_json(silent=True) or {}
    try:
        value = float(data.get("value"))
    except (TypeError, ValueError):
        return jsonify({"error": "value must be a number 0.0–1.0"}), 400
    state["brightness"] = max(0.0, min(1.0, value))
    # Adjusting brightness implies solid output and the light on.
    state["effect"] = "none"
    if state["brightness"] > 0:
        state["on"] = True
    apply_state()
    return jsonify(state)


@app.route("/effect", methods=["POST"])
def effect():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if name not in EFFECTS:
        return jsonify({"error": "name must be one of %s" % (EFFECTS,)}), 400
    state["effect"] = name
    # Selecting any effect (including 'none'/solid) turns the LED on.
    state["on"] = True
    apply_state()
    return jsonify(state)


if __name__ == "__main__":
    # host=0.0.0.0 makes the server reachable from other devices on the
    # network (your Mac/PC), not just localhost on the Pi itself.
    apply_state()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
