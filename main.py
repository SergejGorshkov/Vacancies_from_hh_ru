from config import config
from src.db_manager import DBManager
from src.hh_api import HeadHunterAPI

# Список id организаций (на hh.ru)
COMPANY_IDS = ["4306244",  # "VICTORY_group"
               "67611",  # "Тензор"
               "41862",  # "Контур"
               "1429999",  # "Циан"
               "906557",  # "SberTec"
               "1740",  # "Яндекс"
               "78638",  # "Т-Банк"
               "4181",  # "ПАО ВТБ"
               "10246537",  # "Кибертех"
               "3529"  # "СБЕР"
               ]
DB_NAME = 'hh_database'  # Название создаваемой БД


def user_interaction() -> None:
    """Функция для взаимодействия с пользователем и анализа вакансий"""

    while True:
        user_answer = input("""Для получения соответствующих данных о компаниях и их вакансиях на hh.ru выберите
        соответствующий пункт меню (например, 2).
        1. Получить список компаний и количества вакансий у каждой компании.
        2. Получить список всех вакансий с их кратким описанием.
        3. Получить список всех вакансий, у которых зарплата выше средней по всем вакансиям.
        4. Получить список всех вакансий по ключевому слову.
        5. Завершить работу программы.  """).strip(" .,!?\"\n\t")

        # Обработка ответа пользователя
        if user_answer not in ["1", "2", "3", "4", "5"]:
            print(f"Выбран несуществующий пункт меню {user_answer}. Введите число от 1 до 5.")
            continue  # Возврат к меню

        elif user_answer == "5":
            print("Программа завершает работу. До встречи.")
            break

        elif user_answer == "1":
            try:
                print(*data_base.get_companies_list())  # Вывод списка компаний с количеством вакансий
            except Exception as error:
                print(f"При работе с базой данных произошла ошибка: {error}")
                continue  # Возврат к меню

        elif user_answer == "2":
            try:
                print(*data_base.get_vacancies_list())  # Вывод списка вакансий с кратким описанием
            except Exception as error:
                print(f"При работе с базой данных произошла ошибка: {error}")
                continue  # Возврат к меню

        elif user_answer == "3":
            try:
                print(f"Средняя зарплата по всем вакансиям составляет {data_base.get_avg_salary()} руб.")
                print(*data_base.get_vacancies_list_with_higher_salary())  # Вывод списка вакансий с з/п выше средней
            except Exception as error:
                print(f"При работе с базой данных произошла ошибка: {error}")
                continue  # Возврат к меню

        elif user_answer == "4":
            while True:
                keyword = input(
                    "Введите ключевое слово (например, Python) или введите '0' для возврата в меню: ").strip(
                    " .,!?\"\n\t")

                if keyword == "0":
                    break  # Прерывание цикла поиска по ключевому слову. Возврат в меню

                try:
                    result = data_base.get_vacancies_list_by_keyword(keyword)
                    if result:
                        print(*result)  # Вывод списка вакансий по ключевому слову
                    else:
                        print(
                            f"Не найдено ни одной вакансии по ключевому слову '{keyword}'. "
                            f"Попробуйте уточнить запрос.")
                        continue
                except Exception as error:
                    print(f"При работе с базой данных произошла ошибка: {error}")
                    break  # Прерывание цикла поиска по ключевому слову. Возврат к меню


if __name__ == '__main__':
    print("Добро пожаловать в программу работы с вакансиями с сайта hh.ru!")

    db_params = config()  # Извлечение параметров для подключения к БД из файла database.ini
    data_base = DBManager(DB_NAME, db_params)  # Создание объекта БД

    # Создание экземпляра класса для работы с API сайта hh.ru
    hh_api = HeadHunterAPI()

    vacancies_list = []  # Список с вакансиями пока пустой

    try:
        # Получение вакансий от указанных в списке 'COMPANY_IDS' компаний с API сайта hh.ru
        vacancies_list = hh_api.get_vacancies(COMPANY_IDS)
    except TypeError as error:
        print(error)

    # Выполняется анализ полученных данных. Если произошла ошибка или вакансии не были найдены,- завершение работы
    finally:
        if vacancies_list:  # Если данные от API получены успешно...
            try:
                data_base.insert_data_to_db(vacancies_list)  # Заполнение БД
            except Exception as error:
                print(f"При заполнении базы данных произошла ошибка: {error}")

            # Вызов функции для взаимодействия с пользователем и анализа вакансий
            user_interaction()
        else:
            print("Не удалось получить данные о вакансиях от API hh.ru")
