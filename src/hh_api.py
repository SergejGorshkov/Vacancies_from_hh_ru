import requests

from src.base_job_api import JobAPI


class HeadHunterAPI(JobAPI):
    """Класс для поиска вакансий на платформе hh.ru"""
    VACANCIES_URL = "https://api.hh.ru/vacancies"  # URL для поиска вакансий

    page: int  # Количество вакансий для поиска (по умолчанию 100)
    params: dict  # Параметры для GET-запроса по API hh.ru

    def __init__(self) -> None:
        """Метод-конструктор для инициализации экземпляров класса HeadHunterAPI. Определение значений атрибутов экземпляров."""
        self.__session = None  # На начало работы программы ответа от сервера еще нет

    def _connect(self, params):
        """Метод подключения к API (защищенный)"""
        # Валидация данных перед выполнением GET-запроса
        if not isinstance(params, dict):
            raise ValueError("Неверный тип данных у атрибута 'params'.")

        with requests.Session() as self.__session:  # Для закрытия сессии после завершения работы с ней
            response = self.__session.get(self.VACANCIES_URL,
                                          params=params)  # API-запрос на получение информации по вакансиям от hh.ru

            if response.status_code != 200:  # Если запрос неудачный...
                raise ValueError(
                    f"Неудачная попытка API-запроса по адресу '{self.VACANCIES_URL}'. Возможная причина: "
                    f"{response.reason}.")

            return response  # Возврат ответа от API, если запрос удачный

    def get_vacancies(self, company_ids: list[str], page=100) -> list[dict] | None:
        """Метод получения вакансий по id организаций (на hh.ru).
        Принимает список id номеров компаний.
        Возвращает список словарей с данными о вакансиях."""
        if not isinstance(company_ids, list):
            raise TypeError("Неверный тип данных у параметров запроса вакансий.")

        # Параметры GET-запроса
        params = {
            "employer_id": company_ids,
            "per_page": page,
        }
        result = self._connect(params).json()  # Преобразование ответа от API в формат JSON

        # Возврат содержимого ключа "items" (только список словарей с вакансиями без вспомогательной информации)
        return result.get("items", [])


# ###################################################################################################
# Код для проверки:
# COMPANY_IDS = ["4306244",  # "VICTORY_group"
#                "67611",  # "Тензор"
#                "41862",  # "Контур"
#                "1429999",  # "Циан"
#                "906557",  # "SberTec"
#                "1740",  # "Яндекс"
#                "78638",  # "Т-Банк"
#                "4181",  # "ПАО ВТБ"
#                "10246537",  # "Кибертех"
#                "3529"  # "СБЕР"
#                ]
# hh_api = HeadHunterAPI()
# vacancies = hh_api.get_vacancies(COMPANY_IDS)
# print(vacancies)
