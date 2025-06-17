import requests

from src.base_job_api import JobAPI


class HeadHunterAPI(JobAPI):
    """Класс для поиска вакансий на платформе hh.ru"""
    VACANCIES_URL = "https://api.hh.ru/vacancies"  # URL для поиска вакансий

    per_page: int  # Количество вакансий для поиска (по умолчанию 100)
    params: dict  # Параметры для GET-запроса по API hh.ru
    company_ids: list[str]  # список id компаний на hh.ru

    def __init__(self) -> None:
        """Метод-конструктор для инициализации экземпляров класса HeadHunterAPI.
        Определение значений атрибутов экземпляров."""
        self.__session = None  # На начало работы программы ответа от сервера еще нет

    def get_vacancies(self, company_ids, per_page=100) -> list:
        """Метод получения вакансий по id организаций (на hh.ru).
        Принимает список id номеров компаний.
        Возвращает список словарей с данными о вакансиях."""

        if not isinstance(company_ids, list):
            raise TypeError("Неверный тип данных у параметров запроса вакансий.")

        page = 0  # Первая страница в запросе
        data = []  # Список для сохранения данных

        with requests.Session() as self.__session:  # Для закрытия сессии после завершения работы с ней

            # Цикл для получения всех данных от API hh.ru (пагинация)
            while True:
                # Параметры GET-запроса
                params = {
                    "employer_id": company_ids,
                    "per_page": per_page,  # Максимальное количество вакансий на странице
                    "page": page,  # Текущий номер страницы в запросе
                }

                # API-запрос на получение информации по вакансиям от hh.ru
                response = self.__session.get(self.VACANCIES_URL, params=params)
                if response.status_code != 200:  # Если запрос неудачный...
                    raise ValueError(
                        f"Неудачная попытка API-запроса по адресу '{self.VACANCIES_URL}'. Возможная причина: "
                        f"{response.reason}.")
                result = response.json()  # Преобразование ответа от API в формат JSON

                # Добавление содержимого ключа "items" (только список словарей с вакансиями без вспомогательной
                # информации)
                data.extend(result.get("items", []))

                page += 1  # Переход на следующую страницу
                # Проверка на наличие еще не обработанных страниц в запросе
                if page >= result['pages']:
                    break
        return data
