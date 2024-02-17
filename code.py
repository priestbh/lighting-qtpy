# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import secrets
import ipaddress
import microcontroller
import os
import wifi
import socketpool
import time
import json
import rtc
import board
import touchio
import adafruit_ntp
import neopixel
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.color import BLUE
from adafruit_httpserver.mime_type import MIMEType
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.server import HTTPServer

# json headers for webserver response
JSON_HEADERS = '''\
HTTP/1.1 200 OK
Content-Type: application/json

'''

print("list: ", os.listdir("/patterns"))
# for on onboard neopixel
# pixel_pin = board.NEOPIXEL
# num_pixels = 1
# ORDER = neopixel.GRB

# for neopixel strip
pixel_pin = board.A0
num_pixels = 44
#num_pixels = 229
# 229 max for living room strip
ORDER = neopixel.GRB

touch_pad = board.A2
touch = touchio.TouchIn(touch_pad)
touch.threshold = 60000
TOUCH_ON_DURATION = 0.25
LAST_TOUCH_TIME = -1
touchCycleCount = 0


pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.8, auto_write=False, pixel_order=ORDER
)

class myColor:
  def __init__(self, r, g, b):
    self.r = r
    self.g = g
    self.b = b

last = myColor(0, 0, 0)
BGcolor = myColor(0, 0, 0)
FGcolor = myColor(0, 0, 255)


comet = Comet(pixels, speed=0.01, color=(0,255,255), tail_length=10, bounce=True)
cometActive = False


sparkle = Sparkle(pixels, speed=0.05, color=(0,255,255), num_sparkles=10)
sparkleActive = False


# print("ESP32-S2 WebClient Test")

print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

# print("Available WiFi networks:")
# for network in wifi.radio.start_scanning_networks():
#    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
#            network.rssi, network.channel))
# wifi.radio.stop_scanning_networks()


ssid, password = secrets.WIFI_SSID, secrets.WIFI_PASSWORD  # pylint: disable=no-member

print("Connecting to", ssid)
wifi.radio.connect(ssid, password)
print("Connected to", ssid)
print("My IP address is", wifi.radio.ipv4_address)

# ipv4 = ipaddress.ip_address("8.8.4.4")
# print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))

pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)
try:
    ntp = adafruit_ntp.NTP(pool, tz_offset=0)
    rtc.RTC().datetime = ntp.datetime
except OSError as err:
    print("OS error:", err)
print (time.localtime())

#  font for HTML
font_family = "monospace"

