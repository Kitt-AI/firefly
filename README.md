# WARNING

This system is not usable yet until the parser is in the Python Package Index.

# firefly
Interacting with Philips Hue with natural language, powered by Firebird.

![Firefly screenshot]
(/screenshots/firefly-screenshot1.png)

![Firefly screenshot: incremental parsing]
(/screenshots/incremental.gif)

# How To

`python firebird/lightdemo.py -b bridge_ip -u bridge_username`

Then firefly will serve an interface on http://localhost:8085/ .

# Usage

``python firebird/lightdemo.py -h``:

```
usage: lightdemo.py [-h] [-b BRIDGE] [-u USER] [-p PORT] [-d DEBUG]

Firefly lighting demo

optional arguments:
  -h, --help            show this help message and exit
  -b BRIDGE, --bridge BRIDGE
                        Bridge IP address
  -u USER, --user USER  Bridge user name, more info:
                        http://www.developers.meethue.com/documentation/getting-started
  -p PORT, --port PORT  Webserver port
  -d DEBUG, --debug DEBUG
                        debug output
```                       

You'll need to:

1. Register a dev user name on your Hue Bridge. Here's 
   [how](http://www.developers.meethue.com/documentation/getting-started).
   Then pass it with ``-u USER``.
2. Find out and pass Bridge IP address (``-b 192.168.?.?``) *if* Firefly 
   failed to do so.  Firefly does UPnP discovery with SSDP (Simple Service 
   Discovery Protocol). If it failed, then you have to enter the IP address 
   manually.
   
This is only a *very basic* example of demonstrating firebird's ability to
parse natural languages. But you can take it from here to make your own
(text/voice-controlled) smart light systems.
