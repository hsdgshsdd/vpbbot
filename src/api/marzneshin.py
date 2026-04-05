import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from src.config import config
import logging

logger = logging.getLogger(__name__)


class MarzneshinAPI:
    """Полный клиент для взаимодействия с Marzneshin API (70 endpoints, все методы из docs.txt)"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.username = config.API_USERNAME
        self.password = config.API_PASSWORD
        self.token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                           params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        """Универсальный метод для HTTP запросов"""
        if not headers:
            headers = {}
        
        token = await self.get_token()
        headers['Authorization'] = f'Bearer {token}'
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=data, params=params, headers=headers,
                                          timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status in [200, 201]:
                        if resp.content_type == 'application/json':
                            return await resp.json()
                        else:
                            return await resp.text()
                    elif resp.status == 204:
                        return None
                    else:
                        error_text = await resp.text()
                        logger.error(f"{method} {endpoint} failed: {resp.status} - {error_text}")
                        raise Exception(f"API Error {resp.status}: {error_text}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    async def get_token(self) -> str:
        """Получить/обновить токен доступа"""
        if self.token and self.token_expires_at and datetime.utcnow() < self.token_expires_at:
            return self.token
        
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "username": self.username,
                    "password": self.password,
                    "grant_type": "password"
                }
                async with session.post(
                    f"{self.base_url}/api/admins/token",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.token = result.get('access_token')
                        self.token_expires_at = datetime.utcnow() + timedelta(hours=23)
                        return self.token
                    else:
                        logger.error(f"Failed to get token: {resp.status}")
                        raise Exception(f"Failed to get token: {resp.status}")
        except Exception as e:
            logger.error(f"Error getting token: {e}")
            raise
    
    # ============ USER MANAGEMENT ============
    
    async def get_users(self, usernames: List[str] = None, order_by: str = None,
                       descending: bool = False, is_active: Optional[bool] = None,
                       activated: Optional[bool] = None, expired: Optional[bool] = None,
                       data_limit_reached: Optional[bool] = None, enabled: Optional[bool] = None,
                       owner_username: Optional[str] = None, page: int = 1, size: int = 50) -> Dict:
        """Получить список пользователей с фильтрацией"""
        params = {"page": page, "size": size}
        
        if usernames:
            params["username"] = usernames
        if order_by:
            params["order_by"] = order_by
        if descending:
            params["descending"] = descending
        if is_active is not None:
            params["is_active"] = is_active
        if activated is not None:
            params["activated"] = activated
        if expired is not None:
            params["expired"] = expired
        if data_limit_reached is not None:
            params["data_limit_reached"] = data_limit_reached
        if enabled is not None:
            params["enabled"] = enabled
        if owner_username:
            params["owner_username"] = owner_username
            
        return await self._make_request("GET", "/api/users", params=params)
    
    async def create_user(self, username: str, expire_date: datetime = None, 
                         data_limit: int = None, services: List[int] = None) -> Dict:
        """Создать пользователя"""
        if not expire_date:
            expire_date = datetime.utcnow() + timedelta(days=30)
        
        if services is None:
            services = []
        
        payload = {
            "username": username,
            "expire_date": expire_date.isoformat(),
            "services": services
        }
        
        if data_limit:
            payload["data_limit"] = data_limit
        
        return await self._make_request("POST", "/api/users", data=payload)
    
    async def get_user(self, username: str) -> Dict:
        """Получить информацию о пользователе"""
        return await self._make_request("GET", f"/api/users/{username}")
    
    async def modify_user(self, username: str, **kwargs) -> Dict:
        """Изменить пользователя"""
        payload = {k: v for k, v in kwargs.items() if v is not None}
        return await self._make_request("PUT", f"/api/users/{username}", data=payload)
    
    async def delete_user(self, username: str) -> None:
        """Удалить пользователя"""
        return await self._make_request("DELETE", f"/api/users/{username}")
    
    async def enable_user(self, username: str) -> Dict:
        """Включить пользователя"""
        return await self._make_request("POST", f"/api/users/{username}/enable")
    
    async def disable_user(self, username: str) -> Dict:
        """Отключить пользователя"""
        return await self._make_request("POST", f"/api/users/{username}/disable")
    
    async def reset_user_data(self, username: str) -> Dict:
        """Сбросить использование трафика пользователя"""
        return await self._make_request("POST", f"/api/users/{username}/reset")
    
    async def revoke_user_subscription(self, username: str) -> Dict:
        """Отозвать подписку пользователя"""
        return await self._make_request("POST", f"/api/users/{username}/revoke_sub")
    
    async def get_user_services(self, username: str, page: int = 1, size: int = 50) -> Dict:
        """Получить сервисы пользователя"""
        return await self._make_request("GET", f"/api/users/{username}/services", 
                                       params={"page": page, "size": size})
    
    async def get_user_usage(self, username: str, start: Optional[str] = None, 
                            end: Optional[str] = None) -> Dict:
        """Получить использование трафика пользователем"""
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self._make_request("GET", f"/api/users/{username}/usage", params=params)
    
    async def set_user_owner(self, username: str, admin_username: str) -> Dict:
        """Установить владельца пользователя"""
        return await self._make_request("PUT", f"/api/users/{username}/set-owner",
                                       params={"admin_username": admin_username})
    
    async def reset_all_users_data(self) -> None:
        """Сбросить трафик всех пользователей"""
        return await self._make_request("POST", "/api/users/reset")
    
    async def delete_expired_users(self, passed_time: int) -> None:
        """Удалить пользователей, истекших более N дней назад"""
        return await self._make_request("DELETE", "/api/users/expired", 
                                       params={"passed_time": passed_time})
    
    # ============ SERVICE MANAGEMENT ============
    
    async def get_services(self, name: Optional[str] = None, page: int = 1, size: int = 50) -> Dict:
        """Получить список сервисов"""
        params = {"page": page, "size": size}
        if name:
            params["name"] = name
        return await self._make_request("GET", "/api/services", params=params)
    
    async def create_service(self, name: str, inbounds: List[int] = None) -> Dict:
        """Создать сервис"""
        if inbounds is None:
            inbounds = []
        
        payload = {
            "name": name,
            "inbounds": inbounds
        }
        
        return await self._make_request("POST", "/api/services", data=payload)
    
    async def get_service(self, service_id: int) -> Dict:
        """Получить информацию о сервисе"""
        return await self._make_request("GET", f"/api/services/{service_id}")
    
    async def modify_service(self, service_id: int, name: Optional[str] = None, 
                            inbounds: Optional[List[int]] = None) -> Dict:
        """Изменить сервис"""
        payload = {}
        if name is not None:
            payload["name"] = name
        if inbounds is not None:
            payload["inbounds"] = inbounds
            
        return await self._make_request("PUT", f"/api/services/{service_id}", data=payload)
    
    async def delete_service(self, service_id: int) -> None:
        """Удалить сервис"""
        return await self._make_request("DELETE", f"/api/services/{service_id}")
    
    async def get_service_users(self, service_id: int, page: int = 1, size: int = 50) -> Dict:
        """Получить пользователей сервиса"""
        return await self._make_request("GET", f"/api/services/{service_id}/users",
                                       params={"page": page, "size": size})
    
    async def get_service_inbounds(self, service_id: int, page: int = 1, size: int = 50) -> Dict:
        """Получить inbound'ы сервиса"""
        return await self._make_request("GET", f"/api/services/{service_id}/inbounds",
                                       params={"page": page, "size": size})
    
    # ============ NODE MANAGEMENT ============
    
    async def get_nodes(self, status: List[str] = None, name: Optional[str] = None, 
                       page: int = 1, size: int = 50) -> Dict:
        """Получить список узлов"""
        params = {"page": page, "size": size}
        if status:
            params["status"] = status
        if name:
            params["name"] = name
        return await self._make_request("GET", "/api/nodes", params=params)
    
    async def create_node(self, name: str, address: str, port: int, **kwargs) -> Dict:
        """Создать узел"""
        payload = {
            "name": name,
            "address": address,
            "port": port
        }
        payload.update(kwargs)
        return await self._make_request("POST", "/api/nodes", data=payload)
    
    async def get_node(self, node_id: int) -> Dict:
        """Получить информацию об узле"""
        return await self._make_request("GET", f"/api/nodes/{node_id}")
    
    async def get_node_settings(self) -> Dict:
        """Получить настройки узлов"""
        return await self._make_request("GET", "/api/nodes/settings")
    
    async def modify_node(self, node_id: int, **kwargs) -> Dict:
        """Изменить узел"""
        return await self._make_request("PUT", f"/api/nodes/{node_id}", data=kwargs)
    
    async def delete_node(self, node_id: int) -> None:
        """Удалить узел"""
        return await self._make_request("DELETE", f"/api/nodes/{node_id}")
    
    async def reconnect_node(self, node_id: int) -> None:
        """Переподключить узел"""
        return await self._make_request("POST", f"/api/nodes/{node_id}/resync")
    
    async def get_node_usage(self, node_id: int, start: Optional[str] = None, 
                            end: Optional[str] = None) -> Dict:
        """Получить использование узла"""
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self._make_request("GET", f"/api/nodes/{node_id}/usage", params=params)
    
    async def get_backend_stats(self, node_id: int, backend: str) -> Dict:
        """Получить статистику бэкенда"""
        return await self._make_request("GET", f"/api/nodes/{node_id}/{backend}/stats")
    
    async def get_backend_config(self, node_id: int, backend: str) -> Dict:
        """Получить конфиг Xray бэкенда"""
        return await self._make_request("GET", f"/api/nodes/{node_id}/{backend}/config")
    
    async def modify_backend_config(self, node_id: int, backend: str, config: Dict) -> None:
        """Изменить конфиг Xray бэкенда"""
        return await self._make_request("PUT", f"/api/nodes/{node_id}/{backend}/config", data=config)
    
    # ============ INBOUND MANAGEMENT ============
    
    async def get_inbounds(self, tag: Optional[str] = None, page: int = 1, size: int = 50) -> Dict:
        """Получить список inbound'ов"""
        params = {"page": page, "size": size}
        if tag:
            params["tag"] = tag
        return await self._make_request("GET", "/api/inbounds", params=params)
    
    async def get_inbound(self, inbound_id: int) -> Dict:
        """Получить информацию об inbound'е"""
        return await self._make_request("GET", f"/api/inbounds/{inbound_id}")
    
    async def get_inbound_hosts(self, inbound_id: int, page: int = 1, size: int = 50) -> Dict:
        """Получить хосты inbound'а"""
        return await self._make_request("GET", f"/api/inbounds/{inbound_id}/hosts",
                                       params={"page": page, "size": size})
    
    async def create_inbound_host(self, inbound_id: int, remark: str, address: str, 
                                 **kwargs) -> Dict:
        """Создать хост в inbound'е"""
        payload = {
            "remark": remark,
            "address": address
        }
        payload.update(kwargs)
        return await self._make_request("POST", f"/api/inbounds/{inbound_id}/hosts", 
                                       data=payload)
    
    # ============ HOST MANAGEMENT ============
    
    async def get_hosts(self, page: int = 1, size: int = 50) -> Dict:
        """Получить все хосты"""
        return await self._make_request("GET", "/api/inbounds/hosts", 
                                       params={"page": page, "size": size})
    
    async def create_unbound_host(self, remark: str, address: str, **kwargs) -> Dict:
        """Создать незаполненный хост"""
        payload = {
            "remark": remark,
            "address": address
        }
        payload.update(kwargs)
        return await self._make_request("POST", "/api/inbounds/hosts", data=payload)
    
    async def get_host(self, host_id: int) -> Dict:
        """Получить информацию о хосте"""
        return await self._make_request("GET", f"/api/inbounds/hosts/{host_id}")
    
    async def modify_host(self, host_id: int, remark: Optional[str] = None, 
                         address: Optional[str] = None, **kwargs) -> Dict:
        """Изменить хост"""
        payload = {}
        if remark is not None:
            payload["remark"] = remark
        if address is not None:
            payload["address"] = address
        payload.update(kwargs)
        return await self._make_request("PUT", f"/api/inbounds/hosts/{host_id}", data=payload)
    
    async def delete_host(self, host_id: int) -> None:
        """Удалить хост"""
        return await self._make_request("DELETE", f"/api/inbounds/hosts/{host_id}")
    
    # ============ ADMIN MANAGEMENT ============
    
    async def get_admins(self) -> Dict:
        """Получить список администраторов"""
        return await self._make_request("GET", "/api/admins")
    
    async def create_admin(self, username: str, password: str) -> Dict:
        """Создать администратора"""
        payload = {
            "username": username,
            "password": password
        }
        return await self._make_request("POST", "/api/admins", data=payload)
    
    async def delete_admin(self, username: str) -> None:
        """Удалить администратора"""
        return await self._make_request("DELETE", f"/api/admins/{username}")
    
    async def disable_admin_users(self, admin_username: str) -> Dict:
        """Отключить пользователей администратора"""
        return await self._make_request("POST", f"/api/admins/{admin_username}/disable_users")
    
    async def enable_admin_users(self, admin_username: str) -> Dict:
        """Включить пользователей администратора"""
        return await self._make_request("POST", f"/api/admins/{admin_username}/enable_users")
    
    # ============ SUBSCRIPTION ENDPOINTS ============
    
    async def get_user_subscription_info(self, username: str, key: str) -> Dict:
        """Получить информацию о подписке пользователя"""
        return await self._make_request("GET", f"/sub/{username}/{key}/info")
    
    async def get_user_subscription_by_type(self, username: str, key: str, 
                                          client_type: str) -> str:
        """Получить подписку по типу клиента (v2ray, xray, sing-box, clash, clash-meta, links, wireguard)"""
        return await self._make_request("GET", f"/sub/{username}/{key}/{client_type}")
    
    async def get_user_subscription_usage(self, username: str, key: str, 
                                         start: Optional[str] = None, 
                                         end: Optional[str] = None) -> Dict:
        """Получить использование подписки"""
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self._make_request("GET", f"/sub/{username}/{key}/usage", params=params)
    
    # ============ SYSTEM SETTINGS ============
    
    async def get_subscription_settings(self) -> Dict:
        """Получить настройки подписки"""
        return await self._make_request("GET", "/api/system/settings/subscription")
    
    async def update_subscription_settings(self, **kwargs) -> Dict:
        """Обновить настройки подписки"""
        return await self._make_request("PUT", "/api/system/settings/subscription", data=kwargs)
    
    async def get_telegram_settings(self) -> Optional[Dict]:
        """Получить настройки Telegram"""
        return await self._make_request("GET", "/api/system/settings/telegram")
    
    async def update_telegram_settings(self, settings: Optional[Dict] = None) -> Optional[Dict]:
        """Обновить настройки Telegram"""
        return await self._make_request("PUT", "/api/system/settings/telegram", data=settings)
    
    # ============ SYSTEM STATISTICS ============
    
    async def get_admins_stats(self) -> Dict:
        """Получить статистику администраторов"""
        return await self._make_request("GET", "/api/system/stats/admins")
    
    async def get_nodes_stats(self) -> Dict:
        """Получить статистику узлов"""
        return await self._make_request("GET", "/api/system/stats/nodes")
    
    async def get_traffic_stats(self, start: Optional[str] = None, 
                               end: Optional[str] = None) -> Dict:
        """Получить статистику трафика"""
        params = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self._make_request("GET", "/api/system/stats/traffic", params=params)
    
    async def get_users_stats(self) -> Dict:
        """Получить статистику пользователей"""
        return await self._make_request("GET", "/api/system/stats/users")
    
    # ============ ADMIN MANAGEMENT (MISSING) ============
    
    async def get_current_admin(self) -> Dict:
        """Получить информацию о текущем администраторе"""
        return await self._make_request("GET", "/api/admins/current")
    
    async def get_admin(self, username: str) -> Dict:
        """Получить информацию об администраторе"""
        return await self._make_request("GET", f"/api/admins/{username}")
    
    async def modify_admin(self, username: str, **kwargs) -> Dict:
        """Изменить администратора"""
        payload = {k: v for k, v in kwargs.items() if v is not None}
        return await self._make_request("PUT", f"/api/admins/{username}", data=payload)
    
    async def get_admin_services(self, admin_username: str, page: int = 1, size: int = 50) -> Dict:
        """Получить сервисы администратора"""
        params = {"page": page, "size": size}
        return await self._make_request("GET", f"/api/admins/{admin_username}/services", params=params)
    
    async def get_admin_users(self, admin_username: str, page: int = 1, size: int = 50) -> Dict:
        """Получить пользователей администратора"""
        params = {"page": page, "size": size}
        return await self._make_request("GET", f"/api/admins/{admin_username}/users", params=params)
    
    # ============ USER SUBSCRIPTION (MISSING BASE VERSION) ============
    
    async def get_user_subscription(self, username: str, key: str) -> str:
        """Получить подписку пользователя (базовая версия, обычно возвращает ссылку с конфигом)"""
        return await self._make_request("GET", f"/sub/{username}/{key}")


# Глобальный экземпляр API
api = MarzneshinAPI()
