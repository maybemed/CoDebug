import requests
import base64
import os
from typing import Optional, Tuple
from backend.core.map.map_manager import MapManager

class ImageManager:
    def __init__(self):
        self.api_key = os.getenv('BAIDU_API_KEY')
        self.secret_key = os.getenv('BAIDU_SECRET_KEY')
        self.user_image_dir = os.path.join(os.path.dirname(__file__), 'user_image')
        self._access_token = None

    def get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        res = requests.get(
            'https://aip.baidubce.com/oauth/2.0/token',
            params={
                'grant_type': 'client_credentials',
                'client_id': self.api_key,
                'client_secret': self.secret_key
            }
        )
        self._access_token = res.json()['access_token']
        return self._access_token

    def identify_landmark(self, image_path: str) -> Optional[str]:
        """
        识别图片中的景点，返回景点名。
        """
        access_token = self.get_access_token()
        url = f'https://aip.baidubce.com/rest/2.0/image-classify/v1/landmark?access_token={access_token}'
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'image': image_data}
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        if 'result' in result and result['result']:
            landmark = result['result'].get('landmark', '')
            return landmark
        return None
