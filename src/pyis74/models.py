"""Типизированные модели ответов API IS74."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
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
class LkToken:
    """Access token личного кабинета CRM API.

    Args:
        token: Bearer-токен CRM/LK API.
        expires_at: Время истечения токена, если API его вернул.
        raw: Исходный JSON-ответ API.
    """

    token: str
    expires_at: datetime | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает модель CRM/LK token из JSON-ответа API.

        Args:
            payload: JSON-ответ `td-crm.is74.ru/api/auth-lk`.

        Returns:
            Модель CRM/LK token.

        Raises:
            IS74APIError: В ответе нет строкового поля `TOKEN` или `token`.
        """
        token = get_str(payload, "TOKEN") or get_str(payload, "token")
        if token is None:
            msg = "IS74 LK auth response does not contain TOKEN or token."
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


class HistoryEventKind(StrEnum):
    """Нормализованная категория события истории.

    Значение `event_type` из API остается доступным как есть, а `kind` нужен для
    пользовательских фильтров, которым не важно точное внутреннее имя события.
    """

    OPEN = "open"
    CALL = "call"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class HistoryEventParams:
    """Параметры события истории.

    Args:
        mac: MAC-адрес устройства, если API его вернул.
        address: Адрес события, если API его вернул.
        entrance_title: Описание подъезда или точки доступа.
        raw: Исходный JSON-объект `params`.
    """

    mac: str | None
    address: str | None
    entrance_title: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает параметры события истории из JSON.

        Args:
            payload: JSON-объект `params`.

        Returns:
            Параметры события.
        """
        return cls(
            mac=get_str(payload, "mac"),
            address=get_str(payload, "address"),
            entrance_title=get_str(payload, "entranceTitle"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class HistoryEvent:
    """Событие истории IS74.

    Args:
        create_date: Исходная дата события из API.
        created_at: Дата события в формате `datetime`, если ее удалось распарсить.
        event_type: Тип события, например `OPEN_API`, `OPEN_INTERNAL` или `HANDSET_CALL`.
        params: Параметры события.
        image_link: Ссылка на snapshot события, если API ее вернул.
        raw: Исходный JSON-объект события.
    """

    create_date: str | None
    created_at: datetime | None
    event_type: str | None
    params: HistoryEventParams | None
    image_link: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает событие истории из JSON.

        Args:
            payload: JSON-объект события.

        Returns:
            Событие истории.
        """
        params_payload = get_json_object(payload, "params")
        create_date = get_str(payload, "create_date")
        return cls(
            create_date=create_date,
            created_at=parse_datetime(create_date),
            event_type=get_str(payload, "type"),
            params=(
                HistoryEventParams.from_json_object(params_payload)
                if params_payload is not None
                else None
            ),
            image_link=get_str(payload, "image_link"),
            raw=payload,
        )

    @property
    def kind(self) -> HistoryEventKind:
        """Возвращает нормализованную категорию события.

        Returns:
            Категория события: открытие, звонок или другое событие.
        """
        return classify_history_event_type(self.event_type)

    @property
    def is_open(self) -> bool:
        """Проверяет, относится ли событие к открытию.

        Returns:
            `True`, если событие похоже на открытие.
        """
        return self.kind is HistoryEventKind.OPEN

    @property
    def is_call(self) -> bool:
        """Проверяет, относится ли событие к звонку.

        Returns:
            `True`, если событие похоже на звонок.
        """
        return self.kind is HistoryEventKind.CALL


