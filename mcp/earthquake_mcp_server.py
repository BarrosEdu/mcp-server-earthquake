# mcp/earthquake_server.py
import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()


API_BASE = "https://earthquake-ce5c9a0f9ec7.herokuapp.com"
API_KEY = os.getenv("API_KEY")


mcp = FastMCP("earthquake-mcp")

def _headers():
    return {
        "X-API-Key": API_KEY
    }

@mcp.tool()
async def recent(min_magnitude: float = 0.0, hours: int = 24, limit: int = 100):
    """
    Get recent earthquakes from your FastAPI.
    """
    async with httpx.AsyncClient(base_url=API_BASE, headers=_headers()) as client:
        resp = await client.get("/earthquakes/recent", params={
            "min_magnitude": min_magnitude,
            "hours": hours,
            "limit": limit
        })
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def around(lat: float, lon: float, radius_km: float = 300.0,
                 min_magnitude: float = 0.0, limit: int = 100):
    """
    Get earthquakes around a coordinate.
    """
    async with httpx.AsyncClient(base_url=API_BASE, headers=_headers()) as client:
        resp = await client.get("/earthquakes/around", params={
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km,
            "min_magnitude": min_magnitude,
            "limit": limit
        })
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    mcp.run()
