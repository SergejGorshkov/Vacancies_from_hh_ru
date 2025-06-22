import psycopg2


class DBManager:
    db_name: str  # Название базы данных для сохранения результатов поиска
    params: dict  # Параметры для подключения в БД
    vacancies_list: list[dict]  # Список с вакансиями, полученный от API hh.ru, для заполнения БД

    def __init__(self, db_name, params) -> None:
        """Метод-конструктор для инициализации экземпляров класса DBManager."""
        self.db_name = db_name
        self.params = params

        self._create_database()  # Создание БД
        self._create_tables()  # Создание таблиц в БД

    def _create_database(self) -> None:
        """Создание базы данных для сохранения данных о компаниях и их вакансиях на hh.ru"""

        try:
            # Подключение к стандартной базе данных postgres
            conn = psycopg2.connect(dbname='postgres', **self.params)
            conn.autocommit = True  # Автоматическое внесение изменений в БД после каждой SQL-команды
            cur = conn.cursor()

            # Проверка на существование базы данных с переданным в конструктор класса именем
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_name,))
            exists = cur.fetchone()

            if not exists:
                # Создание базы данных только если она не существует
                cur.execute(f"CREATE DATABASE {self.db_name} WITH ENCODING 'UTF8';")
                print(f"База данных {self.db_name} успешно создана")
            else:
                print(f"База данных {self.db_name} уже существует")

        except psycopg2.Error as e:
            print(f"Ошибка при работе с базой данных: {e}")
            raise
        finally:
            if 'cur' in locals():
                cur.close()

            if 'conn' in locals():
                conn.close()


    def _create_tables(self):
        """Создание таблиц в БД"""

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        conn.autocommit = True

        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE company
                (
                    id SERIAL PRIMARY KEY,
                    hh_company_id INT UNIQUE NOT NULL,
                    company_name VARCHAR(255) NOT NULL
                )
            """)

        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE vacancy
                 (
                    id SERIAL PRIMARY KEY,
                    hh_vacancy_id INT UNIQUE NOT NULL,
                    hh_company_id INT NOT NULL,
                    company_name VARCHAR(100) NOT NULL,
                    title VARCHAR NOT NULL,
                    salary_from INT,
                    salary_to INT,
                    currency VARCHAR(10),
                    vacancy_url VARCHAR(100),
                    description TEXT
                )
            """)

        conn.close()

    def insert_data_to_db(self, vacancies_list) -> None:
        """Заполнение БД данными с сайта hh.ru о компаниях и их вакансиях"""

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        conn.autocommit = True

        # Цикл по вакансиям из списка 'vacancies_list', полученных от API hh.ru
        for vacancy in vacancies_list:
            # Заполнение таблицы 'vacancy'
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO vacancy (hh_vacancy_id, hh_company_id, company_name, title, salary_from, salary_to,"
                    " currency, vacancy_url, description) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (vacancy["id"],
                     vacancy["employer"]["id"],
                     vacancy["employer"]["name"],
                     vacancy["name"],
                     vacancy.get("salary_range", {}).get("from", 0) if vacancy.get("salary_range") else 0,
                     vacancy.get("salary_range", {}).get("to", 0) if vacancy.get("salary_range") else 0,
                     vacancy.get("salary_range", {}).get("currency") if vacancy.get("salary_range") else "",
                     vacancy["alternate_url"],
                     vacancy["snippet"]["responsibility"])
                )

        # Заполнение таблицы 'company' данными из таблицы 'vacancy'
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO company (hh_company_id, company_name)
                SELECT
                    hh_company_id,
                    company_name
                FROM vacancy
                GROUP BY hh_company_id, company_name
                """)

        # Добавление в таблицу 'vacancy' ссылки на внешний ключ 'hh_company_id' таблицы 'company'
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE vacancy
                ADD CONSTRAINT fk_hh_company_id
                FOREIGN KEY (hh_company_id)
                REFERENCES company(hh_company_id);
                """)

        conn.close()

    def get_companies_list(self) -> list[str]:
        """Метод получения списка всех компаний с количеством вакансий у каждой компании"""

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    company.hh_company_id,
                    company.company_name,
                    COUNT(vacancy.hh_vacancy_id) AS vacancies_amount
                FROM company
                LEFT JOIN vacancy ON company.hh_company_id = vacancy.hh_company_id
                GROUP BY company.hh_company_id, company.company_name
                ORDER BY vacancies_amount DESC
            """)
            result = cur.fetchall()

        # Преобразование результата в список строк для последующего вывода в консоль
        companies = []
        for row in result:
            companies.append(f"id компании на hh.ru: {row[0]}. Название компании: {row[1]}. "
                             f"Количество вакансий на hh.ru: {row[2]}.\n")
        conn.close()
        return companies

    def get_vacancies_list(self) -> list[str]:
        """
        Метод получения списка всех вакансий с указанием названия компании, названия вакансии,
        зарплаты и ссылки на вакансию.
        """

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    vacancy.company_name,
                    vacancy.title,
                    vacancy.salary_from,
                    vacancy.salary_to,
                    vacancy.currency,
                    vacancy.vacancy_url
                FROM vacancy
                LEFT JOIN company ON company.hh_company_id = vacancy.hh_company_id
                ORDER BY vacancy.salary_from DESC
            """)
            result = cur.fetchall()

        # Преобразование результата в список строк для последующего вывода в консоль
        vacancies = []
        for row in result:
            vacancies.append(f"Название компании: {row[0]}.\n"
                             f"Требуется: {row[1]}.\n"
                             f"Зарплата от {row[2] if row[2] else 0} до {row[3] if row[3] else 0} {row[4]}.\n"
                             f"Ссылка на вакансию: {row[5]}.\n")
        conn.close()
        return vacancies

    def get_avg_salary(self) -> int:
        """Метод получения средней зарплаты по всем вакансиям"""

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        with conn.cursor() as cur:
            cur.execute("""
                SELECT AVG(
                    COALESCE(
                        (salary_from + salary_to) / 2,
                        salary_from,
                        salary_to,
                        0))
                FROM vacancy;
            """)
            result = cur.fetchone()

        conn.close()
        return round(result[0]) if result and result[0] is not None else 0

    def get_vacancies_list_with_higher_salary(self) -> list[str]:
        """
        Метод получения списка всех вакансий, у которых зарплата выше средней по всем вакансиям
        (с указанием названия компании, названия вакансии, зарплаты и ссылки на вакансию).
        """

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    vacancy.company_name,
                    vacancy.title,
                    vacancy.salary_from,
                    vacancy.salary_to,
                    vacancy.currency,
                    vacancy.vacancy_url
                FROM vacancy
                WHERE vacancy.salary_from > (SELECT AVG(
                    COALESCE(
                        (salary_from + salary_to) / 2,
                        salary_from,
                        salary_to,
                        0))
                FROM vacancy) OR vacancy.salary_to > (SELECT AVG(
                    COALESCE(
                        (salary_from + salary_to) / 2,
                        salary_from,
                        salary_to,
                        0))
                FROM vacancy)
                ORDER BY vacancy.salary_from DESC
            """)
            result = cur.fetchall()

        # Преобразование результата в список строк для последующего вывода в консоль
        vacancies = []
        for row in result:
            vacancies.append(f"Название компании: {row[0]}.\n"
                             f"Требуется: {row[1]}.\n"
                             f"Зарплата от {row[2] if row[2] else 0} до {row[3] if row[3] else 0} {row[4]}.\n"
                             f"Ссылка на вакансию: {row[5]}.\n")

        conn.close()
        return vacancies

    def get_vacancies_list_by_keyword(self, keyword: str) -> list[str]:
        """
        Метод получения списка всех вакансий, у которых в названии или в описании есть ключевые слова
        (с указанием названия компании, названия вакансии, зарплаты и ссылки на вакансию).
        """

        conn = psycopg2.connect(dbname=self.db_name, **self.params)  # Подключение к ранее созданной БД
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    vacancy.company_name,
                    vacancy.title,
                    vacancy.salary_from,
                    vacancy.salary_to,
                    vacancy.currency,
                    vacancy.vacancy_url
                FROM vacancy
                WHERE vacancy.title ILIKE %s OR vacancy.description ILIKE %s
                ORDER BY vacancy.salary_from DESC
            """, (f'%{keyword}%', f'%{keyword}%'))

            result = cur.fetchall()

        # Преобразование результата в список строк для последующего вывода в консоль
        vacancies = []
        for row in result:
            vacancies.append(f"Название компании: {row[0]}.\n"
                             f"Требуется: {row[1]}.\n"
                             f"Зарплата от {row[2] if row[2] else 0} до {row[3] if row[3] else 0} {row[4]}.\n"
                             f"Ссылка на вакансию (на hh.ru): {row[5]}.\n")

        conn.close()
        return vacancies
