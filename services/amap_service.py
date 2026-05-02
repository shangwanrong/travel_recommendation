import requests
import time
from typing import List, Dict, Optional
from config import Config

class AmapService:
    """高德地图API服务类"""

    def __init__(self):
        self.api_key = Config.AMAP_API_KEY
        self.base_url = Config.AMAP_BASE_URL
        self.timeout = Config.REQUEST_TIMEOUT
        self.delay = Config.REQUEST_DELAY

        if not self.api_key:
            raise ValueError("高德地图API Key未配置，请在.env文件中设置AMAP_API_KEY")

    def search_attractions(self, city: str, page: int = 1, keywords: str = "景点|风景区|公园") -> List[Dict]:
        """
        搜索景点

        Args:
            city: 城市名称
            page: 页码（从1开始）
            keywords: 搜索关键词

        Returns:
            景点列表
        """
        url = f"{self.base_url}/place/text"
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "types": Config.POI_TYPES['attraction'],
            "offset": 20,
            "page": page,
            "extensions": "all"
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()

            if data.get('status') == '1' and data.get('pois'):
                return self._parse_pois(data['pois'], 'attraction')
            else:
                print(f"搜索景点失败: {data.get('info', '未知错误')}")
                return []
        except Exception as e:
            print(f"搜索景点异常: {str(e)}")
            return []
        finally:
            time.sleep(self.delay)

    def search_hotels(self, city: str, page: int = 1, keywords: str = "酒店") -> List[Dict]:
        """
        搜索酒店

        Args:
            city: 城市名称
            page: 页码
            keywords: 搜索关键词

        Returns:
            酒店列表
        """
        url = f"{self.base_url}/place/text"
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "types": Config.POI_TYPES['hotel'],
            "offset": 20,
            "page": page,
            "extensions": "all"
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()

            if data.get('status') == '1' and data.get('pois'):
                return self._parse_pois(data['pois'], 'hotel')
            else:
                print(f"搜索酒店失败: {data.get('info', '未知错误')}")
                return []
        except Exception as e:
            print(f"搜索酒店异常: {str(e)}")
            return []
        finally:
            time.sleep(self.delay)

    def search_restaurants(self, city: str, page: int = 1, keywords: str = "美食") -> List[Dict]:
        """
        搜索餐厅

        Args:
            city: 城市名称
            page: 页码
            keywords: 搜索关键词

        Returns:
            餐厅列表
        """
        url = f"{self.base_url}/place/text"
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "types": Config.POI_TYPES['restaurant'],
            "offset": 20,
            "page": page,
            "extensions": "all"
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()

            if data.get('status') == '1' and data.get('pois'):
                return self._parse_pois(data['pois'], 'restaurant')
            else:
                print(f"搜索餐厅失败: {data.get('info', '未知错误')}")
                return []
        except Exception as e:
            print(f"搜索餐厅异常: {str(e)}")
            return []
        finally:
            time.sleep(self.delay)

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Dict]:
        """
        地理编码：地址转坐标

        Args:
            address: 地址
            city: 城市（可选）

        Returns:
            坐标信息
        """
        url = f"{self.base_url}/geocode/geo"
        params = {
            "key": self.api_key,
            "address": address
        }
        if city:
            params["city"] = city

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()

            if data.get('status') == '1' and data.get('geocodes'):
                geocode = data['geocodes'][0]
                location = geocode.get('location', '').split(',')
                if len(location) == 2:
                    return {
                        'longitude': float(location[0]),
                        'latitude': float(location[1])
                    }
            return None
        except Exception as e:
            print(f"地理编码异常: {str(e)}")
            return None
        finally:
            time.sleep(self.delay)

    def _parse_pois(self, pois: List, poi_type: str) -> List[Dict]:
        """
        解析POI数据

        Args:
            pois: POI列表
            poi_type: POI类型（attraction/hotel/restaurant）

        Returns:
            解析后的数据列表
        """
        results = []
        for poi in pois:
            location = poi.get('location', '').split(',')

            # 处理地址字段（可能是字符串或列表）
            address = poi.get('address', '')
            if isinstance(address, list):
                address = ', '.join(address) if address else ''

            # 处理电话字段（可能是字符串或列表）
            phone = poi.get('tel', '')
            if isinstance(phone, list):
                phone = ';'.join(phone) if phone else ''

            parsed = {
                'name': poi.get('name', ''),
                'address': address,
                'longitude': float(location[0]) if len(location) > 0 and location[0] else None,
                'latitude': float(location[1]) if len(location) > 1 and location[1] else None,
                'phone': phone,
                'type_code': poi.get('type', ''),
                'city': poi.get('cityname', ''),
                'province': poi.get('pname', ''),
                'poi_type': poi_type
            }

            # 只添加有坐标的POI
            if parsed['longitude'] and parsed['latitude']:
                results.append(parsed)

        return results

    def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            是否连接成功
        """
        try:
            result = self.search_attractions("北京", page=1)
            if result:
                print(f"高德地图API连接成功！找到 {len(result)} 个景点")
                return True
            else:
                print("高德地图API连接失败：未返回数据")
                return False
        except Exception as e:
            print(f"高德地图API连接失败: {str(e)}")
            return False
