import aiohttp
import asyncio
import ssl
import certifi
from datetime import datetime, timezone

async def main():
    url = "https://api.met.no/weatherapi/metalerts/2.0/current.json?lang=en"
    headers = {"User-Agent": "met_alerts/3.0.0 jeremy.m.cook@gmail.com"}
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, ssl=ssl_context) as response:
            data = await response.json()
            
    features = data.get("features", [])
    print(f"Total current alerts in Norway: {len(features)}\n")
    
    # Filter for Vestland county (46) or nearby
    now = datetime.now(timezone.utc)
    vestland_alerts = []
    
    for feature in features:
        props = feature.get("properties", {})
        area = props.get("area", "")
        counties = props.get("county", [])
        
        # County 46 is Vestland
        if "Vestland" in area or "vest" in area.lower() or "46" in counties:
            vestland_alerts.append(feature)
    
    print(f"Alerts mentioning Vestland: {len(vestland_alerts)}\n")
    
    for alert in vestland_alerts:
        props = alert.get("properties", {})
        when = alert.get("when", {})
        interval = when.get("interval", [])
        
        print(f"Event: {props.get('event', 'N/A')}")
        print(f"Title: {props.get('title', 'N/A')}")
        print(f"Area: {props.get('area', 'N/A')}")
        print(f"Start: {interval[0] if len(interval) > 0 else 'N/A'}")
        print(f"End: {interval[1] if len(interval) > 1 else 'N/A'}")
        print(f"Counties: {props.get('county', [])}")
        print("-" * 80)
    
    # List all unique event types
    event_types = sorted(set(f["properties"].get("event") for f in features if f["properties"].get("event")))
    print(f"\nAll current event types in Norway:")
    for evt in event_types:
        print(f"  - {evt}")

asyncio.run(main())
