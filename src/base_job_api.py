from abc import ABC, abstractmethod


class JobAPI(ABC):
    """Абстрактный класс для создания подклассов поиска вакансий"""

    params: dict  # Параметры для GET-запроса по API платформы поиска вакансий

    @abstractmethod
    def _connect(self, params):
        """Метод подключения к API (приватный)"""
        pass

    @abstractmethod
    def get_vacancies(self, company_ids):
        """Метод получения вакансий по id организаций (на hh.ru)"""
        pass
