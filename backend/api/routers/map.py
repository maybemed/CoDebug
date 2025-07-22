from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.core.map.map_manager import MapManager
import requests
from time import sleep
router = APIRouter()

class RoutePlanRequest(BaseModel):
    city: str
    origin: str
    destination: str
    waypoints: Optional[str] = None  # 途径点字符串，逗号分隔

class RoutePlanResponse(BaseModel):
    points: List[List[float]]  # [[lng, lat], ...]

@router.post("/plan_route", response_model=RoutePlanResponse)
async def plan_route(req: RoutePlanRequest):
    try:
        manager = MapManager()
        # 获取起点、终点、途径点经纬度
        origin_coord = manager.get_location_coordinates(manager.get_precise_location(req.city, req.origin))
        sleep(1)
        dest_coord = manager.get_location_coordinates(manager.get_precise_location(req.city, req.destination))
        print(f"起点经纬度: {origin_coord}, 终点经纬度: {dest_coord}")
        waypoints_coords = []
        if req.waypoints:
            for wp in req.waypoints.split(","):
                coord = manager.get_location_coordinates(manager.get_precise_location(req.city, wp.strip()))
                if coord:
                    waypoints_coords.append(coord)
        # 构造高德API参数
        origin_str = f"{origin_coord['lng']},{origin_coord['lat']}"
        dest_str = f"{dest_coord['lng']},{dest_coord['lat']}"
        waypoints_str = "|".join([f"{c['lng']},{c['lat']}" for c in waypoints_coords]) if waypoints_coords else None
        params = {
            "key": manager.amap_key,
            "origin": origin_str,
            "destination": dest_str,
            "strategy": 32,
            "show_fields": "polyline"
        }
        if waypoints_str:
            params["waypoints"] = waypoints_str
        resp = requests.get(manager.route_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1" and data.get("route") and data["route"].get("paths"):
            # 取第一条路径的所有polyline点
            path = data["route"]["paths"][0]
            points = []
            for step in path.get("steps", []):
                polyline = step.get("polyline", "")
                for pair in polyline.split(";"):
                    if pair:
                        lng, lat = pair.split(",")
                        # 转为GPS坐标
                        gps = manager.amap_to_gps(float(lng), float(lat))
                        points.append([gps["lng"], gps["lat"]])
            return RoutePlanResponse(points=points)
        else:
            raise HTTPException(status_code=500, detail="路线规划失败或无结果")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路线规划异常: {e}")

class ListCoordinatesRequest(BaseModel):
    city: str
    places: List[str]

class ListCoordinatesResponse(BaseModel):
    coordinates: List[Optional[dict]]  # [{"lng": float, "lat": float} or None]

@router.post("/get_list_coordinates", response_model=ListCoordinatesResponse)
async def get_list_coordinates(req: ListCoordinatesRequest):
    try:
        manager = MapManager()
        coords = []
        for place in req.places:
            precise = manager.get_precise_location(req.city, place)
            coord = manager.get_location_coordinates(precise)
            if coord:
                coord = manager.amap_to_gps(coord["lng"], coord["lat"])
            coords.append(coord)
        return ListCoordinatesResponse(coordinates=coords)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量获取经纬度异常: {e}")
