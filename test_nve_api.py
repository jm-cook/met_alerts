#!/usr/bin/env python3
"""Test script to check NVE API for landslide and flood alerts."""
import asyncio
import aiohttp
import json
from datetime import datetime, timezone


async def fetch_nve_warnings(county_id="46", lang="en", warning_type="landslide"):
    """Fetch NVE warnings."""
    
    if warning_type == "landslide":
        base_url = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10"
        type_name = "Landslide (Jordskred)"
    else:
        base_url = "https://api01.nve.no/hydrology/forecast/flood/v1.0.10"
        type_name = "Flood (Flom)"
    
    url = f"{base_url}/api/Warning/County/{county_id}/{lang}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "met_alerts/3.0.0 jeremy.m.cook@gmail.com"
    }
    
    print(f"NVE {type_name} API - County {county_id} ({lang})")
    print(f"URL: {url}\n")
    print("=" * 80)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(f"ERROR: Status {response.status}")
                    return None
                
                data = await response.json()
                
                # Count warnings
                yellow_or_higher = []
                for entry in data:
                    activity_level = entry.get("ActivityLevel", "1")
                    if activity_level != "1":
                        munis = entry.get("MunicipalityList", [])
                        muni_names = [m.get("Name") for m in munis] if munis else []
                        
                        # Construct varsom.no URL using the Id field
                        forecast_id = entry.get("Id", "")
                        # Use English or Norwegian based on lang parameter
                        lang_path = "en" if lang == "en" else ""
                        varsom_url = f"https://www.varsom.no/{lang_path}/flood-and-landslide-warning-service/forecastid/{forecast_id}".replace("//", "/") if forecast_id else None
                        
                        yellow_or_higher.append({
                            "level": activity_level,
                            "valid_from": entry.get("ValidFrom"),
                            "valid_to": entry.get("ValidTo"),
                            "main_text": entry.get("MainText"),
                            "warning_text": entry.get("WarningText"),
                            "advice_text": entry.get("AdviceText"),
                            "consequence_text": entry.get("ConsequenceText"),
                            "danger_type": entry.get("DangerTypeName"),
                            "municipalities": muni_names,
                            "id": forecast_id,
                            "url": varsom_url,
                            "danger_increase": entry.get("DangerIncreaseDateTime"),
                            "danger_decrease": entry.get("DangerDecreaseDateTime")
                        })
                
                print(f"Total entries: {len(data)}")
                print(f"Active warnings (level 2+): {len(yellow_or_higher)}\n")
                
                if yellow_or_higher:
                    for w in yellow_or_higher:
                        level_name = {"2": "YELLOW", "3": "ORANGE", "4": "RED"}.get(w["level"], w["level"])
                        print(f"  Level {level_name}:")
                        print(f"    Valid: {w['valid_from']} to {w['valid_to']}")
                        print(f"    Danger type: {w['danger_type']}")
                        print(f"    Main text: {w['main_text']}")
                        if w["municipalities"]:
                            print(f"    Municipalities: {', '.join(w['municipalities'])}")
                        print(f"    Forecast ID: {w['id']}")
                        print(f"    Varsom.no URL (with map): {w['url']}")
                        if w["danger_increase"]:
                            print(f"    Danger increases: {w['danger_increase']}")
                        if w["danger_decrease"]:
                            print(f"    Danger decreases: {w['danger_decrease']}")
                        print()
                else:
                    print("  No active warnings - all areas at GREEN level\n")
                
                return data
                
    except Exception as e:
        print(f"ERROR: {e}")
        return None


asyncio.run(fetch_nve_warnings("46", "en", "landslide"))