#  the HTML script
#  setup as an f string
#  this way, can insert string variables from code.py directly
#  of note, use {{ and }} if something from html *actually* needs to be in brackets
#  i.e. CSS style formatting
def webpage():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    html{{font-family: {font_family}; background-color: darkgrey;
    display:inline-block; margin: 0px auto; text-align: center;}}
      h1{{color: cyan; width: 200; word-wrap: break-word;
            padding: 2vh; font-size: 35px;}}
      p{{font-size: 1.5rem; width: 200; word-wrap: break-word;}}
      .button{{font-family: {font_family};display: inline-block;
      background-color: black; border: none;
      border-radius: 4px; color: white; padding: 16px 40px;
      text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}}
      p.dotted {{margin: auto;
      width: 75%; font-size: 25px; text-align: center;}}
      table.center {{ margin-left: auto;margin-right: auto; }}

    </style>

    <script src="huewheel.min.js"></script>
	<script src="underscore-min.js"></script>

    </head>
    <body>
    <title>Living Room Lights</title>
    <h1>Living Room</h1>
    <br>
    <p id="demo"></p>
    <script>
        var w = window.innerWidth;
        var h = window.innerHeight;

        var x = document.getElementById("demo");
        x.innerHTML = "Browser width: " + w + ", height: " + h + ".";
    </script>

	<div id="container" style="width:400px; margin:50px auto 0 auto;">
		<div id="huewheel"></div>
		<br>
		<div id="info"> info </div>
		<br>
	</div>

    <script type="text/javascript">
	var throttleSetColor = _.throttle(setColor, 400);

    	hw = new HueWheel('huewheel', {{
		onChange:  _.after(2,throttleSetColor),
		saturation:  1.0,
		lightness:  0.5,
		colorSpace:  'hsl',
		diameter:  400,
		shadowBlur:  7,
		changeSaturation:  false,
		changeLightness:  true,
		showColor:  true,
		colorSpotWidth:  0.7,
		colorSpotBorder:  1,
		colorSpotBorderColor:  '#333',
		quality:  2,
		hueKnobSize:  0.12,
		hueKnobColor:  '#ffc',
		lightKnobColor:  '#ff0',
		hueKnobColorSelected:  '#fff',
		hueKnobShadow:  true,
		lightnessKnobColorSelected:  '#f00',
		lightnessRingClickable:  true,
		useKeys:  true,
		hueKeyDelta:  2,
		saturationKeyDelta:  1,
		lightnessKeyDelta:  1,
		shiftKeyFactor:  10
	}});
    function setColor(e,jsonType = 'all') {{

		document.getElementById('info').innerHTML = 'R:' + ('000' + e.r).substr(-3) +
			'   G:' + ('000' + e.g).substr(-3) +
			'   B:' + ('000' + e.b).substr(-3);
        var redSlider = document.getElementById("RED_VALUE");
        var greenSlider = document.getElementById("GREEN_VALUE");
        var blueSlider = document.getElementById("BLUE_VALUE");
        redSlider.value = e.r;
        redSlider.innerHTML = e.r;
        greenSlider.value = e.g;
        greenSlider.innerHTML = e.g;
        blueSlider.value = e.b;
        blueSlider.innerHTML = e.b;

		var colorJSON = '{{"' + jsonType + '":"' + e.r + ',' + e.g + ',' + e.b + '"}}';
		var xhttp = new XMLHttpRequest();
		xhttp.open('POST', 'http://' + window.location.hostname + '/json/', true);
		xhttp.setRequestHeader('Content-type', 'application/json');
		xhttp.send(colorJSON);
	}}
    function sendSliders(jsonType) {{
        var redSliderValue = document.getElementById("RED_VALUE").value;
        var greenSliderValue = document.getElementById("GREEN_VALUE").value;
        var blueSliderValue = document.getElementById("BLUE_VALUE").value;
        var myE = {{r:redSliderValue, g:greenSliderValue, b:blueSliderValue}}

        setColor(myE,jsonType);
		document.getElementById('info').innerHTML = 'R:' + ('000' + redSliderValue).substr(-3) +
			'   G:' + ('000' + greenSliderValue).substr(-3) +
			'   B:' + ('000' + blueSliderValue).substr(-3);
	}}

    </script>
    <form accept-charset="utf-8" method="POST" oninput="RED_OUT.value=parseInt(RED_VALUE.value);GREEN_OUT.value=parseInt(GREEN_VALUE.value);BLUE_OUT.value=parseInt(BLUE_VALUE.value)" >
    <table class="center">
    <tr>
    <td><label>Red:</label></td>
    <td><input type="range" min=0 max=255 id="RED_VALUE" name="RED_VALUE" value="{last.r}" /></td>
    <td><output name="RED_OUT" for="RED_VALUE" > </output><td>
    </tr>
    <tr>
    <td><label>Green:</label></td>
    <td><input type="range" min=0 max=255 id="GREEN_VALUE" name="GREEN_VALUE" value="{last.g}" /></td>
    <td><output name="GREEN_OUT" for="GREEN_VALUE" > </output></td>
    </tr>
    <tr>
    <td><label>Blue:</label></td>
    <td><input type="range" min=0 max=255 id="BLUE_VALUE" name="BLUE_VALUE"value="{last.b}" /></td>
    <td><output name="BLUE_OUT" for="BLUE_VALUE" > </output></td>
    </tr>
    <tr>
    <td><button class="button" name="FG" value="ON" type="button" onclick="sendSliders('fg')">Set Foreground</button></td>
    <td><button class="button" name="LED ON" value="ON" type="button" onclick="sendSliders('all')">LED ON</button></td>
    <td><button class="button" name="BG" value="ON" type="button" onclick="sendSliders('bg')">Set Background</button></td>
    </tr>
    </table>
    </p>
    </p></form>

    <p><form accept-charset="utf-8" method="POST" oninput="SPEED_OUT.value=parseInt(SPEED_VALUE.value)/40">
    <table class="center">
    <tr>
    <td><label>speed:</label></td>
    <td><input type="range" min=1 max=100 name="SPEED_VALUE" value="1" /></td>
    <td><output name="SPEED_OUT" for="SPEED_VALUE" > </output><td>
    </tr>
    </table>
    <p><button class="button" name="NorthernLights" value="ON" type="submit">Northern Lights</button></p>
    <p><button class="button" name="Comet" value="ON" type="submit">Comet</button>
       <button class="button" name="Sparkle" value="ON" type="submit">Sparkle</button></p>
    </form>
    <p><form accept-charset="utf-8" method="POST">
    <button class="button" name="LED OFF" value="OFF" type="submit">LED OFF</button></p></form>
    </body></html>
    """
    return html



#  route default static IP
@server.route("/")
def base(request):  # pylint: disable=unused-argument
    #  serve the HTML f string
    #  with content type text/html
    response = HTTPResponse(request)
    with response:
        response.send(content_type="text/html", body=webpage())


#  if a button is pressed on the site
@server.route("/", "POST")
def buttonpress(request):
    global last
    global BGcolor
    global FGcolor
    global comet
    global cometActive
    global sparkle
    global sparkleActive

    #  get the raw text

    raw_text = request.body.decode("utf8")
    print(raw_text)
    formData = raw_text.split("&")
    print(formData)
    for formColor in formData:
        formColorPair = formColor.split("=")
        print(formColorPair)

    #  if the led on button was pressed
    if "LED+ON=ON" in raw_text:
        formData = raw_text.split("&")
        print(formData)
        for formColor in formData:
            formColorPair = formColor.split("=")
            print(formColorPair)
            if formColorPair[0] == "RED_VALUE":
                red = int(formColorPair[1])
            elif formColorPair[0] == "GREEN_VALUE":
                green = int(formColorPair[1])
            elif formColorPair[0] == "BLUE_VALUE":
                blue = int(formColorPair[1])
        #  turn on the onboard LED
        pixels.fill((red, green, blue))
        pixels.show()
        last.r = red
        last.g = green
        last.b = blue

    if "NorthernLights=ON" in raw_text:
        formData = raw_text.split("&")
        print(formData)
        for formItem in formData:
            formItemPair = formItem.split("=")
            print(formItemPair)
            if formItemPair[0] == "SPEED_VALUE":
                formSpeed = float(int(formItemPair[1])/40)
        comet = Comet(pixels, speed=formSpeed, color=(0,255,255), background_color=(127,0,255), tail_length=15, bounce=True)
        cometActive = True
    if "Comet=ON" in raw_text:
        formData = raw_text.split("&")
        print(formData)
        for formItem in formData:
            formItemPair = formItem.split("=")
            print(formItemPair)
            if formItemPair[0] == "SPEED_VALUE":
                formSpeed = float(int(formItemPair[1])/40)
        comet = Comet(pixels, speed=formSpeed, color=(FGcolor.r,FGcolor.g,FGcolor.b), background_color=(BGcolor.r,BGcolor.g,BGcolor.b), tail_length=15, bounce=True)
        cometActive = True
    if "Sparkle=ON" in raw_text:
        formData = raw_text.split("&")
        print(formData)
        for formItem in formData:
            formItemPair = formItem.split("=")
            print(formItemPair)
            if formItemPair[0] == "SPEED_VALUE":
                formSpeed = float(int(formItemPair[1])/40)
        sparkle = Sparkle(pixels, speed=formSpeed, color=(FGcolor.r,FGcolor.g,FGcolor.b), )
        sparkleActive = True
    if "LED+OFF=OFF" in raw_text:
        #  turn the onboard LED off
        turnOff()
    #  reload site
    response = HTTPResponse(request)
    with response:
        response.send(content_type="text/html", body=webpage())



@server.route("/json/", "POST")
def processJson(request):
    global last
    global BGcolor
    global FGcolor

    jsonResponse='{"success": true}'

    raw_text = request.body.decode("utf8")
    print(raw_text)
    response = HTTPResponse(request)
    try:
        tmpJSON = json.loads(raw_text)
#        print(tmpJSON)
        if 'bg' in tmpJSON:
            print("bg =", tmpJSON['bg'])
            rgb = tmpJSON['bg'].split(',')
            BGcolor.r = int(rgb[0])
            BGcolor.g = int(rgb[1])
            BGcolor.b = int(rgb[2])
#            print(r, g, b, sep=' ')
            pixels.fill((BGcolor.r,BGcolor.g,BGcolor.b))
            del tmpJSON['bg']
#            print(tmpJSON)
        if 'fg' in tmpJSON:
            print("fg =", tmpJSON['fg'])
            rgb = tmpJSON['fg'].split(',')
            FGcolor.r = int(rgb[0])
            FGcolor.g = int(rgb[1])
            FGcolor.b = int(rgb[2])
#            print(r, g, b, sep=' ')
            pixels.fill((FGcolor.r,FGcolor.g,FGcolor.b))
            del tmpJSON['fg']
#            print(tmpJSON)
        if 'all' in tmpJSON:
            print("all =", tmpJSON['all'])
            rgb = tmpJSON['all'].split(',')
            r = int(rgb[0])
            g = int(rgb[1])
            b = int(rgb[2])
#            print(r, g, b, sep=' ')
            pixels.fill((r,g,b))
            del tmpJSON['all']
#            print(tmpJSON)
        for key in tmpJSON.keys():
            rgb = tmpJSON[key].split(',')
            r = int(rgb[0])
            g = int(rgb[1])
            b = int(rgb[2])
            print(key, r, g, b, sep=' ')
            if '-' in key:
                rangekeys = key.split('-')
                if (int(rangekeys[0]) > num_pixels):
                    print("pixels exceeded ", rangekeys[0])
                    continue;
                elif int(rangekeys[1]) > num_pixels:
                    endpixel = num_pixels
                else:
                    endpixel = int(rangekeys[1])
                for mypixels in range(int(rangekeys[0]), endpixel):
                    pixels[mypixels] = (r,g,b)
            else:
                if int(key) < num_pixels:
                    pixels[int(key)] = (r,g,b)
        pixels.show()

    except  ValueError:
        print("bad format")
        jsonResponse='{"success": false}'
    with response:
        response.send(body=jsonResponse, content_type="application/json")


@server.route("/huewhheel.min.js")
def base(request: HTTPRequest):

    with HTTPResponse(request, content_type="application/javascript") as response:
        response.send_file("huewhheel.min.js")

@server.route("/underscore-min.js")
def base(request: HTTPRequest):

    with HTTPResponse(request, content_type="application/javascript") as response:
        response.send_file("underscore-min.js")

def turnOff():
    global cometActive
    global sparkleActive
    cometActive = False
    sparkleActive = False
    pixels.fill((0, 0, 0))
    pixels.show()

def touchCycle():
    global touchCycleCount
    global FGcolor
    global cometActive
    global sparkleActive

    touchCycleCount = touchCycleCount + 1
    print(touchCycleCount)
    if touchCycleCount == 1:
        turnOff()
    elif touchCycleCount == 2:
        pixels.fill((FGcolor.r, FGcolor.g, FGcolor.b))
        pixels.show()
    elif touchCycleCount == 3:
        cometActive = True
        sparkleActive = False
    elif touchCycleCount == 4:
        sparkleActive = True
        cometActive = False
        touchCycleCount = 0
    else:
        turnOff()
        touchCycleCount = 0

print("starting server..")
# startup the server
try:
    server.start(str(wifi.radio.ipv4_address))
    print("Listening on http://%s:80" % wifi.radio.ipv4_address)
#  on restart the LEDs sometimes come on.  Turn them off
    pixels.fill((0, 0, 0))
    pixels.show()
#  if the server fails to begin, restart the pico w
except OSError:
    time.sleep(5)
    print("restarting..")
    microcontroller.reset()
ping_address = ipaddress.ip_address("8.8.4.4")

#  text objects for screen
#  connected to SSID text

while True:
    server.poll()
    if cometActive:
        comet.animate()
    if sparkleActive:
        sparkle.animate()
    if touch.value:
        now = time.monotonic()
        if now >= LAST_TOUCH_TIME + TOUCH_ON_DURATION:
            print("Touched!", touch.threshold)
            touchCycle()
            LAST_TOUCH_TIME = now



# requests = adafruit_requests.Session(pool, ssl.create_default_context())
