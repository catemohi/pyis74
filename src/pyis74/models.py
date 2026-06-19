"""Типизированные модели ответов API IS74."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Self

from pyis74.exceptions import IS74APIError
from pyis74.types import JsonObject, JsonValue


@dataclass(frozen=True, slots=True)
class MobileToken:
    """Mobile access token API IS74.

    Args:
        token: Bearer-токен мобильного API.
        expires_at: Время истечения токена, если API его вернул.
        raw: Исходный JSON-ответ API.
    """

    token: str
    expires_at: datetime | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает модель токена из JSON-ответа API.

        Args:
            payload: JSON-ответ auth endpoint.

        Returns:
            Модель токена.

        Raises:
            IS74APIError: В ответе нет строкового поля `TOKEN`.
        """
        token = get_str(payload, "TOKEN") or get_str(payload, "token")
        if token is None:
            msg = "IS74 auth response does not contain TOKEN or token."
            raise IS74APIError(msg, payload)
        return cls(
            token=token,
            expires_at=parse_datetime(get_str(payload, "ACCESS_END")),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class PhoneConfirmationStart:
    """Результат запроса кода подтверждения по телефону.

    Args:
        device_id: Идентификатор устройства, использованный в auth flow.
        auth_id: Идентификатор auth-сессии, если API вернул его на этом шаге.
        raw: Исходный JSON-ответ API.
    """

    device_id: str
    auth_id: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject, *, device_id: str) -> Self:
        """Создает результат старта телефонной авторизации.

        Args:
            payload: JSON-ответ API.
            device_id: Идентификатор устройства, отправленный в API.

        Returns:
            Результат старта подтверждения.
        """
        return cls(device_id=device_id, auth_id=get_str(payload, "authId"), raw=payload)


