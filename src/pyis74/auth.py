"""Методы авторизации в API IS74."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Final

from pyis74 import endpoints
from pyis74.models import MobileToken, PhoneConfirmationCheck, PhoneConfirmationStart
from pyis74.options import ClientRequestOptions
from pyis74.types import normalize_json_object

if TYPE_CHECKING:
    from pyis74.client import IS74, IS74Async

RUSSIAN_PHONE_WITH_COUNTRY_CODE_LENGTH: Final = 11


class AuthAPI:
    """Асинхронный домен авторизации IS74."""

    def __init__(self, client: IS74Async) -> None:
        """Создает домен авторизации.

        Args:
            client: Асинхронный клиент верхнего уровня.
        """
        self._client = client

    async def login_with_password(self, username: str, password: str) -> MobileToken:
        """Авторизуется по логину и паролю.

        Args:
            username: Логин учетной записи IS74.
            password: Пароль учетной записи IS74.

        Returns:
            Mobile access token.
        """
        payload = await self._client.request(
            "POST",
            endpoints.AUTH_MOBILE,
            ClientRequestOptions(json_body={"username": username, "password": password}),
        )
        token = MobileToken.from_json_object(normalize_json_object(payload))
        self._client.set_mobile_token(token.token)
        return token

    async def request_phone_confirmation(
        self,
        phone: str,
        *,
        device_id: str | None = None,
    ) -> PhoneConfirmationStart:
        """Запрашивает код подтверждения для телефонной авторизации.

        Args:
            phone: Номер телефона. Можно передавать с `+7`, `7` или `8`.
            device_id: Идентификатор устройства. Если не передан, будет создан автоматически.

        Returns:
            Результат старта phone auth flow.
        """
        normalized_phone = normalize_phone(phone)
        actual_device_id = device_id or generate_device_id()
        payload = await self._client.request(
            "POST",
            endpoints.AUTH_SEND_SMS,
            ClientRequestOptions(
                json_body={"phone": normalized_phone, "uniqueDeviceId": actual_device_id}
            ),
        )
        return PhoneConfirmationStart.from_json_object(
            normalize_json_object(payload),
            device_id=actual_device_id,
        )

    async def check_phone_confirmation(
        self,
        phone: str,
        code: str,
        *,
        device_id: str,
    ) -> PhoneConfirmationCheck:
        """Проверяет код подтверждения телефона.

        Args:
            phone: Номер телефона. Можно передавать с `+7`, `7` или `8`.
            code: Код из SMS или последние цифры номера входящего звонка.
            device_id: Идентификатор устройства из `request_phone_confirmation`.

        Returns:
            Результат проверки кода и список доступных адресов.
        """
        payload = await self._client.request(
            "POST",
            endpoints.AUTH_CONFIRM,
            ClientRequestOptions(
                json_body={
                    "confirmCode": code,
                    "phone": normalize_phone(phone),
                    "uniqueDeviceId": device_id,
                }
            ),
        )
        return PhoneConfirmationCheck.from_json_object(normalize_json_object(payload))

    async def get_token_for_user(
        self,
        *,
        auth_id: str,
        user_id: int,
        device_id: str | None = None,
    ) -> MobileToken:
        """Получает mobile token для выбранного адреса пользователя.

        Args:
            auth_id: Идентификатор auth-сессии из `check_phone_confirmation`.
            user_id: `USER_ID` выбранного адреса.
            device_id: Идентификатор устройства из `request_phone_confirmation`.
                Аргумент оставлен для совместимости; текущий API не требует его
                в `get-token` payload.

        Returns:
            Mobile access token.
        """
        payload = await self._client.request(
            "POST",
            endpoints.AUTH_GET_TOKEN,
            ClientRequestOptions(
                json_body={
                    "authId": auth_id,
                    "userId": str(user_id),
                }
            ),
        )
        token = MobileToken.from_json_object(normalize_json_object(payload))
        self._client.set_mobile_token(token.token)
        return token


class SyncAuthAPI:
    """Синхронная обертка домена авторизации IS74."""

    def __init__(self, client: IS74) -> None:
        """Создает синхронный домен авторизации.

        Args:
            client: Синхронный клиент верхнего уровня.
        """
        self._client = client

    def login_with_password(self, username: str, password: str) -> MobileToken:
        """Авторизуется по логину и паролю.

        Args:
            username: Логин учетной записи IS74.
            password: Пароль учетной записи IS74.

        Returns:
            Mobile access token.
        """
        return self._client._run(lambda client: client.auth.login_with_password(username, password))

    def request_phone_confirmation(
        self,
        phone: str,
        *,
        device_id: str | None = None,
    ) -> PhoneConfirmationStart:
        """Запрашивает код подтверждения для телефонной авторизации.

        Args:
            phone: Номер телефона. Можно передавать с `+7`, `7` или `8`.
            device_id: Идентификатор устройства. Если не передан, будет создан автоматически.

        Returns:
            Результат старта phone auth flow.
        """
        return self._client._run(
            lambda client: client.auth.request_phone_confirmation(phone, device_id=device_id)
        )

    def check_phone_confirmation(
        self,
        phone: str,
        code: str,
        *,
        device_id: str,
    ) -> PhoneConfirmationCheck:
        """Проверяет код подтверждения телефона.

        Args:
            phone: Номер телефона. Можно передавать с `+7`, `7` или `8`.
            code: Код из SMS или последние цифры номера входящего звонка.
            device_id: Идентификатор устройства из `request_phone_confirmation`.

        Returns:
            Результат проверки кода и список доступных адресов.
        """
        return self._client._run(
            lambda client: client.auth.check_phone_confirmation(phone, code, device_id=device_id)
        )

    def get_token_for_user(
        self,
        *,
        auth_id: str,
        user_id: int,
        device_id: str | None = None,
    ) -> MobileToken:
        """Получает mobile token для выбранного адреса пользователя.

        Args:
            auth_id: Идентификатор auth-сессии из `check_phone_confirmation`.
            user_id: `USER_ID` выбранного адреса.
            device_id: Идентификатор устройства из `request_phone_confirmation`.
                Аргумент оставлен для совместимости; текущий API не требует его
                в `get-token` payload.

        Returns:
            Mobile access token.
        """
        return self._client._run(
            lambda client: client.auth.get_token_for_user(
                auth_id=auth_id,
                user_id=user_id,
                device_id=device_id,
            )
        )


def generate_device_id() -> str:
    """Генерирует идентификатор устройства для phone auth flow.

    Returns:
        32-символьный hex UUID без дефисов.
    """
    return uuid.uuid4().hex


def normalize_phone(phone: str) -> str:
    """Нормализует российский телефон для API IS74.

    Args:
        phone: Номер телефона в пользовательском формате.

    Returns:
        Номер без `+7`, `7` или `8` в начале, если это 11-значный российский номер.
    """
    digits = "".join(char for char in phone if char.isdigit())
    if len(digits) == RUSSIAN_PHONE_WITH_COUNTRY_CODE_LENGTH and digits[0] in {"7", "8"}:
        return digits[1:]
    return digits
