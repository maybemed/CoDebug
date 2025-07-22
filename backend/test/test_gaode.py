from time import sleep

import requests
from fontTools.misc.plistlib import end_key


def get_coordinates(location_name, api_key,city):
    """
    通过地名获取坐标

    Args:
        location_name: str - 地点名称
        api_key: str - 高德地图API密钥

    Returns:
        str: 坐标字符串 "经度,纬度"
    """
    try:
        location_name = city+location_name
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            "address": location_name,
            "key": api_key,
            "output": "json"
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0]["location"]
            return location

    except Exception as e:
        print(f"获取坐标失败: {location_name}, 错误: {e}")

    return None


from backend.config.settings import settings
API_KEY = settings.GAODE_API_KEY
start_coords= get_coordinates("南大津南校区", API_KEY,"天津市")
end_coords = get_coordinates("天大北洋园", API_KEY,"天津市")


def get_route_info(start_location, end_location, api_key, city):
    """
    调用高德地图API获取两点间的路径信息

    Args:
        start_location: str - 起点名称
        end_location: str - 终点名称
        api_key: str - 高德地图API密钥

    Returns:
        tuple: (distance, transport, commuting_time)
    """
    sleep(1)
    # 第一步：获取起点和终点的坐标
    start_coords = get_coordinates(start_location, api_key, city)
    end_coords = get_coordinates(end_location, api_key, city)

    if not start_coords or not end_coords:
        return "", "", ""

    # 第二步：调用路径规划API（这里使用驾车路径规划）
    url = "https://restapi.amap.com/v5/direction/driving"
    params = {
        "origin": start_coords,
        "destination": end_coords,
        "key": api_key,
        "show_fields": ["cost"],
        "output": "json"
    }

    response = requests.get(url, params=params)
    data = response.json()
    print(data)

    if data.get("status") == "1" and data.get("route"):
        route = data["route"]["paths"][0]

        # 距离（转换为km）
        distance_m = int(route["distance"])
        distance = f"{distance_m / 1000:.1f}km"

        # 时间（转换为秒）
        duration_s = int(route['cost']["duration"])

        # 交通方式（这里默认为驾车，你可以根据距离调整）
        if distance_m < 2000:
            transport = "步行"
            duration_s *= 2
        elif distance_m < 50000:
            transport = "打车"
        else:
            transport = "公共交通"

        # 时间（转换为小时分钟格式）
        hours = duration_s // 3600
        minutes = (duration_s % 3600) // 60

        if hours > 0:
            commuting_time = f"{hours}h{minutes}min"
        else:
            commuting_time = f"{minutes}min"

        return distance, transport, commuting_time


print(get_route_info("南大津南校区", "天大北洋园", API_KEY, "天津市"))