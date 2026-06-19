"""Методы получения данных аккаунта IS74."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyis74 import endpoints
from pyis74.models import AccountSummary, Address, Balance, ServiceStatus, UserInfo
from pyis74.options import ClientRequestOptions
from pyis74.types import normalize_json_object

if TYPE_CHECKING:
    from pyis74.client import IS74, IS74Async


class AccountAPI:
    """Асинхронный домен данных аккаунта IS74."""

    def __init__(self, client: IS74Async) -> None:
        """Создает домен аккаунта.

        Args:
            client: Асинхронный клиент верхнего уровня.
        """
        self._client = client

    async def get_service_status(self) -> ServiceStatus:
        """Возвращает статус сервисов текущего пользователя.

        Returns:
            Статус сервисов.
        """
        payload = await self._client.request_mobile("GET", endpoints.USER_STATUS)
        return ServiceStatus.from_json_object(normalize_json_object(payload))

    async def get_user(self) -> UserInfo:
        """Возвращает информацию о текущем пользователе.

        Returns:
            Информация о пользователе.
        """
        payload = await self._client.request_mobile("GET", endpoints.USER_INFO)
        return UserInfo.from_json_object(normalize_json_object(payload))

    async def get_address(self) -> Address:
        """Возвращает адрес установки услуг текущего пользователя.

        Returns:
            Адрес установки услуг.
        """
        payload = await self._client.request_mobile("GET", endpoints.USER_ADDRESS)
        return Address.from_json_object(normalize_json_object(payload))

    async def get_balance(self) -> Balance:
        """Возвращает баланс лицевого счета текущего пользователя.

        Returns:
            Баланс лицевого счета.
        """
        payload = await self._client.request_mobile(
            "GET",
            endpoints.USER_BALANCE,
            ClientRequestOptions(headers={"Accept": "application/json; version=v2"}),
        )
        return Balance.from_json_object(normalize_json_object(payload))

    async def get_summary(self) -> AccountSummary:
        """Возвращает сводную информацию аккаунта.

        Returns:
            Статус сервисов, пользователь, адрес и баланс.
        """
        return AccountSummary(
            service_status=await self.get_service_status(),
            user=await self.get_user(),
            address=await self.get_address(),
            balance=await self.get_balance(),
        )


class SyncAccountAPI:
    """Синхронная обертка домена данных аккаунта IS74."""

    def __init__(self, client: IS74) -> None:
        """Создает синхронный домен аккаунта.

        Args:
            client: Синхронный клиент верхнего уровня.
        """
        self._client = client

    def get_service_status(self) -> ServiceStatus:
        """Возвращает статус сервисов текущего пользователя.

        Returns:
            Статус сервисов.
        """
        return self._client._run(lambda client: client.account.get_service_status())

    def get_user(self) -> UserInfo:
        """Возвращает информацию о текущем пользователе.

        Returns:
            Информация о пользователе.
        """
        return self._client._run(lambda client: client.account.get_user())

    def get_address(self) -> Address:
        """Возвращает адрес установки услуг текущего пользователя.

        Returns:
            Адрес установки услуг.
        """
        return self._client._run(lambda client: client.account.get_address())

    def get_balance(self) -> Balance:
        """Возвращает баланс лицевого счета текущего пользователя.

        Returns:
            Баланс лицевого счета.
        """
        return self._client._run(lambda client: client.account.get_balance())

    def get_summary(self) -> AccountSummary:
        """Возвращает сводную информацию аккаунта.

        Returns:
            Статус сервисов, пользователь, адрес и баланс.
        """
        return self._client._run(lambda client: client.account.get_summary())