@dataclass(frozen=True, slots=True)
class HistoryResponse:
    """Страница истории событий IS74.

    Args:
        events: События текущей страницы.
        page: Номер текущей страницы.
        per_page: Количество записей на странице.
        count: Общее количество записей.
        raw: Исходный JSON-ответ API.
    """

    events: tuple[HistoryEvent, ...]
    page: int | None
    per_page: int | None
    count: int | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает страницу истории из JSON.

        Args:
            payload: JSON-ответ `td-crm.is74.ru/api/user/history`.

        Returns:
            Страница истории событий.
        """
        return cls(
            events=tuple(
                HistoryEvent.from_json_object(event)
                for event in get_json_object_list(payload, "data")
            ),
            page=get_int(payload, "page"),
            per_page=get_int(payload, "perPage"),
            count=get_int(payload, "count"),
            raw=payload,
        )

    def filter_events(
        self,
        *,
        event_types: Iterable[str] = (),
        kinds: Iterable[HistoryEventKind | str] = (),
        with_images: bool | None = None,
    ) -> tuple[HistoryEvent, ...]:
        """Фильтрует события текущей страницы истории.

        Фильтрация выполняется локально по уже полученной странице. Поля `page`,
        `per_page`, `count` и `raw` остаются исходными свойствами ответа API.

        Args:
            event_types: Точные значения `HistoryEvent.event_type`, например `OPEN_API`.
            kinds: Нормализованные категории `open`, `call`, `other`.
            with_images: Если задано, фильтрует события по наличию `image_link`.

        Returns:
            Кортеж событий, подходящих под фильтры.
        """
        expected_event_types = {event_type.upper() for event_type in event_types}
        expected_kinds = {normalize_history_event_kind(kind) for kind in kinds}
        filtered_events: list[HistoryEvent] = []

        for event in self.events:
            event_type = event.event_type.upper() if event.event_type is not None else ""
            if expected_event_types and event_type not in expected_event_types:
                continue
            if expected_kinds and event.kind not in expected_kinds:
                continue
            if with_images is not None and bool(event.image_link) != with_images:
                continue
            filtered_events.append(event)

        return tuple(filtered_events)


def classify_history_event_type(event_type: str | None) -> HistoryEventKind:
    """Классифицирует исходный тип события истории.

    Args:
        event_type: Значение поля `type` из API.

    Returns:
        Нормализованная категория события.
    """
    if event_type is None:
        return HistoryEventKind.OTHER

    normalized = event_type.strip().upper()
    if "OPEN" in normalized:
        return HistoryEventKind.OPEN
    if "CALL" in normalized or "HANDSET" in normalized:
        return HistoryEventKind.CALL
    return HistoryEventKind.OTHER


def normalize_history_event_kind(value: HistoryEventKind | str) -> HistoryEventKind:
    """Нормализует пользовательское значение категории события.

    Args:
        value: `HistoryEventKind` или строка `open`, `call`, `other`.

    Returns:
        Нормализованная категория.

    Raises:
        ValueError: Значение не является известной категорией.
    """
    if isinstance(value, HistoryEventKind):
        return value

    normalized = value.strip().lower()
    for kind in HistoryEventKind:
        if kind.value == normalized:
            return kind

    msg = f"Unknown history event kind: {value!r}."
    raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class CameraAccessStatus:
    """Статус доступа к отдельной функции камеры.

    Args:
        status: Доступна ли функция.
        reason: Причина недоступности, если API ее вернул.
        audio: Доступен ли аудиопоток в архиве, если поле есть в ответе.
        raw: Исходный JSON-объект статуса.
    """

    status: bool | None
    reason: str | None
    audio: bool | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает статус доступа из JSON.

        Args:
            payload: JSON-объект статуса.

        Returns:
            Статус доступа.
        """
        return cls(
            status=get_bool(payload, "STATUS"),
            reason=get_str(payload, "REASON"),
            audio=get_bool(payload, "AUDIO"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraAccess:
    """Права доступа к функциям камеры.

    Args:
        live: Доступ к live-видео.
        archive: Доступ к архиву.
        movement: Доступ к событиям движения.
        download: Доступ к скачиванию архива.
        ptz: Доступ к PTZ.
        raw: Исходный JSON-объект `ACCESS`.
    """

    live: CameraAccessStatus | None
    archive: CameraAccessStatus | None
    movement: CameraAccessStatus | None
    download: CameraAccessStatus | None
    ptz: CameraAccessStatus | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает права доступа камеры из JSON.

        Args:
            payload: JSON-объект `ACCESS`.

        Returns:
            Права доступа камеры.
        """
        return cls(
            live=build_camera_access_status(payload, "LIVE"),
            archive=build_camera_access_status(payload, "ARCHIVE"),
            movement=build_camera_access_status(payload, "MOVEMENT"),
            download=build_camera_access_status(payload, "DOWNLOAD"),
            ptz=build_camera_access_status(payload, "PTZ"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraArchive:
    """Параметры архивного HLS-плейлиста камеры.

    Args:
        link: Относительная ссылка архива из API.
        start_time: Начало доступного архива в строковом формате API.
        stop_time: Конец доступного архива в строковом формате API.
        raw: Исходный JSON-объект `ARCHIVE`.
    """

    link: str | None
    start_time: str | None
    stop_time: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает параметры архива камеры из JSON.

        Args:
            payload: JSON-объект `ARCHIVE`.

        Returns:
            Параметры архива камеры.
        """
        return cls(
            link=get_str(payload, "LINK"),
            start_time=get_str(payload, "START_TIME"),
            stop_time=get_str(payload, "STOP_TIME"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraCoordinates:
    """Географические координаты камеры.

    Args:
        latitude: Широта как `Decimal`, если API вернул число или строку.
        longitude: Долгота как `Decimal`, если API вернул число или строку.
        raw: Исходный JSON-объект координат.
    """

    latitude: Decimal | None
    longitude: Decimal | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает координаты камеры из JSON.

        Args:
            payload: JSON-объект `COORDINATES`.

        Returns:
            Координаты камеры.
        """
        return cls(
            latitude=get_decimal(payload, "LATITUDE"),
            longitude=get_decimal(payload, "LONGITUDE"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraPosition:
    """Позиция и направление камеры.

    Args:
        azimuth: Азимут камеры.
        latitude: Широта как `Decimal`, если API вернул число или строку.
        longitude: Долгота как `Decimal`, если API вернул число или строку.
        raw: Исходный JSON-объект `POSITION`.
    """

    azimuth: int | None
    latitude: Decimal | None
    longitude: Decimal | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает позицию камеры из JSON.

        Args:
            payload: JSON-объект `POSITION`.

        Returns:
            Позиция камеры.
        """
        return cls(
            azimuth=get_int(payload, "AZIMUTH"),
            latitude=get_decimal(payload, "LATITUDE"),
            longitude=get_decimal(payload, "LONGITUDE"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraHlsLive:
    """Live HLS-ссылки камеры.

    Args:
        main: Основной HLS URL.
        low_latency: Low-latency HLS URL.
        raw: Исходный JSON-объект `MEDIA.HLS.LIVE`.
    """

    main: str | None
    low_latency: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает live HLS-ссылки из JSON.

        Args:
            payload: JSON-объект `MEDIA.HLS.LIVE`.

        Returns:
            Live HLS-ссылки.
        """
        return cls(
            main=get_str(payload, "MAIN"),
            low_latency=get_str(payload, "LOW_LATENCY"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraHlsMedia:
    """HLS media-ссылки камеры.

    Args:
        live: Live HLS-ссылки.
        archive: Архивный HLS URL.
        raw: Исходный JSON-объект `MEDIA.HLS`.
    """

    live: CameraHlsLive | None
    archive: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает HLS media-ссылки из JSON.

        Args:
            payload: JSON-объект `MEDIA.HLS`.

        Returns:
            HLS media-ссылки.
        """
        live_payload = get_json_object(payload, "LIVE")
        return cls(
            live=(
                CameraHlsLive.from_json_object(live_payload) if live_payload is not None else None
            ),
            archive=get_str(payload, "ARCHIVE"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraMseMedia:
    """MSE media-ссылки камеры.

    Args:
        live: Live MSE WebSocket URL.
        raw: Исходный JSON-объект `MEDIA.MSE`.
    """

    live: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает MSE media-ссылки из JSON.

        Args:
            payload: JSON-объект `MEDIA.MSE`.

        Returns:
            MSE media-ссылки.
        """
        return cls(live=get_str(payload, "LIVE"), raw=payload)


@dataclass(frozen=True, slots=True)
class CameraSnapshotLive:
    """Live snapshot-ссылки камеры.

    Args:
        main: Основной snapshot URL.
        lossy: Сжатый snapshot URL.
        raw: Исходный JSON-объект `MEDIA.SNAPSHOT.LIVE`.
    """

    main: str | None
    lossy: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает live snapshot-ссылки из JSON.

        Args:
            payload: JSON-объект `MEDIA.SNAPSHOT.LIVE`.

        Returns:
            Live snapshot-ссылки.
        """
        return cls(main=get_str(payload, "MAIN"), lossy=get_str(payload, "LOSSY"), raw=payload)


@dataclass(frozen=True, slots=True)
class CameraSnapshotMedia:
    """Snapshot media-ссылки камеры.

    Args:
        live: Live snapshot-ссылки.
        raw: Исходный JSON-объект `MEDIA.SNAPSHOT`.
    """

    live: CameraSnapshotLive | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает snapshot media-ссылки из JSON.

        Args:
            payload: JSON-объект `MEDIA.SNAPSHOT`.

        Returns:
            Snapshot media-ссылки.
        """
        live_payload = get_json_object(payload, "LIVE")
        return cls(
            live=(
                CameraSnapshotLive.from_json_object(live_payload)
                if live_payload is not None
                else None
            ),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraMedia:
    """Media-ссылки камеры.

    Args:
        hls: HLS-ссылки.
        mse: MSE-ссылки.
        snapshot: Snapshot-ссылки.
        raw: Исходный JSON-объект `MEDIA`.
    """

    hls: CameraHlsMedia | None
    mse: CameraMseMedia | None
    snapshot: CameraSnapshotMedia | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает media-ссылки камеры из JSON.

        Args:
            payload: JSON-объект `MEDIA`.

        Returns:
            Media-ссылки камеры.
        """
        hls_payload = get_json_object(payload, "HLS")
        mse_payload = get_json_object(payload, "MSE")
        snapshot_payload = get_json_object(payload, "SNAPSHOT")
        return cls(
            hls=CameraHlsMedia.from_json_object(hls_payload) if hls_payload is not None else None,
            mse=CameraMseMedia.from_json_object(mse_payload) if mse_payload is not None else None,
            snapshot=(
                CameraSnapshotMedia.from_json_object(snapshot_payload)
                if snapshot_payload is not None
                else None
            ),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraSnapshot:
    """Относительные snapshot-пути камеры.

    Args:
        hd: HD snapshot path.
        lossy: Сжатый snapshot path.
        raw: Исходный JSON-объект `SNAPSHOT`.
    """

    hd: str | None
    lossy: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает относительные snapshot-пути из JSON.

        Args:
            payload: JSON-объект `SNAPSHOT`.

        Returns:
            Относительные snapshot-пути.
        """
        return cls(hd=get_str(payload, "HD"), lossy=get_str(payload, "LOSSY"), raw=payload)


@dataclass(frozen=True, slots=True)
class CameraRealtimeWs:
    """Realtime WebSocket-ссылки камеры.

    Args:
        combined: Общий WebSocket URL.
        main: Main-quality WebSocket URL.
        sub: Sub-quality WebSocket URL.
        raw: Исходный JSON-объект `REALTIME_WS`.
    """

    combined: str | None
    main: str | None
    sub: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает realtime WebSocket-ссылки из JSON.

        Args:
            payload: JSON-объект `REALTIME_WS`.

        Returns:
            Realtime WebSocket-ссылки.
        """
        return cls(
            combined=get_str(payload, "combined"),
            main=get_str(payload, "main"),
            sub=get_str(payload, "sub"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraSupportedFeatures:
    """Поддерживаемые функции камеры.

    Args:
        doorbell: Поддержка doorbell.
        ptz: Поддержка PTZ.
        setup_motion_detect: Можно ли настраивать детекцию движения.
        voice: Поддержка голоса.
        zoom: Поддержка zoom.
        raw: Исходный JSON-объект `SUPPORTED_FEATURES`.
    """

    doorbell: bool | None
    ptz: bool | None
    setup_motion_detect: bool | None
    voice: bool | None
    zoom: bool | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает поддерживаемые функции камеры из JSON.

        Args:
            payload: JSON-объект `SUPPORTED_FEATURES`.

        Returns:
            Поддерживаемые функции камеры.
        """
        return cls(
            doorbell=get_bool(payload, "doorbell"),
            ptz=get_bool(payload, "ptz"),
            setup_motion_detect=get_bool(payload, "setup_motion_detect"),
            voice=get_bool(payload, "voice"),
            zoom=get_bool(payload, "zoom"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraVaFeatures:
    """Функции видеоаналитики камеры.

    Args:
        annotation: Доступность annotation.
        raw: Исходный JSON-объект `VA_FEATURES`.
    """

    annotation: bool | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает функции видеоаналитики из JSON.

        Args:
            payload: JSON-объект `VA_FEATURES`.

        Returns:
            Функции видеоаналитики.
        """
        return cls(annotation=get_bool(payload, "annotation"), raw=payload)


@dataclass(frozen=True, slots=True)
class CameraStreams:
    """Собранные media URL камеры.

    Args:
        hls_live_main: Основной live HLS URL.
        hls_live_low_latency: Low-latency live HLS URL.
        hls_archive: Архивный HLS URL.
        mse_live: Live MSE WebSocket URL.
        snapshot_live_main: Основной live snapshot URL.
        snapshot_live_lossy: Сжатый live snapshot URL.
        realtime_ws_combined: Общий realtime WebSocket URL.
        realtime_ws_main: Main-quality realtime WebSocket URL.
        realtime_ws_sub: Sub-quality realtime WebSocket URL.
    """

    hls_live_main: str | None
    hls_live_low_latency: str | None
    hls_archive: str | None
    mse_live: str | None
    snapshot_live_main: str | None
    snapshot_live_lossy: str | None
    realtime_ws_combined: str | None
    realtime_ws_main: str | None
    realtime_ws_sub: str | None

    @classmethod
    def from_camera(cls, camera: Camera) -> Self:
        """Собирает stream URL из вложенных полей камеры.

        Args:
            camera: Камера IS74.

        Returns:
            Компактная модель stream URL.
        """
        hls_live_main: str | None = None
        hls_live_low_latency: str | None = None
        hls_archive: str | None = None
        mse_live: str | None = None
        snapshot_live_main: str | None = None
        snapshot_live_lossy: str | None = None
        realtime_ws_combined: str | None = None
        realtime_ws_main: str | None = None
        realtime_ws_sub: str | None = None

        if camera.media is not None:
            if camera.media.hls is not None:
                hls_archive = camera.media.hls.archive
                if camera.media.hls.live is not None:
                    hls_live_main = camera.media.hls.live.main
                    hls_live_low_latency = camera.media.hls.live.low_latency
            if camera.media.mse is not None:
                mse_live = camera.media.mse.live
            if camera.media.snapshot is not None and camera.media.snapshot.live is not None:
                snapshot_live_main = camera.media.snapshot.live.main
                snapshot_live_lossy = camera.media.snapshot.live.lossy

        if camera.realtime_ws is not None:
            realtime_ws_combined = camera.realtime_ws.combined
            realtime_ws_main = camera.realtime_ws.main
            realtime_ws_sub = camera.realtime_ws.sub

        return cls(
            hls_live_main=hls_live_main,
            hls_live_low_latency=hls_live_low_latency,
            hls_archive=hls_archive,
            mse_live=mse_live,
            snapshot_live_main=snapshot_live_main,
            snapshot_live_lossy=snapshot_live_lossy,
            realtime_ws_combined=realtime_ws_combined,
            realtime_ws_main=realtime_ws_main,
            realtime_ws_sub=realtime_ws_sub,
        )

    @property
    def has_any(self) -> bool:
        """Проверяет, есть ли хотя бы один URL.

        Returns:
            `True`, если модель содержит хотя бы один URL.
        """
        return bool(self.items())

    def items(self) -> tuple[tuple[str, str], ...]:
        """Возвращает непустые URL с устойчивыми именами полей.

        Returns:
            Кортеж пар `имя поля`, `URL`.
        """
        stream_items: list[tuple[str, str]] = []
        for name, value in (
            ("hls.live.main", self.hls_live_main),
            ("hls.live.low_latency", self.hls_live_low_latency),
            ("hls.archive", self.hls_archive),
            ("mse.live", self.mse_live),
            ("snapshot.live.main", self.snapshot_live_main),
            ("snapshot.live.lossy", self.snapshot_live_lossy),
            ("realtime_ws.combined", self.realtime_ws_combined),
            ("realtime_ws.main", self.realtime_ws_main),
            ("realtime_ws.sub", self.realtime_ws_sub),
        ):
            if value:
                stream_items.append((name, value))
        return tuple(stream_items)


@dataclass(frozen=True, slots=True)
class Camera:
    """Камера IS74.

    Args:
        camera_id: Идентификатор камеры из поля `ID`.
        uuid: UUID камеры.
        object_type: Тип объекта, обычно `CAMERA`.
        name: Название камеры.
        short_name: Короткое название камеры.
        address: Адрес камеры.
        porch: Номер подъезда или `None`.
        hls: Относительный HLS path.
        realtime_hls: Относительный realtime HLS path.
        link_to_admin: Ссылка на админку, если доступна.
        sleep_mode: Состояние sleep mode, если API его вернул.
        stream_exists: Состояние stream exists, если API его вернул.
        access: Права доступа.
        archive: Параметры архива.
        coordinates: Географические координаты.
        media: Абсолютные media-ссылки.
        position: Позиция и направление.
        realtime_ws: Realtime WebSocket-ссылки.
        snapshot: Относительные snapshot-пути.
        supported_features: Поддерживаемые функции.
        va_features: Функции видеоаналитики.
        raw: Исходный JSON-объект камеры.
    """

    camera_id: int | None
    uuid: str | None
    object_type: str | None
    name: str | None
    short_name: str | None
    address: str | None
    porch: str | None
    hls: str | None
    realtime_hls: str | None
    link_to_admin: str | None
    sleep_mode: JsonValue | None
    stream_exists: JsonValue | None
    access: CameraAccess | None
    archive: CameraArchive | None
    coordinates: CameraCoordinates | None
    media: CameraMedia | None
    position: CameraPosition | None
    realtime_ws: CameraRealtimeWs | None
    snapshot: CameraSnapshot | None
    supported_features: CameraSupportedFeatures | None
    va_features: CameraVaFeatures | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает камеру из JSON.

        Args:
            payload: JSON-объект камеры.

        Returns:
            Камера.
        """
        access_payload = get_json_object(payload, "ACCESS")
        archive_payload = get_json_object(payload, "ARCHIVE")
        coordinates_payload = get_json_object(payload, "COORDINATES")
        media_payload = get_json_object(payload, "MEDIA")
        position_payload = get_json_object(payload, "POSITION")
        realtime_ws_payload = get_json_object(payload, "REALTIME_WS")
        snapshot_payload = get_json_object(payload, "SNAPSHOT")
        supported_features_payload = get_json_object(payload, "SUPPORTED_FEATURES")
        va_features_payload = get_json_object(payload, "VA_FEATURES")
        return cls(
            camera_id=get_int(payload, "ID"),
            uuid=get_str(payload, "UUID"),
            object_type=get_str(payload, "OBJECT"),
            name=get_str(payload, "NAME"),
            short_name=get_str(payload, "SHORT_NAME"),
            address=get_str(payload, "ADDRESS"),
            porch=get_str(payload, "PORCH"),
            hls=get_str(payload, "HLS"),
            realtime_hls=get_str(payload, "REALTIME_HLS"),
            link_to_admin=get_str(payload, "LINK_TO_ADMIN"),
            sleep_mode=payload.get("SLEEP_MODE"),
            stream_exists=payload.get("STREAM_EXISTS"),
            access=(
                CameraAccess.from_json_object(access_payload)
                if access_payload is not None
                else None
            ),
            archive=(
                CameraArchive.from_json_object(archive_payload)
                if archive_payload is not None
                else None
            ),
            coordinates=(
                CameraCoordinates.from_json_object(coordinates_payload)
                if coordinates_payload is not None
                else None
            ),
            media=CameraMedia.from_json_object(media_payload)
            if media_payload is not None
            else None,
            position=(
                CameraPosition.from_json_object(position_payload)
                if position_payload is not None
                else None
            ),
            realtime_ws=(
                CameraRealtimeWs.from_json_object(realtime_ws_payload)
                if realtime_ws_payload is not None
                else None
            ),
            snapshot=(
                CameraSnapshot.from_json_object(snapshot_payload)
                if snapshot_payload is not None
                else None
            ),
            supported_features=(
                CameraSupportedFeatures.from_json_object(supported_features_payload)
                if supported_features_payload is not None
                else None
            ),
            va_features=(
                CameraVaFeatures.from_json_object(va_features_payload)
                if va_features_payload is not None
                else None
            ),
            raw=payload,
        )

    @property
    def streams(self) -> CameraStreams:
        """Возвращает собранные stream URL камеры.

        Returns:
            Компактная модель stream/snapshot/WebSocket URL.
        """
        return CameraStreams.from_camera(self)


@dataclass(frozen=True, slots=True)
class CameraGroup:
    """Группа камер IS74.

    Args:
        group_id: Идентификатор группы как строка.
        name: Название группы.
        object_type: Тип объекта, обычно `GROUP`.
        raw: Исходный JSON-объект группы.
    """

    group_id: str | None
    name: str | None
    object_type: str | None
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает группу камер из JSON.

        Args:
            payload: JSON-объект группы.

        Returns:
            Группа камер.
        """
        return cls(
            group_id=get_str_id(payload, "ID") or get_str_id(payload, "id"),
            name=get_str(payload, "NAME") or get_str(payload, "groupName"),
            object_type=get_str(payload, "OBJECT"),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class SelfCameraGroup:
    """Группа камер пользователя из `/self-cams-with-group`.

    Args:
        group_id: Идентификатор группы как строка.
        group_name: Название группы.
        is_management_company_owns: Признак принадлежности УК.
        cameras: Камеры внутри группы.
        raw: Исходный JSON-объект группы.
    """

    group_id: str | None
    group_name: str | None
    is_management_company_owns: bool | None
    cameras: tuple[Camera, ...]
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает группу камер пользователя из JSON.

        Args:
            payload: JSON-объект группы из `/self-cams-with-group`.

        Returns:
            Группа камер пользователя.
        """
        return cls(
            group_id=get_str_id(payload, "id"),
            group_name=get_str(payload, "groupName"),
            is_management_company_owns=get_bool(payload, "isManagementCompanyOwns"),
            cameras=tuple(
                Camera.from_json_object(camera)
                for camera in get_json_object_list(payload, "cameras")
            ),
            raw=payload,
        )


@dataclass(frozen=True, slots=True)
class CameraGroupContent:
    """Содержимое группы камер.

    Args:
        groups: Дочерние группы.
        cameras: Камеры группы.
        raw: Исходный JSON-ответ `get-group/{id}`.
    """

    groups: tuple[CameraGroup, ...]
    cameras: tuple[Camera, ...]
    raw: JsonValue


@dataclass(frozen=True, slots=True)
class CameraLimitedInfo:
    """Ответ `/api/limited-info-by-uuid`.

    Args:
        cameras: Камеры, найденные по переданным UUID.
        raw: Исходный JSON-объект ответа.
    """

    cameras: tuple[Camera, ...]
    raw: JsonObject

    @classmethod
    def from_json_object(cls, payload: JsonObject) -> Self:
        """Создает limited-info ответ из JSON.

        Args:
            payload: JSON-объект, где ключами обычно являются id камер.

        Returns:
            Limited-info ответ.
        """
        cameras = tuple(
            Camera.from_json_object(item) for item in payload.values() if isinstance(item, dict)
        )
        return cls(cameras=cameras, raw=payload)


@dataclass(frozen=True, slots=True)
class DomofonRelayCameras:
    """Связка домофонного реле и найденных для него камер.

    Args:
        relay: Домофонное реле.
        cameras: Камеры, найденные по `relay.entrance_uid`.
    """

    relay: DomofonRelay
    cameras: tuple[Camera, ...]


def build_camera_access_status(payload: JsonObject, key: str) -> CameraAccessStatus | None:
    """Создает статус доступа камеры из вложенного объекта.

    Args:
        payload: JSON-объект `ACCESS`.
        key: Ключ вложенного статуса.

    Returns:
        Статус доступа или `None`.
    """
    status_payload = get_json_object(payload, key)
    if status_payload is None:
        return None
    return CameraAccessStatus.from_json_object(status_payload)


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


def get_str_id(payload: JsonObject, key: str) -> str | None:
    """Возвращает строковое представление id из JSON-объекта.

    Args:
        payload: JSON-объект.
        key: Ключ поля id.

    Returns:
        Строковый id или `None`.
    """
    value = payload.get(key)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | str):
        return str(value)
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
