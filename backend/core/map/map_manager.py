import requests
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class MapManager:
    def __init__(self):
        self.amap_key = os.getenv("AMAP_API_KEY")
        self.geocode_url = "https://restapi.amap.com/v3/geocode/geo"
        self.route_url = "https://restapi.amap.com/v5/direction/driving"

    def get_precise_location(self, city: str, place: str) -> str:
        """
        获取地点的精确位置（省市区县街道门牌等）
        """
        params = {
            "key": self.amap_key,
            "address": place,
            "city": city
        }
        resp = requests.get(self.geocode_url, params=params)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "1" and data.get("geocodes"):
            geocode = data["geocodes"][0]

            components = [
                geocode.get("province", ""),
                geocode.get("city", "") if isinstance(geocode.get("city"), str) else "",
                geocode.get("district", ""),
                geocode.get("township", ""),
                geocode.get("neighborhood", {}).get("name", ""),
                geocode.get("building", {}).get("name", ""),
                geocode.get("street", ""),
                geocode.get("number", "")
            ]

            # formatted_address 作为备用附加
            formatted = geocode.get("formatted_address", "")

            # 组装 + 去重
            address_parts = [part for part in components if part]
            if formatted and formatted not in address_parts:
                address_parts.append(formatted)

            return ", ".join(address_parts)
        else:
            return "未找到精确位置"


    def get_location_coordinates(self, address: str) -> Optional[Dict[str, float]]:
        """
        获取地点的经纬度
        """
        params = {
            "key": self.amap_key,
            "address": address
        }
        resp = requests.get(self.geocode_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0].get("location", "")
            if location:
                lng, lat = location.split(",")
                return {"lng": float(lng), "lat": float(lat)}
        return None

    # 预留：路线规划等方法

if __name__ == "__main__":
    # 测试代码
    manager = MapManager()
    city = "北京市"
    place = "北京南站"

    precise_location = manager.get_precise_location(city, place)
    print(f"精确位置: {precise_location}")

    coordinates = manager.get_location_coordinates(precise_location)
    print(f"经纬度: {coordinates}")

    # 其他测试可以在这里添加