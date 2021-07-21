from auth_date import username, password, passwordBase, webdriverPath, postPath, nameBase
import pymysql.cursors
import random
import os
import requests
from PIL import Image
from append_arts import Append
import autoit
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
import xlrd
import subprocess


class Generation():
    """
    Порядок создания баазы данных:
        1. Скачивается xlsx
        2. xlsx, сокраняется как файл csv (обычный, не utf8),
            который ипортируется в готовую модель базы данных в таблицу pictures.
            Если импортировал мало строк, перезагрузить Workbenc, и попробовать заново.
        3. xlsx сохранятеся как файл "Книга Excel 97-2003 (*.xls)"
        4. importing_special_characters
        5. removal_defective (так как пока не научились сскачивать картинны,
            у которых 'https://www.sothebys.com/en/auctions' в tried_url. теряется 13782 картины)
        6. converting_price_to_dollars
        7. filling_database.

    Порядок создания поста:
        1. extracting_pictures_for_post
        2. export_arts
        3. description
        4. post (Не понятно почему, но иногда может не открывать окно для загрузки фотографий. Можно попробовать перезагрузить компьютер)

        Все эти пункты объединины в make_post
    """

    def __init__(self, passwordBase):
        """
        Объявление класса.
        host – Host where the database server is located
        user – Username to log in as
        password – Password to use.
        db – Database to use, None to not use a particular one.
        charset – Charset you want to use.
        cursorclass – Custom cursor class to use.

        :param passwordBase: Пароль от базы данных
        """

        self.connect = pymysql.connect(host='127.0.0.1',
                                       user='root',
                                       password=passwordBase,
                                       db=nameBase,
                                       charset='utf8mb4',
                                       cursorclass=pymysql.cursors.DictCursor
                                       )

    def importing_special_characters(self, excel_path):
        """
        Импортирование специальных символов из файла xls в базу данных и
        добавление некоторых строк, которые были пропущены по какой-то причине при импортировании.
        Но xlsx нучжно сохранить как файл формата "Книга Excel 97-2003 (*.xls)", чтобы читал спец символы.

        :param excel_path: Путь до файла xls
        :return: None
        """
        with self.connect.cursor() as cursor:
            rb = xlrd.open_workbook(excel_path, formatting_info=True)
            sheet = rb.sheet_by_name('Dataset')

            for i in range(1, sheet.nrows):
                a = sheet.row_values(i)
                Author = sheet.row_values(i)[2]
                Author = Author.replace('"', "'")
                Art = sheet.row_values(i)[3]
                Art = Art.replace('"', "'")
                tried_url = sheet.row_values(i)[21]

                try:
                    cursor.execute(f"""Select id_picture from pictures WHERE pictures.tried_url = '{tried_url}';""")
                    id_picture = cursor.fetchone()
                    cursor.execute(f"""UPDATE pictures SET pictures.Author = "{Author}", pictures.Art = "{Art}"
                                                            WHERE pictures.id_picture = {id_picture['id_picture']};""")
                except Exception as ex:  # если не найдет картины по url в базе данных (была не импортирована)
                    print(ex)
                    print("Импортируем отсутствующую картину с tried_url: ", tried_url)
                    cursor.execute(f"""INSERT pictures(sale_date, Price, Author, Art, Sign, Technique, 
                    Material, Nazi, Framed, Size,square_m, Currency, EstimateFrom, EstimateTo, ExhibitedNum, 
                    ProvenanceNum, LiteratureNum, CataloguingLength, Time, City, tried_url, Image, date_of_birth, 
                    date_of_death, century, nationality, sex, style, repeat_sale, feature1, feature2, number_of_day, 
                    day_of_week, month, year, normalized_price, hasFollowers, hasAfter, mannerOf, 
                    circleOf, isUntitled, isNumbered, normalized_estimatefrom, normalized_estimateto, Auction) 
                    VALUES ("{sheet.row_values(i)[0]}","{sheet.row_values(i)[1]}","{Author}","{Art}",
                    "{sheet.row_values(i)[5]}","{sheet.row_values(i)[6]}",
                    "{sheet.row_values(i)[7]}","{sheet.row_values(i)[8]}","{sheet.row_values(i)[9]}",
                    "{sheet.row_values(i)[10]}","{sheet.row_values(i)[11]}","{sheet.row_values(i)[12]}",
                    "{sheet.row_values(i)[13]}","{sheet.row_values(i)[14]}","{sheet.row_values(i)[15]}",
                    "{sheet.row_values(i)[16]}","{sheet.row_values(i)[17]}","{sheet.row_values(i)[18]}",
                    "{sheet.row_values(i)[19]}","{sheet.row_values(i)[20]}","{tried_url}","{sheet.row_values(i)[22]}",
                    "{sheet.row_values(i)[23]}","{sheet.row_values(i)[24]}","{sheet.row_values(i)[25]}",
                    "{sheet.row_values(i)[27]}","{sheet.row_values(i)[28]}","{sheet.row_values(i)[29]}",
                    "{sheet.row_values(i)[30]}","{sheet.row_values(i)[31]}","{sheet.row_values(i)[32]}",
                    "{sheet.row_values(i)[33]}","{sheet.row_values(i)[34]}","{sheet.row_values(i)[35]}",
                    "{sheet.row_values(i)[36]}","{sheet.row_values(i)[37]}","{sheet.row_values(i)[38]}",
                    "{sheet.row_values(i)[39]}","{sheet.row_values(i)[40]}","{sheet.row_values(i)[41]}",
                    "{sheet.row_values(i)[42]}","{sheet.row_values(i)[43]}","{sheet.row_values(i)[44]}",
                    "{sheet.row_values(i)[45]}","{sheet.row_values(i)[46]}");""")
                    # без  deal_time_(utc) и Owner из-за скобок
                self.connect.commit()

    def removal_defective(self):
        """
        Удаление картин, которые невозможно скачать.
        Удаляет примерно 6500 картин.

        :return: None
        """
        with self.connect.cursor() as cursor:
            cursor.execute("""Select id_picture, tried_url from pictures;""")
            all_mas = cursor.fetchall()
            cursor.execute("""Select count(id_picture) as count from pictures;""")
            j = cursor.fetchall()[0]['count']

            while (j > 0):
                j -= 1
                id_picture = all_mas[j]['id_picture']
                tried_url = all_mas[j]['tried_url']
                if 'https://www.sothebys.com/en/auctions' in tried_url:
                    try:
                        cursor.execute(f"""DELETE FROM pictures WHERE pictures.id_picture = {id_picture};""")
                        self.connect.commit()
                    except Exception as ex:
                        print(ex)

    def converting_price_to_dollars(self):
        """
        Создает 3 столбца в таблице и перевод стоимости картин и их оценки в USD, для последующего сравнения.
        Удаляет ошибочные строки (Например, когда в Currency попадает неверное значение из другой ячейки,
        то есть устраняет проблему базы данных).

        :return: None
        """
        with self.connect.cursor() as cursor:
            cursor.execute("""ALTER TABLE pictures
                                DROP COLUMN PriceInUSD,
                                DROP COLUMN EstimateFromInUSD,
                                DROP COLUMN EstimateToInUSD;""")
            cursor.execute("""ALTER TABLE pictures
                                ADD PriceInUSD FLOAT NULL,
                                ADD EstimateFromInUSD FLOAT NULL,
                                ADD EstimateToInUSD FLOAT NULL;""")
            cursor.execute("""SELECT id_picture, Price, EstimateFrom, EstimateTo, Currency FROM pictures;""")
            all_mas = cursor.fetchall()

            CurrencyToUSD = {"USD": 1, "EUR": 1.2169262, "GBP": 1.4138254, "HKD": 0.12873913, "RMB": 0.1556072,
                             "CHF": 1.1092421, "ESP": 0.0073121019, "SGD": 0.754384, "CNY": 0.15559932}

            for Art in all_mas:
                try:
                    PriceInUSD = Art["Price"] * CurrencyToUSD[Art["Currency"]]
                    EstimateFromInUSD = int(Art["EstimateFrom"]) * CurrencyToUSD[Art["Currency"]]
                    EstimateToInUSD = int(Art["EstimateTo"]) * CurrencyToUSD[Art["Currency"]]
                    cursor.execute(f"""UPDATE pictures SET pictures.PriceInUSD = {PriceInUSD}, 
                                            pictures.EstimateFromInUSD = {EstimateFromInUSD}, 
                                            pictures.EstimateToInUSD = {EstimateToInUSD}
                                            WHERE pictures.id_picture = {Art['id_picture']};""")
                    self.connect.commit()

                except Exception as ex:
                    print(ex)
                    try:
                        cursor.execute(f"""DELETE FROM pictures WHERE pictures.id_picture = {Art["id_picture"]};""")
                        self.connect.commit()
                    except Exception as ex:
                        print(ex)

    def filling_database(self):
        """
        Запонение таблиц authors и author_and_pictures нас основе pictures.
        :return: None
        """
        with self.connect.cursor() as cursor:
            cursor.execute("""Select Author, id_picture from pictures;""")
            all_mas = cursor.fetchall()
            cursor.execute("""Select count(id_picture) as count from pictures;""")
            count_of_pictures = cursor.fetchall()[0]['count']
            j = 0
            count_of_authors = 1

            while(j < count_of_pictures):
                author = all_mas[j]['Author']
                id_picture = all_mas[j]['id_picture']
                cursor.execute(f"""Select id_author from author_and_pictures where Author = "{author}";""")
                author_in_table = cursor.fetchone()

                try:
                    id_author = int(author_in_table['id_author'])  # выдаст ошибку, если такого автора не было в таблице author_and_pictures
                    try:
                        cursor.execute(
                            f"""INSERT INTO author_and_pictures(id_picture, Author, id_author) VALUES('{id_picture}', "{author}", '{id_author}');""")
                    except Exception as ex:
                        print(ex)
                        print(f'Что-то не так со строкой с индексом {id_picture}')
                        print("Автора еще не было в author_and_pictures, ", all_mas[j], "\n")
                        j += 1
                        continue

                except:
                    try:
                        cursor.execute(f"""INSERT INTO Authors(id_author, Author) VALUES("{count_of_authors}", "{author}");""")
                        cursor.execute(
                            f"""INSERT INTO author_and_pictures(id_picture, Author, id_author) VALUES('{id_picture}', "{author}", '{count_of_authors}');""")
                        count_of_authors += 1
                    except Exception as ex:
                        print(ex)
                        print(f'Что-то не так со строкой с индексом {id_picture}')
                        print("Автор уже был в author_and_pictures, ", all_mas[j], "\n")
                        j += 1
                        continue

                j += 1
                self.connect.commit()

    def extracting_pictures_for_post(self):
        """
        Взятие дорогой и дешевой картины (строк данных) одного автора

        :return: Массив двух строк базы данных
        """
        with self.connect.cursor() as cursor:
            true_or_false = True
            while true_or_false:
                cursor.execute("""SELECT author_and_pictures.id_author, author_and_pictures.Author, status FROM
                                        author_and_pictures LEFT OUTER JOIN authors
                                            ON author_and_pictures.id_author = authors.id_author
                                        WHERE authors.status is NULL
                                        GROUP BY author_and_pictures.id_author;""")
                author_row = cursor.fetchone()
                author = author_row['Author']
                author = author.replace('\'', '\\\'')
                author = author.replace('\"', '\\\"')
                id_author = int(author_row['id_author'])

                cursor.execute(f"""SELECT pictures.id_picture, sale_date, Price, pictures.Author, Art, Currency, EstimateFrom, EstimateTo, City, tried_url, Image, PriceInUSD, EstimateFromInUSD, EstimateToInUSD FROM
                                                        pictures LEFT OUTER JOIN author_and_pictures
                                                            ON pictures.id_picture = author_and_pictures.id_picture
                                                        LEFT OUTER JOIN authors
                                                            ON author_and_pictures.id_author = authors.id_author
                                                        WHERE Image IS NOT NULL AND Image != '—' AND pictures.Author = "{author}"
                                                            AND PriceInUSD = (SELECT MAX(PriceInUSD) FROM pictures WHERE Image IS NOT NULL AND Image != '—' AND
                                                                                pictures.Author = "{author}") ;""")
                One_of_the_most_expensive_paintings = cursor.fetchone()
                cursor.execute(f"""SELECT pictures.id_picture, sale_date, Price, pictures.Author, Art, Currency, EstimateFrom, EstimateTo, City, tried_url, Image, PriceInUSD, EstimateFromInUSD, EstimateToInUSD FROM
                                                        pictures LEFT OUTER JOIN author_and_pictures
                                                            ON pictures.id_picture = author_and_pictures.id_picture
                                                        LEFT OUTER JOIN authors
                                                            ON author_and_pictures.id_author = authors.id_author
                                                        WHERE Image IS NOT NULL AND Image != '—' AND pictures.Author = "{author}"
                                                            AND PriceInUSD = (SELECT MIN(PriceInUSD) FROM pictures WHERE Image IS NOT NULL AND Image != '—' AND
                                                                                pictures.Author = "{author}") ;""")
                One_of_the_most_inexpensive_paintings = cursor.fetchone()

                if One_of_the_most_expensive_paintings['Price'] == One_of_the_most_inexpensive_paintings['Price']:
                    cursor.execute(f"""UPDATE authors SET authors.status = 'TheSamePrice or OnePicture',
                                                    authors.One_of_the_most_expensive_paintings = {One_of_the_most_expensive_paintings['id_picture']},
                                                    authors.One_of_the_most_inexpensive_paintings = {One_of_the_most_inexpensive_paintings['id_picture']}
                                                    WHERE authors.id_author = {id_author};""")

                else:
                    cursor.execute(f"""UPDATE authors SET authors.status = 'Used',
                                                    authors.One_of_the_most_expensive_paintings = {One_of_the_most_expensive_paintings['id_picture']},
                                                    authors.One_of_the_most_inexpensive_paintings = {One_of_the_most_inexpensive_paintings['id_picture']}
                                                    WHERE authors.id_author = {id_author};""")
                    true_or_false = False
                self.connect.commit()

        return [One_of_the_most_expensive_paintings, One_of_the_most_inexpensive_paintings]

    def extracting_pictures_for_story(self):
        """
        Взятие двух картин (строк данных) одного стиля

        :return: Массив двух строк базы данных
        """
        with self.connect.cursor() as cursor:
            true_or_false = True
            while true_or_false:
                masStyle = ["abstract expressionism", "abstractionism", "academicism", "avant-garde", "baroque", "classicism", "conceptualism", "contemporary art", "cubism", "dadaism", "expressionism", "fauvism", "folk-art", "futurism", "impressionism", "installation", "magical realism", "mannerism", "metaphysical art", "minimalism", "modern", "modernism", "nabism", "neo-expressionism", "neo-impressionism", "neo-pop / post-pop", "neoclassicism", "organic abstraction", "pop-art", "post-impressionism", "postconceptualism", "pre-raphaelitism", "realism", "renaissance", "rococo", "romanica", "romanticism", "surrealism", "symbolism", "traditional chinese painting"]
                style = random.choice(masStyle)

                cursor.execute(f"""SELECT pictures.id_picture, sale_date, Price, pictures.Author, Art, Currency, EstimateFrom, EstimateTo, City, tried_url, Image, style, PriceInUSD FROM
                                                        pictures LEFT OUTER JOIN author_and_pictures
                                                            ON pictures.id_picture = author_and_pictures.id_picture
                                                        LEFT OUTER JOIN authors
                                                            ON author_and_pictures.id_author = authors.id_author
                                                        WHERE Image IS NOT NULL AND Image != '—' AND storyStatus is NULL
                                                            AND style = '{style}' ;""")
                first = cursor.fetchone()

                if first is None:  # уже все картины в этом стиле были использованы
                    continue

                cursor.execute(f"""SELECT pictures.id_picture, sale_date, Price, pictures.Author, Art, Currency, EstimateFrom, EstimateTo, City, tried_url, Image, style, PriceInUSD FROM
                                                                        pictures LEFT OUTER JOIN author_and_pictures
                                                                            ON pictures.id_picture = author_and_pictures.id_picture
                                                                        LEFT OUTER JOIN authors
                                                                            ON author_and_pictures.id_author = authors.id_author
                                                                        WHERE Image IS NOT NULL AND Image != '—' AND storyStatus is NULL AND pictures.id_picture != {first['id_picture']}
                                                                            AND style = '{style}' ;""")
                second = cursor.fetchone()

                if second is None:  # осталась только одна картина в этом стиле
                    cursor.execute(f"""UPDATE author_and_pictures SET storyStatus = 'Only one picture left'
                                                    WHERE author_and_pictures.id_picture = {first["id_picture"]};""")
                    continue

                else:
                    cursor.execute(f"""UPDATE author_and_pictures SET storyStatus = 'Used'
                                                    WHERE author_and_pictures.id_picture = {first["id_picture"]};""")
                    cursor.execute(f"""UPDATE author_and_pictures SET storyStatus = 'Used'
                                                    WHERE author_and_pictures.id_picture = {second["id_picture"]};""")
                    true_or_false = False
                self.connect.commit()

        return [first, second]

    def export_arts(self, mas, postPath):
        """
        Скачивание картин

        :param mas: Массив двух строк базы данных
        :param postPath: Путь, куда скачивать картины
        :return: None
        """
        mas_str = ['\One_of_the_most_expensive_paintings', '\One_of_the_most_inexpensive_paintings']

        for i in range(2):
            try:
                url = mas[i]["Image"]
                r = requests.get(url)

                with open(postPath + mas_str[i] + ".jpg", 'wb') as file:
                    file.write(r.content)

            except Exception as ex:
                print(ex)

    def description(self, mas, direction = "horizontal"): # предполагается, что преведение цен и оценок к доллару уже произошло
        """
        Генерация текста для поста.

        :param mas: Массив двух строк базы данных
        :param direction: 'horizontal' или 'vertical'
        :return: str
        """
        text = ""

        if '\n' in mas[0]["Art"]:
            mas[0]["Art"] = mas[0]["Art"].replace('\n', '')
        if '\n' in mas[1]["Art"]:
            mas[1]["Art"] = mas[1]["Art"].replace('\n', '')

        try:
            if direction == 'horizontal':
                if mas[0]["Currency"] == "USD":
                    text += f"""Author: {mas[0]["Author"]}\n\nOne of the most expensive art (left): {mas[0]["Art"]}\nDate of sale: {mas[0]["sale_date"]}\nPrice: {mas[0]["Price"]} {mas[0]["Currency"]}\nEstimate: {mas[0]["EstimateFrom"]} - {mas[0]["EstimateTo"]} {mas[0]["Currency"]} \nLink to auction: {mas[0]["tried_url"]}\n\n"""
                else:
                    text += f"""Author: {mas[0]["Author"]}\n\nOne of the most expensive art (left): {mas[0]["Art"]}\nDate of sale: {mas[0]["sale_date"]}\nPrice: {mas[0]["Price"]} {mas[0]["Currency"]} ({int(mas[0]["PriceInUSD"]) // 10 * 10} USD)\nEstimate: {mas[0]["EstimateFrom"]} - {mas[0]["EstimateTo"]} {mas[0]["Currency"]} ({int(mas[0]["EstimateFromInUSD"]) // 10 * 10} - { int(mas[0]["EstimateToInUSD"]) // 10 * 10} USD)\nLink to auction: {mas[0]["tried_url"]}\n\n"""

                if mas[1]["Currency"] == "USD":
                    text += f"""One of the most inexpensive art (right): {mas[1]["Art"]}\nDate of sale: {mas[1]["sale_date"]}\nPrice: {mas[1]["Price"]} {mas[1]["Currency"]}\nEstimate: {mas[1]["EstimateFrom"]} - {mas[1]["EstimateTo"]} {mas[1]["Currency"]}\nLink to auction: {mas[1]["tried_url"]}"""
                else:
                    text += f"""One of the most inexpensive art (right): {mas[1]["Art"]}\nDate of sale: {mas[1]["sale_date"]}\nPrice: {mas[1]["Price"]} {mas[1]["Currency"]} ({int(mas[1]["PriceInUSD"]) // 10 * 10} USD)\nEstimate: {mas[1]["EstimateFrom"]} - {mas[1]["EstimateTo"]} {mas[1]["Currency"]} ({int(mas[1]["EstimateFromInUSD"]) // 10 * 10} - {int(mas[1]["EstimateToInUSD"]) // 10 * 10} USD)\nLink to auction: {mas[1]["tried_url"]}"""
            else:
                if mas[0]["Currency"] == "USD":
                    text += f"""Author: {mas[0]["Author"]}\n\nOne of the most expensive art (above): {mas[0]["Art"]}\nDate of sale: {mas[0]["sale_date"]}\nPrice: {mas[0]["Price"]} {mas[0]["Currency"]}\nEstimate: {mas[0]["EstimateFrom"]} - {mas[0]["EstimateTo"]} {mas[0]["Currency"]}\nLink to auction: {mas[0]["tried_url"]}\n\n"""
                else:
                    text += f"""Author: {mas[0]["Author"]}\n\nOne of the most expensive art (above): {mas[0]["Art"]}\nDate of sale: {mas[0]["sale_date"]}\nPrice: {mas[0]["Price"]} {mas[0]["Currency"]} ({int(mas[0]["PriceInUSD"]) // 10 * 10} USD)\nEstimate: {mas[0]["EstimateFrom"]} - {mas[0]["EstimateTo"]} {mas[0]["Currency"]} ({int(mas[0]["EstimateFromInUSD"]) // 10 * 10} - {int(mas[0]["EstimateToInUSD"]) // 10 * 10} USD)\nLink to auction: {mas[0]["tried_url"]}\n\n"""

                if mas[1]["Currency"] == "USD":
                    text += f"""One of the most inexpensive art (below): {mas[1]["Art"]}\nDate of sale: {mas[1]["sale_date"]}\nPrice: {mas[1]["Price"]} {mas[1]["Currency"]}\nEstimate: {mas[1]["EstimateFrom"]} - {mas[1]["EstimateTo"]} {mas[1]["Currency"]}\nLink to auction: {mas[1]["tried_url"]}"""
                else:
                    text += f"""One of the most inexpensive art (below): {mas[1]["Art"]}\nDate of sale: {mas[1]["sale_date"]}\nPrice: {mas[1]["Price"]} {mas[1]["Currency"]} ({int(mas[1]["PriceInUSD"]) // 10 * 10} USD)\nEstimate: {mas[1]["EstimateFrom"]} - {mas[1]["EstimateTo"]} {mas[1]["Currency"]} ({int(mas[1]["EstimateFromInUSD"]) // 10 * 10} - {int(mas[1]["EstimateToInUSD"]) // 10 * 10} USD)\nLink to auction: {mas[1]["tried_url"]}"""

            # text += "\n\nWhy do you think there is such a difference in the cost of paintings?"
            text += "\n\n#contrarto"
        except Exception as ex:
            print(ex)
        return text

    def post(self, postPath, webdriverPath, caption):
        """
        Выкладывание поста через selenium и AutoIt

        :param postPath: Путь к публикуемой картинке
        :param webdriverPath: Путь к webdriver
        :param caption: Текст к посту
        :return: None
        """
        mobile_emulation = {"deviceName": "Galaxy S5"}
        opts = webdriver.ChromeOptions()
        # opts.add_argument('--headless')  делает открытие невидимы
        opts.add_experimental_option("mobileEmulation", mobile_emulation)

        driver = webdriver.Chrome(executable_path=webdriverPath, options=opts)

        driver.get("https://www.instagram.com")

        sleep(random.randrange(4, 5))

        def login():
            try:
                login_button = driver.find_element_by_xpath(
                    "/html/body/div[1]/section/main/article/div/div/div/div[3]/button[1]")
                login_button.click()
            except:
                login_button = driver.find_element_by_xpath(
                    "/html/body/div[1]/section/main/article/div/div/div/div[2]/button")
                login_button.click()
            sleep(random.randrange(2, 3))
            username_input = driver.find_element_by_name("username")
            username_input.send_keys(username)
            sleep(random.randrange(2, 3))
            password_input = driver.find_element_by_name("password")
            password_input.send_keys(password)
            password_input.submit()

        login()
        sleep(random.randrange(8, 10))

        def close_add_to_home():
            try:
                not_now_btn = driver.find_element_by_xpath("/html/body/div[1]/section/main/div/div/div/button")
                not_now_btn.click()
            except:
                pass

            sleep(random.randrange(8, 10))

            try:
                not_now_btn = driver.find_element_by_xpath("/html/body/div[4]/div/div/div/div[3]/button[2]")
                not_now_btn.click()
            except:
                pass

        close_add_to_home()

        sleep(random.randrange(8, 10))
        new_posq_btn = driver.find_element_by_xpath(
            "/html/body/div[1]/section/nav[2]/div/div/div[2]/div/div/div[3]")
        new_posq_btn.click()

        sleep(random.randrange(2, 3))
        autoit.win_active("Открытие")
        sleep(random.randrange(2, 3))
        autoit.control_send("Открытие", "Edit1", postPath)
        sleep(random.randrange(2, 3))
        autoit.control_send("Открытие", "Edit1", "{ENTER}")
        sleep(random.randrange(2, 3))

        # расширяем фотографию, если нужно
        try:
            turn_btn = driver.find_element_by_xpath(
                '/html/body/div[1]/section/div[2]/div[2]/div/div/div/button[2]/span')  # если нашел такую кнопку,то это не квадрат, можно расширять
            expand_btn = driver.find_element_by_xpath(
                '/html/body/div[1]/section/div[2]/div[2]/div/div/div/button[1]').click()
        except:
            pass
        sleep(random.randrange(2, 3))

        next_btn = driver.find_element_by_xpath("/html/body/div[1]/section/div[1]/header/div/div[2]/button").click()
        sleep(random.randrange(2, 3))

        caption_field = driver.find_element_by_xpath("/html/body/div[1]/section/div[2]/section[1]/div[1]/textarea")
        caption_field.send_keys(caption)

        share_btn = driver.find_element_by_xpath("/html/body/div[1]/section/div[1]/header/div/div[2]/button").click()
        sleep(random.randrange(15, 30))

        driver.close()

    def make_post(self, postPath, webdriverPath, direction = ""):
        """
        Полное создание поста

        :param postPath: Путь, где будут сохраняться картины
        :param webdriverPath: Путь к webdriver
        :param direction: Расположение картин ('horizontal' или 'vertical')
        :return:
        """
        mas = self.extracting_pictures_for_post()
        self.export_arts(mas, postPath)

        images = [Image.open(postPath + '\One_of_the_most_expensive_paintings.jpg'),
                  Image.open(postPath + '\One_of_the_most_inexpensive_paintings.jpg')]
        app = Append()
        if direction == "":
            comboAndDirection = app.append_images_square_minimum_background(images)
            combo = comboAndDirection[0]
            direction = comboAndDirection[1]
        else:
            combo = app.append_images_square(images, direction)

        combo.save(postPath + '\combo.jpg')

        caption = self.description(mas, direction)

        self.post(postPath + '\combo.jpg', webdriverPath, caption)

        os.remove(postPath + '\One_of_the_most_expensive_paintings.jpg')
        os.remove(postPath + '\One_of_the_most_inexpensive_paintings.jpg')
        os.remove(postPath + '\combo.jpg')

        print('Пост был опубликован')

    def make_story(self, postPath):
        mas = self.extracting_pictures_for_story()
        self.export_arts(mas, postPath)

        images = [Image.open(postPath + '\One_of_the_most_expensive_paintings.jpg'),
                  Image.open(postPath + '\One_of_the_most_inexpensive_paintings.jpg')]

        app = Append()
        newMas = app.stories(images)
        newMas[0].save(postPath + '\\first.jpg')
        newMas[1].save(postPath + '\\second.jpg')

        def sendMessage(text):
            response = requests.post(
                url='https://api.telegram.org/bot{0}/{1}'.format(TOKEN, "sendMessage"),
                data={'chat_id': ChatID, 'text': text}
            ).json()

        sendMessage(f"Which {mas[0]['style']} do you like more?")

        def sendPhoto(imageFile):
            command = 'curl -s -X POST https://api.telegram.org/bot' + TOKEN + '/sendPhoto -F chat_id=' + ChatID + " -F photo=@" + imageFile
            subprocess.call(command.split(' '))
            return

        sendPhoto(r'C:\Users\Daniil\PycharmProjects\InstagramBot\web\post\first.jpg')
        price = 'id_picture: ' + str(mas[0]['id_picture']) + ', price: ' + str(mas[0]['Price']) + ' ' + mas[0]['Currency']
        if mas[0]['Currency'] != 'USD':
            price += ' (' + str(int(mas[0]['PriceInUSD'] // 10 * 10)) + " USD)"
        sendMessage(price)
        sendPhoto(r'C:\Users\Daniil\PycharmProjects\InstagramBot\web\post\second.jpg')
        price = 'id_picture: ' + str(mas[1]['id_picture']) + ', price: ' + str(mas[1]['Price']) + ' ' + mas[1]['Currency']
        if mas[1]['Currency'] != 'USD':
            price += ' (' + str(int(mas[1]['PriceInUSD'] // 10 * 10)) + " USD)"
        sendMessage(price)

        print("\n", mas)
        # os.remove(postPath + '\One_of_the_most_expensive_paintings.jpg')
        # os.remove(postPath + '\One_of_the_most_inexpensive_paintings.jpg')
        # os.remove(postPath + '\\first.jpg')
        # os.remove(postPath + '\\second.jpg')






do = Generation(passwordBase)
# do.importing_special_characters(r"C:\Users\Daniil\PycharmProjects\InstagramBot\Datesets\Sothebys_&_Christies_without_description.xls")
# do.removal_defective()
# do.filling_database()
# do.converting_price_to_dollars()


do.make_post(postPath, webdriverPath)
do.make_story(postPath)



# do.connect.close()