@dataclass(frozen=True, slots=True)
class AddressCandidate:
    """Адрес, доступный для выбора после подтверждения телефона.

    Args:
        user_id: Идентификатор пользователя/адреса для получения токена.
        address: Человекочитаемый адрес, если API его вернул.
        raw: Исходный JSON-объект адреса.
    """

    user_id: int | None
    address: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает кандидата адреса из JSON.

        Args:
            payload: JSON-объект адреса.

        Returns:
            Модель адреса-кандидата.
        """
        return cls(
            user_id=get_int(payload, "USER_ID") or get_int(payload, "userId"),
            address=get_str(payload, "ADDRESS") or get_str(payload, "address"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class PhoneConfirmationCheck:
    """Результат проверки кода подтверждения.

    Args:
        auth_id: Идентификатор auth-сессии.
        addresses: Адреса, по которым можно получить access token.
        raw: Исходный JSON-ответ API.
    """

    auth_id: str
    addresses: tuple[AddressCandidate, ...]
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает результат проверки кода из JSON.

        Args:
            payload: JSON-ответ API.

        Returns:
            Результат проверки кода.

        Raises:
            IS74APIError: В ответе нет строкового поля `authId`.
        """
        auth_id = get_str(payload, "authId")
        if auth_id is None:
            msg = "IS74 phone confirmation response does not contain authId."
            raise IS74APIError(msg, payload)
        return cls(
            auth_id=auth_id,
            addresses=tuple(
                AddressCandidate.from_json_object(address)
                for address in get_json_object_list(payload, "addresses")
            ),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class ServiceStatus:
    """Статус сервисов IS74 для текущего пользователя.

    Args:
        status: Код статуса.
        description: Описание статуса.
        title: Заголовок статуса.
        deep_link: Deep link из ответа API.
        deep_link_text: Текст deep link.
        type_button: Тип кнопки из ответа API.
        raw: Исходный JSON-ответ API.
    """

    status: str | None
    description: str | None
    title: str | None
    deep_link: str | None
    deep_link_text: str | None
    type_button: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает статус сервиса из JSON.

        Args:
            payload: JSON-ответ API.

        Returns:
            Статус сервиса.
        """
        return cls(
            status=get_str(payload, "status"),
            description=get_str(payload, "description"),
            title=get_str(payload, "title"),
            deep_link=get_str(payload, "deep_link"),
            deep_link_text=get_str(payload, "deep_link_text"),
            type_button=get_str(payload, "type_button"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class UserInfo:
    """Информация о пользователе IS74.

    Args:
        user_id: Идентификатор пользователя.
        full_name: Полное имя.
        short_name: Короткое имя.
        login: Логин.
        account_number: Номер лицевого счета.
        birth_date: Дата рождения из ответа API.
        raw: Исходный JSON-ответ API.
    """

    user_id: int | None
    full_name: str | None
    short_name: str | None
    login: str | None
    account_number: int | None
    birth_date: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает пользователя из JSON.

        Args:
            payload: JSON-ответ API.

        Returns:
            Информация о пользователе.
        """
        return cls(
            user_id=get_int(payload, "USER_ID"),
            full_name=get_str(payload, "FULL_NAME"),
            short_name=get_str(payload, "shortFio"),
            login=get_str(payload, "LOGIN"),
            account_number=get_int(payload, "ACCOUNT_NUM"),
            birth_date=get_str(payload, "BIRTH_DATE"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class Address:
    """Адрес установки услуг IS74.

    Args:
        user_id: Идентификатор пользователя.
        flat_id: Идентификатор квартиры.
        building_id: Идентификатор дома.
        street_id: Идентификатор улицы.
        city_id: Идентификатор города.
        entrance_id: Идентификатор подъезда.
        raw: Исходный JSON-ответ API.
    """

    user_id: int | None
    flat_id: int | None
    building_id: int | None
    street_id: int | None
    city_id: int | None
    entrance_id: int | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает адрес из JSON.

        Args:
            payload: JSON-ответ API.

        Returns:
            Адрес установки услуг.
        """
        return cls(
            user_id=get_int(payload, "USER_ID"),
            flat_id=get_int(payload, "FLAT_ID"),
            building_id=get_int(payload, "BUILDING_ID"),
            street_id=get_int(payload, "STREET_ID"),
            city_id=get_int(payload, "CITY_ID"),
            entrance_id=get_int(payload, "PODJEZD_ID"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class NextPayment:
    """Информация о следующем платеже.

    Args:
        amount: Сумма следующего платежа.
        text: Описание платежа.
        raw: Исходный JSON-объект платежа.
    """

    amount: Decimal | None
    text: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает информацию о следующем платеже из JSON.

        Args:
            payload: JSON-объект платежа.

        Returns:
            Информация о следующем платеже.
        """
        return cls(amount=get_decimal(payload, "pay"), text=get_str(payload, "text"), raw=payload)


@dataclass(frozen=True, slots=True)
class Balance:
    """Баланс лицевого счета IS74.

    Args:
        balance: Текущий баланс.
        next_payment: Информация о следующем платеже.
        debt: Задолженность, если API ее вернул.
        blocked: Текст или код блокировки, если API его вернул.
        date_delay_lock: Дата отложенной блокировки.
        raw: Исходный JSON-ответ API.
    """

    balance: Decimal | None
    next_payment: NextPayment | None
    debt: Decimal | None
    blocked: str | None
    date_delay_lock: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает баланс из JSON.

        Args:
            payload: JSON-ответ API.

        Returns:
            Баланс лицевого счета.
        """
        next_payment_payload = get_json_object(payload, "nextPayment")
        return cls(
            balance=get_decimal(payload, "balance"),
            next_payment=(
                NextPayment.from_json_object(next_payment_payload)
                if next_payment_payload is not None
                else None
            ),
            debt=get_decimal(payload, "debt"),
            blocked=get_str(payload, "blocked"),
            date_delay_lock=get_str(payload, "dateDelayLock"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class AccountSummary:
    """Сводная информация по аккаунту IS74.

    Args:
        service_status: Статус сервисов.
        user: Информация о пользователе.
        address: Адрес установки услуг.
        balance: Баланс лицевого счета.
    """

    service_status: ServiceStatus
    user: UserInfo
    address: Address
    balance: Balance


@dataclass(frozen=True, slots=True)
class DomofonLinks:
    """Ссылки действий домофонного реле.

    Args:
        open_url: URL открытия двери, калитки или ворот.
        raw: Исходный JSON-объект ссылок.
    """

    open_url: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает ссылки домофонного реле из JSON.

        Args:
            payload: JSON-объект `LINKS`.

        Returns:
            Ссылки действий.
        """
        return cls(open_url=get_str(payload, "open"), raw=payload)


@dataclass(frozen=True, slots=True)
class DomofonOpener:
    """Параметры opener для домофонного реле.

    Args:
        mac: MAC-адрес контроллера.
        relay_id: Идентификатор реле.
        relay_num: Номер реле на контроллере.
        type: Тип opener из API, например `api` или `crm`.
        raw: Исходный JSON-объект opener.
    """

    mac: str | None
    relay_id: int | None
    relay_num: int | None
    type: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает opener из JSON.

        Args:
            payload: JSON-объект `OPENER`.

        Returns:
            Параметры opener.
        """
        return cls(
            mac=get_str(payload, "mac"),
            relay_id=get_int(payload, "relay_id"),
            relay_num=get_int(payload, "relay_num"),
            type=get_str(payload, "type"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class DomofonQrValue:
    """Параметры генерации QR-кода для домофона.

    Args:
        length: Длина кода.
        salt: Salt из API.
        step: Шаг обновления.
        window: Окно допустимости.
        raw: Исходный JSON-объект value.
    """

    length: int | None
    salt: str | None
    step: int | None
    window: int | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает параметры QR-кода из JSON.

        Args:
            payload: JSON-объект `QR_OPTIONS.value`.

        Returns:
            Параметры генерации QR-кода.
        """
        return cls(
            length=get_int(payload, "length"),
            salt=get_str(payload, "salt"),
            step=get_int(payload, "step"),
            window=get_int(payload, "window"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class DomofonQrOptions:
    """QR-настройки домофонного реле.

    Args:
        is_private: Признак приватного QR.
        last_change_date: Дата последнего изменения из API.
        name: Имя настройки.
        value: Параметры генерации QR-кода.
        raw: Исходный JSON-объект `QR_OPTIONS`.
    """

    is_private: bool | None
    last_change_date: str | None
    name: str | None
    value: DomofonQrValue | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает QR-настройки из JSON.

        Args:
            payload: JSON-объект `QR_OPTIONS`.

        Returns:
            QR-настройки.
        """
        value_payload = get_json_object(payload, "value")
        return cls(
            is_private=get_bool(payload, "isPrivate"),
            last_change_date=get_str(payload, "lastChangeDate"),
            name=get_str(payload, "name"),
            value=(
                DomofonQrValue.from_json_object(value_payload)
                if value_payload is not None
                else None
            ),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class DomofonRelay:
    """Домофонное реле, доступное пользователю.

    Args:
        relay_id: Идентификатор реле.
        relay_descr: Описание реле.
        relay_type: Тип реле, например главный вход, калитка или ворота.
        address: Человекочитаемый адрес.
        building_id: Идентификатор дома.
        entrance_uid: UID подъезда.
        has_video: Признак доступного видео.
        image_url: URL snapshot-изображения.
        is_main: Признак основного входа.
        smart_intercom: Признак умного домофона.
        mac_addr: MAC-адрес контроллера.
        porch_num: Номер подъезда.
        num_building: Номер дома из API.
        status_code: Код статуса.
        status_text: Текст статуса.
        links: Ссылки действий.
        opener: Параметры opener.
        qr_options: QR-настройки.
        raw: Исходный JSON-ответ API.
    """

    relay_id: int | None
    relay_descr: str | None
    relay_type: str | None
    address: str | None
    building_id: int | None
    entrance_uid: str | None
    has_video: bool | None
    image_url: str | None
    is_main: bool | None
    smart_intercom: bool | None
    mac_addr: str | None
    porch_num: str | None
    num_building: str | None
    status_code: str | None
    status_text: str | None
    links: DomofonLinks | None
    opener: DomofonOpener | None
    qr_options: DomofonQrOptions | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает домофонное реле из JSON.

        Args:
            payload: JSON-объект реле.

        Returns:
            Домофонное реле.
        """
        links_payload = get_json_object(payload, "LINKS")
        opener_payload = get_json_object(payload, "OPENER")
        qr_options_payload = get_json_object(payload, "QR_OPTIONS")
        return cls(
            relay_id=get_int(payload, "RELAY_ID"),
            relay_descr=get_str(payload, "RELAY_DESCR"),
            relay_type=get_str(payload, "RELAY_TYPE"),
            address=get_str(payload, "ADDRESS"),
            building_id=get_int(payload, "BUILDING_ID"),
            entrance_uid=get_str(payload, "ENTRANCE_UID"),
            has_video=get_bool(payload, "HAS_VIDEO"),
            image_url=get_str(payload, "IMAGE_URL"),
            is_main=get_bool(payload, "IS_MAIN"),
            smart_intercom=get_bool(payload, "SMART_INTERCOM"),
            mac_addr=get_str(payload, "MAC_ADDR"),
            porch_num=get_str(payload, "PORCH_NUM"),
            num_building=get_str(payload, "NUM_BUILDING"),
            status_code=get_str(payload, "STATUS_CODE"),
            status_text=get_str(payload, "STATUS_TEXT"),
            links=(
                DomofonLinks.from_json_object(links_payload) if links_payload is not None else None
            ),
            opener=(
                DomofonOpener.from_json_object(opener_payload)
                if opener_payload is not None
                else None
            ),
            qr_options=(
                DomofonQrOptions.from_json_object(qr_options_payload)
                if qr_options_payload is not None
                else None
            ),
            raw=payload,
        )

    @property
    def open_url(self) -> str | None:
        """Возвращает URL открытия из `LINKS.open`.

        Returns:
            URL открытия или `None`.
        """
        if self.links is None:
            return None
        return self.links.open_url


@dataclass(frozen=True, slots=True)
class DomofonOpenResult:
    """Результат открытия домофонного реле.

    Args:
        status_code: HTTP-код успешного ответа.
        payload: JSON-ответ, если API вернул JSON.
        response_text: Текст ответа API.
    """

    status_code: int
    payload: JsonValue | None
    response_text: str


def get_str(payload: JsonObject, key: str) -> str | None:
    """Возвращает строковое поле из JSON-объекта.

    Args:
        payload: JSON-объект.
        key: Ключ поля.

    Returns:
        Строка или `None`.
    """
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return None


def get_bool(payload: JsonObject, key: str) -> bool | None:
    """Возвращает булево поле из JSON-объекта.

    Args:
        payload: JSON-объект.
        key: Ключ поля.

    Returns:
        Булево значение или `None`.
    """
    value = payload.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n"}:
            return False
    return None


def get_int(payload: JsonObject, key: str) -> int | None:
    """Возвращает целочисленное поле из JSON-объекта.

    Args:
        payload: JSON-объект.
        key: Ключ поля.

    Returns:
        Целое число или `None`.
    """
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def get_decimal(payload: JsonObject, key: str) -> Decimal | None:
    """Возвращает числовое поле как `Decimal`.

    Args:
        payload: JSON-объект.
        key: Ключ поля.

    Returns:
        `Decimal` или `None`.
    """
    value = payload.get(key)
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float | str):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    return None


def get_json_object(payload: JsonObject, key: str) -> JsonObject | None:
    """Возвращает вложенный JSON-объект.

    Args:
        payload: JSON-объект.
        key: Ключ поля.

    Returns:
        Вложенный JSON-объект или `None`.
    """
    value = payload.get(key)
    if isinstance(value, dict):
        return value
    return None


def get_json_object_list(payload: JsonObject, key: str) -> tuple[JsonObject, ...]:
    """Возвращает список вложенных JSON-объектов.

    Args:
        payload: JSON-объект.
        key: Ключ поля.

    Returns:
        Кортеж JSON-объектов.
    """
    value = payload.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def parse_datetime(value: str | None) -> datetime | None:
    """Парсит дату API IS74 в timezone-aware `datetime`.

    Args:
        value: Строковое значение даты.

    Returns:
        `datetime` или `None`.
    """
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
