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

    def amap_to_gps(self, lng: float, lat: float) -> Optional[dict]:
        """
        将高德经纬度(lng, lat)转换为GPS经纬度，返回{"lng": float, "lat": float}。
        纯Python实现GCJ-02(GCJ) -> WGS84(GPS)转换。
        """
        # 常量
        PI = 3.1415926535897932384626
        a = 6378245.0
        ee = 0.00669342162296594323

        def out_of_china(lng, lat):
            return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)

        def transformlat(lng, lat):
            ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * (abs(lng) ** 0.5)
            ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
            ret += (20.0 * math.sin(lat * PI) + 40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
            ret += (160.0 * math.sin(lat / 12.0 * PI) + 320 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
            return ret

        def transformlng(lng, lat):
            ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * (abs(lng) ** 0.5)
            ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
            ret += (20.0 * math.sin(lng * PI) + 40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
            ret += (150.0 * math.sin(lng / 12.0 * PI) + 300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
            return ret

        import math
        lng = float(lng)
        lat = float(lat)
        if out_of_china(lng, lat):
            return {"lng": lng, "lat": lat}
        dlat = transformlat(lng - 105.0, lat - 35.0)
        dlng = transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * PI
        magic = math.sin(radlat)
        magic = 1 - ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * PI)
        dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * PI)
        mglat = lat + dlat
        mglng = lng + dlng
        return {"lng": lng * 2 - mglng, "lat": lat * 2 - mglat}

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
    print("--------------------------------")
    print(manager.amap_to_gps(116.397428, 39.90923))
    print("--------------------------------")