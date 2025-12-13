import aiohttp
import asyncio
import json

async def test_endpoint(url, name):
    """Test an NVE API endpoint and check for ImageUrlList."""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*80)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Accept": "application/json"}) as resp:
                if resp.status != 200:
                    print(f"Status: {resp.status}")
                    return
                
                data = await resp.json()
                
                # Check if data contains ImageUrlList
                images_found = False
                
                if isinstance(data, list):
                    for item in data:
                        image_urls = item.get("ImageUrlList", [])
                        if image_urls:
                            images_found = True
                            print(f"\n✓ Found ImageUrlList in item:")
                            print(f"  ID: {item.get('Id')}")
                            print(f"  Municipality: {item.get('MunicipalityList', [{}])[0].get('Name', 'N/A') if item.get('MunicipalityList') else 'N/A'}")
                            print(f"  Images ({len(image_urls)}):")
                            for img_url in image_urls:
                                print(f"    - {img_url}")
                
                elif isinstance(data, dict):
                    image_urls = data.get("ImageUrlList", [])
                    if image_urls:
                        images_found = True
                        print(f"\n✓ Found ImageUrlList:")
                        print(f"  ID: {data.get('Id')}")
                        print(f"  Images ({len(image_urls)}):")
                        for img_url in image_urls:
                            print(f"    - {img_url}")
                
                if not images_found:
                    print("\n✗ No ImageUrlList found or all are empty")
                    
    except Exception as e:
        print(f"ERROR: {e}")


async def main():
    base_url = "https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api"
    
    # Test different endpoints
    endpoints = [
        (f"{base_url}/Warning/All/en", "All warnings (English)"),
        (f"{base_url}/Warning/County/46/en", "County 46 (Vestland) - English"),
        (f"{base_url}/Warning/584731", "Specific warning by ID (584731 - Tysnes)"),
        (f"{base_url}/Warning/MasterId/584731", "Warning by MasterId (584731)"),
        (f"{base_url}/Warning/County/46/no", "County 46 (Vestland) - Norwegian"),
    ]
    
    for url, name in endpoints:
        await test_endpoint(url, name)
        await asyncio.sleep(0.5)  # Be nice to the API


asyncio.run(main())
