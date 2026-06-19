"""Методы работы с камерами IS74."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from pyis74 import endpoints
from pyis74.exceptions import IS74APIError
from pyis74.models import (
    Camera,
    CameraGroup,
    CameraGroupContent,
    CameraLimitedInfo,
    SelfCameraGroup,
)
from pyis74.options import ClientRequestOptions
from pyis74.types import JsonObject, JsonValue, normalize_json_object

if TYPE_CHECKING:
    from pyis74.client import IS74, IS74Async

FORM_HEADERS: dict[str, str] = {"Content-Type": "application/x-www-form-urlencoded"}


class CamerasAPI:
    """Асинхронный домен камер IS74."""

    def __init__(self, client: IS74Async) -> None:
        """Создает домен камер.

        Args:
            client: Асинхронный клиент верхнего уровня.
        """
        self._client = client

    async def get_self_cams_with_group(self) -> tuple[SelfCameraGroup, ...]:
        """Возвращает группы камер, доступные текущему пользователю.

        Returns:
            Кортеж групп камер пользователя.
        """
        payload = await self._client.request_mobile("GET", endpoints.CAMS_SELF_WITH_GROUP)
        return parse_self_camera_groups(payload)

    async def get_groups(self, *, self_cams: bool = False) -> tuple[CameraGroup, ...]:
        """Возвращает список групп camera API.

        Args:
            self_cams: Добавить query-параметр `selfCams=true`.

        Returns:
            Кортеж групп камер.
        """
        payload = await self._client.request_mobile(
            "GET",
            endpoints.CAMS_GET_GROUP,
            ClientRequestOptions(params={"selfCams": True} if self_cams else None),
        )
        return parse_camera_groups(payload)

    async def get_group(self, group_id: int | str) -> CameraGroupContent:
        """Возвращает содержимое группы камер.

        Endpoint может вернуть смешанный список: дочерние группы и камеры. Поэтому метод
        возвращает контейнер с раздельными `groups` и `cameras`.

        Args:
            group_id: ID группы из `get_groups()` или `get_self_cams_with_group()`.

        Returns:
            Содержимое группы камер.
        """
        payload = await self._client.request_mobile("GET", build_group_url(group_id))
        return parse_camera_group_content(payload)

    async def get_limited_info_by_uuid(self, camera_uuid: str) -> CameraLimitedInfo:
        """Возвращает limited camera info по одному UUID.

        Args:
            camera_uuid: UUID камеры или подъезда из `ENTRANCE_UID`.

        Returns:
            Limited-info ответ с найденными камерами.
        """
        return await self.get_limited_info_by_uuids((camera_uuid,))

    async def get_limited_info_by_uuids(self, camera_uuids: Iterable[str]) -> CameraLimitedInfo:
        """Возвращает limited camera info по набору UUID.

        Args:
            camera_uuids: UUID камер или подъездов.

        Returns:
            Limited-info ответ с найденными камерами.
        """
        uuids = tuple(camera_uuid for camera_uuid in camera_uuids if camera_uuid)
        if not uuids:
            return CameraLimitedInfo(cameras=(), raw={})

        payload = await self._client.request_mobile(
            "POST",
            endpoints.CAMS_LIMITED_INFO_BY_UUID,
            ClientRequestOptions(
                headers=FORM_HEADERS,
                content=urlencode([("CAMERA_UUIDS[]", camera_uuid) for camera_uuid in uuids]),
            ),
        )
        try:
            info_payload = normalize_json_object(payload)
        except TypeError as error:
            msg = "IS74 camera limited-info response is not an object."
            raise IS74APIError(msg, payload) from error
        return CameraLimitedInfo.from_json_object(info_payload)


class SyncCamerasAPI:
    """Синхронная обертка домена камер IS74."""

    def __init__(self, client: IS74) -> None:
        """Создает синхронный домен камер.

        Args:
            client: Синхронный клиент верхнего уровня.
        """
        self._client = client

    def get_self_cams_with_group(self) -> tuple[SelfCameraGroup, ...]:
        """Возвращает группы камер, доступные текущему пользователю.

        Returns:
            Кортеж групп камер пользователя.
        """
        return self._client._run(lambda client: client.cameras.get_self_cams_with_group())

    def get_groups(self, *, self_cams: bool = False) -> tuple[CameraGroup, ...]:
        """Возвращает список групп camera API.

        Args:
            self_cams: Добавить query-параметр `selfCams=true`.

        Returns:
            Кортеж групп камер.
        """
        return self._client._run(lambda client: client.cameras.get_groups(self_cams=self_cams))

    def get_group(self, group_id: int | str) -> CameraGroupContent:
        """Возвращает содержимое группы камер.

        Args:
            group_id: ID группы из `get_groups()` или `get_self_cams_with_group()`.

        Returns:
            Содержимое группы камер.
        """
        return self._client._run(lambda client: client.cameras.get_group(group_id))

    def get_limited_info_by_uuid(self, camera_uuid: str) -> CameraLimitedInfo:
        """Возвращает limited camera info по одному UUID.

        Args:
            camera_uuid: UUID камеры или подъезда из `ENTRANCE_UID`.

        Returns:
            Limited-info ответ с найденными камерами.
        """
        return self._client._run(
            lambda client: client.cameras.get_limited_info_by_uuid(camera_uuid)
        )

    def get_limited_info_by_uuids(self, camera_uuids: Iterable[str]) -> CameraLimitedInfo:
        """Возвращает limited camera info по набору UUID.

        Args:
            camera_uuids: UUID камер или подъездов.

        Returns:
            Limited-info ответ с найденными камерами.
        """
        uuids = tuple(camera_uuid for camera_uuid in camera_uuids if camera_uuid)
        return self._client._run(lambda client: client.cameras.get_limited_info_by_uuids(uuids))


def parse_self_camera_groups(payload: JsonValue) -> tuple[SelfCameraGroup, ...]:
    """Разбирает ответ `/api/self-cams-with-group`.

    Args:
        payload: JSON-ответ camera API.

    Returns:
        Группы камер пользователя.

    Raises:
        IS74APIError: Ответ не является списком объектов.
    """
    return tuple(
        SelfCameraGroup.from_json_object(item)
        for item in require_json_object_list(payload, "self-cams-with-group")
    )


def parse_camera_groups(payload: JsonValue) -> tuple[CameraGroup, ...]:
    """Разбирает ответ `/api/get-group/`.

    Args:
        payload: JSON-ответ camera API.

    Returns:
        Группы камер.

    Raises:
        IS74APIError: Ответ не является списком объектов.
    """
    return tuple(
        CameraGroup.from_json_object(item)
        for item in require_json_object_list(payload, "camera groups")
    )


def parse_camera_group_content(payload: JsonValue) -> CameraGroupContent:
    """Разбирает смешанный ответ `/api/get-group/{id}`.

    Args:
        payload: JSON-ответ camera API.

    Returns:
        Содержимое группы камер.

    Raises:
        IS74APIError: Ответ не является списком объектов.
    """
    groups: list[CameraGroup] = []
    cameras: list[Camera] = []
    for item in require_json_object_list(payload, "camera group content"):
        object_type = item.get("OBJECT")
        if object_type == "GROUP":
            groups.append(CameraGroup.from_json_object(item))
        elif object_type == "CAMERA":
            cameras.append(Camera.from_json_object(item))
    return CameraGroupContent(groups=tuple(groups), cameras=tuple(cameras), raw=payload)


def require_json_object_list(payload: JsonValue, response_name: str) -> tuple[JsonObject, ...]:
    """Проверяет, что ответ является списком JSON-объектов.

    Args:
        payload: JSON-ответ API.
        response_name: Название ответа для сообщения об ошибке.

    Returns:
        Кортеж JSON-объектов.

    Raises:
        IS74APIError: Ответ не является списком объектов.
    """
    if not isinstance(payload, list):
        msg = f"IS74 {response_name} response is not a list."
        raise IS74APIError(msg, payload)

    items: list[JsonObject] = []
    for item in payload:
        try:
            items.append(normalize_json_object(item))
        except TypeError as error:
            msg = f"IS74 {response_name} response contains non-object item."
            raise IS74APIError(msg, payload) from error
    return tuple(items)


def build_group_url(group_id: int | str) -> str:
    """Собирает URL детального просмотра группы камер.

    Args:
        group_id: ID группы.

    Returns:
        Абсолютный URL `cams.is74.ru/api/get-group/{group_id}`.
    """
    return f"{endpoints.CAMS_GET_GROUP.rstrip('/')}/{group_id}"
