import aiohttp
import asyncio
import json

async def main():
    url = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api/Warning/County/46/en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"Accept": "application/json"}) as resp:
            data = await resp.json()
    
    # Find Tysnes warning
    for entry in data:
        if entry.get("ActivityLevel") == "2":
            munis = entry.get("MunicipalityList", [])
            if any(m.get("Name") == "Tysnes" for m in munis):
                print(json.dumps(entry, indent=2))
                break

asyncio.run(main())
