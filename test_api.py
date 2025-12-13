#!/usr/bin/env python3
"""Test script to check Met.no API for alerts at specific coordinates."""
import asyncio
import aiohttp
import json
import sys
import ssl
import certifi


async def fetch_alerts(latitude: float, longitude: float, lang: str = "no", email: str = "your.email@example.com", endpoint: str = "current"):
    """Fetch Met alerts for given coordinates."""
    # Round to 4 decimals
    lat_rounded = round(latitude, 4)
    lon_rounded = round(longitude, 4)
    
    # Using public API endpoint for testing (integration uses HA-specific endpoint)
    url = f"https://api.met.no/weatherapi/metalerts/2.0/{endpoint}.json?lat={lat_rounded}&lon={lon_rounded}&lang={lang}"
    
    # Met.no requires a User-Agent header identifying the application
    headers = {
        "User-Agent": f"met_alerts/3.0.0 {email}"
    }
    
    print(f"Testing Met.no API with coordinates:")
    print(f"  Original: lat={latitude}, lon={longitude}")
    print(f"  Rounded:  lat={lat_rounded}, lon={lon_rounded}")
    print(f"  Language: {lang}")
    print(f"\nAPI URL: {url}")
    print(f"Headers: {headers}\n")
    print("-" * 80)
    
    # Create SSL context using certifi certificates
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(10):
                async with session.get(url, headers=headers, ssl=ssl_context) as response:
                    print(f"Response Status: {response.status}")
                    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                    print("-" * 80)
                    
                    if response.status != 200:
                        print(f"ERROR: API returned status {response.status}")
                        text = await response.text()
                        print(f"Response body: {text}")
                        return None
                    
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' not in content_type:
                        print(f"ERROR: Unexpected content type: {content_type}")
                        return None
                    
                    try:
                        data = await response.json()
                        print("\n✓ Successfully fetched data from API\n")
                        
                        # Pretty print the JSON response
                        print("Full API Response:")
                        print("=" * 80)
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        print("=" * 80)
                        
                        # Analyze the alerts
                        from datetime import datetime, timezone
                        
                        features = data.get("features", [])
                        print(f"\n\nSUMMARY:")
                        print(f"  Total alerts found: {len(features)}")
                        
                        if features:
                            now = datetime.now(timezone.utc)
                            print(f"  Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
                            print("\n  Alert Details:")
                            
                            for idx, feature in enumerate(features, 1):
                                props = feature.get("properties", {})
                                when = feature.get("when", {})
                                interval = when.get("interval", [])
                                
                                # Parse start and end times
                                start_str = interval[0] if len(interval) > 0 else "Unknown"
                                end_str = interval[1] if len(interval) > 1 else "Unknown"
                                
                                # Determine if alert is past, current, or future
                                status = "Unknown"
                                if start_str != "Unknown" and end_str != "Unknown":
                                    start_time = datetime.fromisoformat(start_str.replace('+00:00', '+00:00'))
                                    end_time = datetime.fromisoformat(end_str.replace('+00:00', '+00:00'))
                                    
                                    if end_time < now:
                                        status = "EXPIRED"
                                    elif start_time > now:
                                        status = "UPCOMING"
                                    else:
                                        status = "ACTIVE NOW"
                                
                                print(f"\n  Alert #{idx}: [{status}]")
                                print(f"    Event: {props.get('event', 'N/A')}")
                                print(f"    Title: {props.get('title', 'N/A')}")
                                print(f"    Start time: {start_str}")
                                print(f"    End time:   {end_str}")
                                print(f"    Awareness Level: {props.get('awareness_level', 'N/A')}")
                                print(f"    Severity: {props.get('severity', 'N/A')}")
                                print(f"    Certainty: {props.get('certainty', 'N/A')}")
                                print(f"    Area: {props.get('area', 'N/A')}")
                                print(f"    Description: {props.get('description', 'N/A')[:100]}...")
                        else:
                            print("  No alerts found for this location.")
                        
                        return data
                        
                    except json.JSONDecodeError as err:
                        print(f"ERROR: Failed to parse JSON response: {err}")
                        text = await response.text()
                        print(f"Response body: {text[:500]}")
                        return None
                        
    except aiohttp.ClientError as err:
        print(f"ERROR: Network error: {err}")
        return None
    except asyncio.TimeoutError:
        print("ERROR: Request timed out after 10 seconds")
        return None
    except Exception as err:
        print(f"ERROR: Unexpected error: {type(err).__name__}: {err}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function."""
    # Your coordinates
    latitude = 59.94046730665437
    longitude = 5.483461731763352
    lang = "no"  # Change to "en" for English
    email = "jeremy.m.cook@gmail.com"
    
    # Allow command line overrides
    if len(sys.argv) > 2:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])
        if len(sys.argv) > 3:
            lang = sys.argv[3]
        if len(sys.argv) > 4:
            email = sys.argv[4]
    
    # Try both current and all endpoints
    print("=" * 80)
    print("CHECKING /current ENDPOINT (active alerts only)")
    print("=" * 80)
    await fetch_alerts(latitude, longitude, lang, email, "current")
    
    print("\n\n")
    print("=" * 80)
    print("CHECKING /all ENDPOINT (all alerts including future)")
    print("=" * 80)
    await fetch_alerts(latitude, longitude, lang, email, "all")
    
    # Also try without coordinates to see all alerts in the system
    print("\n\n")
    print("=" * 80)
    print("CHECKING /current.json WITHOUT coordinates (all alerts in Norway)")
    print("=" * 80)
    url_no_coords = f"https://api.met.no/weatherapi/metalerts/2.0/current.json?lang={lang}"
    print(f"\nAPI URL: {url_no_coords}\n")
    headers = {"User-Agent": f"met_alerts/3.0.0 {email}"}
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(10):
                async with session.get(url_no_coords, headers=headers, ssl=ssl_context) as response:
                    data = await response.json()
                    features = [f for f in data.get("features", []) if "Vestland" in f.get("properties", {}).get("area", "")]
                    print(f"Total alerts in Vestland: {len(features)}")
                    for idx, feature in enumerate(features, 1):
                        props = feature.get("properties", {})
                        when = feature.get("when", {})
                        interval = when.get("interval", [])
                        print(f"\n  Alert #{idx}:")
                        print(f"    Event: {props.get('event', 'N/A')}")
                        print(f"    Title: {props.get('title', 'N/A')}")
                        print(f"    Start: {interval[0] if len(interval) > 0 else 'N/A'}")
                        print(f"    End: {interval[1] if len(interval) > 1 else 'N/A'}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
