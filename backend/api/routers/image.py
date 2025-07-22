from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.image.image_manager import ImageManager
import os

router = APIRouter()

class ImageIdentifyRequest(BaseModel):
    image_filename: str  # 仅文件名，不含路径

class ImageIdentifyResponse(BaseModel):
    landmark: str
    # city: Optional[str] = None  # 移除

@router.post("/identify_landmark", response_model=ImageIdentifyResponse)
async def identify_landmark(req: ImageIdentifyRequest):
    #前端请获取图片后保存在\backend\core\image\user_image
    try:
        manager = ImageManager()
        image_path = os.path.join(manager.user_image_dir, req.image_filename)
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="图片文件不存在")
        result = manager.identify_landmark(image_path)
        if result:
            # landmark, city = result
            return ImageIdentifyResponse(landmark=result)
        else:
            raise HTTPException(status_code=500, detail="未能识别出景点")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"识别异常: {e}")
