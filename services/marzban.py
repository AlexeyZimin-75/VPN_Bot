import httpx
import logging
from config import MARZBAN_URL, MARZBAN_USERNAME, MARZBAN_PASSWORD

# Настройка логирования, чтобы видеть ответы в консоли докера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarzbanAPI:
    def __init__(self):
        self.base_url = MARZBAN_URL.rstrip("/")
        self.username = MARZBAN_USERNAME
        self.password = MARZBAN_PASSWORD
        self.token = None
        # Базовые настройки для всех запросов
        self.timeout = 10.0

    async def get_token(self) -> str:
        """Получает токен авторизации"""
        url = f"{self.base_url}/api/admin/token"
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }

        print(f"[DEBUG] Попытка авторизации в Marzban: {url}")

        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            try:
                response = await client.post(
                    url,
                    data=data,
                    headers={"Accept": "application/json"}
                )
                print(f"[DEBUG] Ответ get_token: {response.status_code}")

                if response.status_code == 200:
                    self.token = response.json().get("access_token")
                    return self.token
                else:
                    print(f"[DEBUG] Ошибка авторизации: {response.text}")
                    return None

            except httpx.RemoteProtocolError:
                print("[DEBUG] Ошибка протокола, пробуем HTTP/1.1...")
                async with httpx.AsyncClient(http1=True, verify=False) as client_legacy:
                    response = await client_legacy.post(url, data=data)
                    self.token = response.json().get("access_token")
                    return self.token
            except Exception as e:
                print(f"[DEBUG] Ошибка при получении токена: {e}")
                return None

    async def get_headers(self) -> dict:
        """Подготавливает заголовки с токеном"""
        if not self.token:
            await self.get_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_user(self, username: str) -> dict:
        """Получает данные юзера из Marzban"""
        if not username:
            print("[DEBUG] get_user вызван с пустым username")
            return {}

        headers = await self.get_headers()
        url = f"{self.base_url}/api/user/{username}"

        print(f"[DEBUG] Запрос данных пользователя: {url}")

        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                print(f"[DEBUG] Ответ get_user ({username}): {response.status_code}")

                if response.status_code == 200:
                    return response.json()
                return {}
            except Exception as e:
                print(f"[DEBUG] Исключение в get_user: {e}")
                return {}

    async def create_user(self, username: str, expire_timestamp: int, data_limit_gb: int = 150) -> dict:
        """Создает нового юзера в Marzban"""
        headers = await self.get_headers()
        url = f"{self.base_url}/api/user"
        data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb > 0 else 0

        payload = {
            "username": username,
            "proxies": {"vless": {"flow": "xtls-rprx-vision"}},
            "inbounds": {"vless": ["VLESS TCP REALITY"]},
            "expire": expire_timestamp,
            "data_limit": data_limit_bytes,
            "status": "active"
        }

        print(f"[DEBUG] Создание пользователя {username}...")

        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                print(f"[DEBUG] Ответ create_user: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                print(f"[DEBUG] Ошибка создания: {response.text}")
                return {}
            except Exception as e:
                print(f"[DEBUG] Исключение в create_user: {e}")
                return {}

    async def update_user(self, username: str, expire_timestamp: int) -> dict:
        """Продлевает существующего юзера"""
        headers = await self.get_headers()
        url = f"{self.base_url}/api/user/{username}"

        payload = {
            "expire": expire_timestamp,
            "status": "active"
        }

        print(f"[DEBUG] Обновление пользователя {username}...")

        async with httpx.AsyncClient(verify=False, timeout=self.timeout) as client:
            try:
                response = await client.put(url, headers=headers, json=payload)
                print(f"[DEBUG] Ответ update_user: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                return {}
            except Exception as e:
                print(f"[DEBUG] Исключение в update_user: {e}")
                return {}