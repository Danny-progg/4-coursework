import json
from abc import abstractmethod, ABC
from exceptions import ParsingError
import requests


class Engine(ABC):

    @abstractmethod
    def get_request(self):
        pass

    @abstractmethod
    def get_vacancies(self):
        pass


class HeadHunter(Engine):

    url = "https://api.hh.ru/vacancies"

    def __init__(self, keyword):
        self.params = {
            "per_page": 100,
            "page": None,
            "text": keyword,
            "archived": False,
        }
        self.headers = {
            "User-Agent": "MyImportantApp 1.0"
        }
        self.vacancies = []

    def get_request(self):

        response = requests.get(self.url, headers=self.headers, params=self.params)
        if response.status_code != 200:
            raise ParsingError(f"{response.status_code}")
        return response.json()["items"]

    def get_formatted_vacancies(self):
        formatted_vacancies = []

        for vacancy in self.vacancies:
            formatted_vacancy = {
                "employer": vacancy["employer"]["name"],
                "title": vacancy["name"],
                "url": vacancy["alternate_url"],
                "api": "HeadHunter",
            }
            salary = vacancy["salary"]
            if salary:
                formatted_vacancy["salary_from"] = salary["from"]
                formatted_vacancy["salary_to"] = salary["to"]
                formatted_vacancy["currency"] = salary["currency"]
            else:
                formatted_vacancy["salary_from"] = None
                formatted_vacancy["salary_to"] = None
                formatted_vacancy["currency"] = None
            formatted_vacancies.append(formatted_vacancy)

        return formatted_vacancies


    def get_vacancies(self, pages_count=2):
        self.vacancies = []
        for page in range(pages_count):
            page_vacancies = []
            self.params["page"] = page
            print(f"({ self.__class__.__name__ }) Парсинг страницы { page } -", end=" ")
            from exceptions import ParsingError
            try:
                page_vacancies = self.get_request()
            except ParsingError as error:
                print(error)
            else:
                self.vacancies.extend(page_vacancies)
                print(f"Загружено вакансий: { len(page_vacancies) }")
            if len(page_vacancies) == 0:
                break


class SuperJob(Engine):

    url = "https://api.superjob.ru/2.0/vacancies/"

    def __init__(self, keyword):
        self.params = {
            "per_page": 100,
            "page": None,
            "text": keyword,
            "archived": False,
        }
        self.headers = {
            "X-Api-App-Id": "v3.r.137642286.11b2ee902c008375d3ec25112e66c43c418b7df7.ff2c120070a2dc5e91070a41194ace6f6d0481cd"
        }
        self.vacancies = []

    def get_formatted_vacancies(self):
        formatted_vacancies = []
        sj_currencies = {
            "rub": "RUR",
            "uah": "UAH",
            "uzs": "UZS",
        }

        for vacancy in self.vacancies:
            formatted_vacancy = {
                "employer": vacancy["firm_name"],
                "title": vacancy["profession"],
                "url": vacancy["link"],
                "api": "SuperJob",
                "salary_from": vacancy["payment_from"] if vacancy["payment_from"] and vacancy["payment_from"] != 0 else None,
                "salary_to": vacancy["payment_to"] if vacancy["payment_to"] and vacancy["payment_to"] != 0 else None,
            }
            currency = sj_currencies[vacancy["currency"]]
            if vacancy["currency"] in sj_currencies:
                formatted_vacancy["currency"] = sj_currencies[vacancy["currency"]]
            elif vacancy["currency"]:
                formatted_vacancy["currency"] = "RUR"
            else:
                formatted_vacancy["currency"] = None

            formatted_vacancies.append(formatted_vacancy)

        return formatted_vacancies


    def get_vacancies(self, pages_count=2):
        self.vacancies = []
        for page in range(pages_count):
            page_vacancies = []
            self.params["page"] = page
            print(f"({self.__class__.__name__}) Парсинг страницы {page} -", end=" ")
            from exceptions import ParsingError
            try:
                page_vacancies = self.get_request
            except ParsingError as error:
                print(error)
            else:
                self.vacancies.extend(page_vacancies)
                print(f"Загружено вакансий: {len(page_vacancies)}")
            if len(page_vacancies) == 0:
                break

    @property
    def get_request(self):

        response = requests.get(self.url, headers=self.headers, params=self.params)
        if response.status_code != 200:
            raise ParsingError(f"{response.status_code}")
        return response.json()["objects"]


class Connector:
    def __init__(self, keyword, vacancies_json):
        self.filename = f"{ keyword.title() }.json"
        self.insert(vacancies_json)

    def insert(self, vacancies_json):
        with open (self.filename, "w", encoding="utf-8") as file:
            json.dump(vacancies_json, file, indent=4)

    def select(self):
        with open(self.filename, "r", encoding="utf-8") as file:
            vacancies = json.load(file)
        return [Vacancy(x) for x in vacancies]

    def sort_by_salary_from(self):
        desc = True if input(
            "> - DESC \n"
            "< - ASC \n>>>"
        ).lower() == ">" else False
        vacancies = self.select()
        return sorted(vacancies, key=lambda x: (x.salary_from if x.salary_from else 0, x.salary_to if x.salary_to else 0))


class Vacancy:
    def __init__(self, vacancy):
        self.employer = vacancy["employer"]
        self.title = vacancy["title"]
        self.url = vacancy["url"]
        self.api = vacancy["api"]
        self.salary_from = vacancy["salary_from"]
        self.salary_to = vacancy["salary_to"]
        self.currency = vacancy["currency"]

    def __str__(self):
        if not self.salary_from and not self.salary_to:
            salary = "Не указана"
        else:
            salary_from, salary_to = "", ""
            if self.salary_from:
                salary_from = f"от { self.salary_from } { self.salary_to }"
                if self.currency != "RUR":
                    salary_from += f" ({ round(self.salary_from * 2, 2) } RUR)"
            if self.salary_to:
                salary_to = f"до { self.salary_to } { self.currency }"
                if self.currency != "RUR":
                    salary_to += f" ({round(self.salary_to * 2, 2)} RUR)"
            salary = " ".join([salary_from, salary_to]).strip()
        return f"""
Работодатель: \"{ self.employer }\"
Вакансия: \"{ self.title }\"
Зарплата: { salary }
Ссылка: { self.url }
        """
