from datetime import datetime, timedelta
import time
import traceback
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
from urllib.parse import urlparse
from urllib.parse import parse_qs
from filelock import FileLock


ACCOUNT_DETAILS_FILE_PATH = "C:\\Users\\babar\\Desktop\\g2g-delivery-bot-modified\\accounts_info.xlsx"


class G2GDeliveryBot:
    def __init__(self, profile):
        self.game_details_search = {
            "Valorant": self.get_valorant_account_details,
            "Overwatch (Global)": None,
            "Overwatch 2": self.get_overwatch2_account_details,
            "League of Legends": None,
            "Counter-Strike 2": None,
            "Tom Clancys Rainbow Six Siege": self.get_rainbow_seige_account_details,
            "Call of Duty": None,
            "GTA 5 Online": self.get_gta5_account_details,
            "Genshin Impact": None,
            "Hay Day (Global)": None,
            "Honkai: Star Rail": None,
            "Mobile Legends": None,
            "One Piece Bounty Rush": None,
            "Apex Legends": None,
            "PUBG Mobile": None,
            "Rocket League": None,
            "Summoners War": None,
            "DayZ": None,
            "Dota 2": None,
            "Sea of Thieves": None,
        }

        self.lock = FileLock(ACCOUNT_DETAILS_FILE_PATH + ".lock")
        self.profile = profile
        self.options = Options()
        self.options.add_argument(
            f"--user-data-dir=C:\\Users\\babar\\Desktop\\Profiles\\{self.profile}"
        )
        self.options.add_argument(f"--profile-directory={self.profile}")
        # self.options.add_argument("--headless=new")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("enable-features=NetworkServiceInProcess")
        self.options.page_load_strategy = "eager"
        self.options.add_argument("--dns-prefetch-disable")
        # self.options.add_argument("enable-automation")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-browser-side-navigation")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("log-level=3")
        self.options.add_argument("--ignore-certificate-errors")
        self.options.add_experimental_option("extensionLoadTimeout", 60000)
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=self.options
        )
        self.driver.set_page_load_timeout(30)
        self.driver.set_script_timeout(60)

        self.driver.implicitly_wait(7)
        self.orders_to_deliver = set()
        self.orders_to_remove = set()
        self.links_to_check_orders = [
            "https://www.g2g.com/g2g-user/sale?status=preparing",
            "https://www.g2g.com/g2g-user/sale?status=delivering",
        ]

    def get_orders(self):
        for link in self.links_to_check_orders:
            self.driver.get(link)
            try:

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div//a[contains(@href,'item')]")
                    )
                )
                for anchor_elem in self.driver.find_elements(
                    By.XPATH, "//div//a[contains(@href,'item')]"
                ):
                    order_link = anchor_elem.get_attribute("href")
                    self.orders_to_deliver.add(order_link)
            except:
                continue

    def get_gta5_account_details(self, game_name, game_details):
        platform = game_details[0]
        level = game_details[1]
        money_owned = game_details[2]
        return self.search_from_file(
            game_name, field_1=platform, field_2=level, field_3=money_owned
        )

    def get_overwatch2_account_details(self, game_name, game_details):
        tank_rank = game_details[0]
        damage_rank = game_details[3]
        support_rank = game_details[4]
        return self.search_from_file(
            game_name,
            field_1=tank_rank,
            field_2=damage_rank,
            field_3=support_rank,
        )

    def get_valorant_account_details(self, game_name, game_details):
        server = game_details[0]
        rank = game_details[2]
        return self.search_from_file(game_name, field_1=server, field_2=rank)

    def get_rainbow_seige_account_details(self, game_name, game_details):
        platform = game_details[0]
        rank = game_details[1]
        return self.search_from_file(game_name, field_1=platform, field_2=rank)

    def search_from_file(self, game_name, **kwargs):
        with self.lock.acquire():
            print("accessing data file...")
            df = pd.read_excel(ACCOUNT_DETAILS_FILE_PATH, na_filter=False)
            df["Is Sold"] = df["Is Sold"].astype(bool)
            for index, row in df.iterrows():
                # print(row["game"], game_name, row["game"] == game_name)
                # print(row["Is Sold"], not row["Is Sold"])
                # print([(row[key],kwargs[key])for key in kwargs],  all(row[key] == kwargs[key] for key in kwargs))
                if (
                    row["game"] == game_name
                    and not row["Is Sold"]
                    and all(row[key] == kwargs[key] for key in kwargs)
                ):
                    print("Checking...")
                    if (
                        not row["Being Sold By"]
                        or pd.isna(row["Being Sold By"])
                        or row["Being Sold By"] == self.profile
                    ):
                        df.loc[index, "Being Sold By"] = self.profile
                        print("data file work completed!!!")
                        df.to_excel(ACCOUNT_DETAILS_FILE_PATH, index=False)
                        return row.to_dict(), index

        print("Details not Found!!!")

    def save_order_delivery_info(self, index, order_id):
        with self.lock.acquire():
            print("accessing data file...")
            df = pd.read_excel(ACCOUNT_DETAILS_FILE_PATH, na_filter=False)
            df["Is Sold"] = df["Is Sold"].astype(bool)

            df.loc[index, "Is Sold"] = True
            df.loc[index, "Order ID"] = order_id
            df.to_excel(ACCOUNT_DETAILS_FILE_PATH, index=False)

    def handle_order_delivery(self, order_link):
        self.driver.get(order_link)
        time.sleep(2)

        # If awaiting for buyer's confirmation, then skip
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//div[contains(text(),"Awaiting buyer\'s confirmation")] | //div[contains(text(),"Report cancel")]',
                    )
                )
            )
            self.driver.find_element(
                By.XPATH,
                '//div[contains(text(),"Awaiting buyer\'s confirmation")] | //div[contains(text(),"Report cancel")]',
            )
            print("Order already Delivered !\n" + "-" * 50)
            return
        except:
            print("New Order")

        view_details_btn = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//span[contains(text(),'View details')]/../../../..",
                )
            )
        )
        self.driver.execute_script("arguments[0].click();", view_details_btn)

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//span[contains(text(),'Start deliver')]/../../..",
                    )
                )
            )
            start_delivery_btn = self.driver.find_element(
                By.XPATH, "//span[contains(text(),'Start deliver')]/../../.."
            )
            self.driver.execute_script("arguments[0].click();", start_delivery_btn)
        except:
            print("Not click on Start delivery button")

        time.sleep(2)

        order_id = order_link.split("/")[-1]
        game_name = self.driver.find_element(
            By.XPATH, "//span[contains(@data-attr,'order-item-brand')]"
        ).text
        game_info_list = self.driver.find_elements(
            By.XPATH, "//span[contains(@data-attr,'order-item-offer-attributes')]"
        )
        game_info_list = list(map(lambda x: x.text, game_info_list))

        print(f"delivering account details for {game_name = } with {game_info_list = }")

        close_btn = self.driver.find_element(
            By.XPATH, "//span//i[contains(text(),'close')]/../../.."
        )
        self.driver.execute_script("arguments[0].click();", close_btn)

        try:
            start_submit_btn = WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(),'Submit account')]")
                )
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoViewIfNeeded(true);", start_submit_btn
            )
            self.driver.execute_script("arguments[0].click();", start_submit_btn)
        except:
            return
        time.sleep(3)

        # Extracting delivery details and fetching account details to deliver
        details = self.game_details_search[game_name](game_name, game_info_list)

        if not details:
            print("Account delivery details not found!!!")
            return None

        account_details, index = details

        self.fill_account_details_form(account_details)

        try:
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(text(),'Your game account has been added successfully.')]",
                    )
                )
            )
            ok_btn = self.driver.find_element(
                By.XPATH, "//span[contains(text(),'Ok')]/../.."
            )
            self.driver.execute_script("arguments[0].click();", ok_btn)

        except:
            print("Checking the order again")
            if self.handle_order_delivery(order_link):
                return

        print(
            f"Message from {self.profile} bot:\nAccount details being delivered...\n{details}\n"
            + "-" * 50
        )
        time.sleep(3)
        print(
            f"Message from {self.profile} bot:\nDelivery done for {order_link}\n"
            + "-" * 50
        )

        self.save_order_delivery_info(index, order_id)
        return True

    def fill_account_details_form(self, account_details):
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@title='Account ID']//input")
            )
        ).send_keys(account_details["Account ID"])

        self.driver.find_element(By.XPATH, "//div[@title='Password']//input").send_keys(
            account_details["Account Password"]
        )
        self.driver.find_element(
            By.XPATH, "//div[@title='Account Country']//input"
        ).send_keys(account_details["Account Country"])
        self.driver.find_element(
            By.XPATH, "//div[@title='Account Email']//input"
        ).send_keys(account_details["Email Account"])
        self.driver.find_element(
            By.XPATH, "//div[@title='Email Password']//input"
        ).send_keys(account_details["Email Password"])
        self.driver.find_element(
            By.XPATH, "//div[@title='Additional Note']//textarea"
        ).send_keys(account_details["Additional Note"])

        submit_btn = WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Submit']/../../.."))
        )
        self.driver.execute_script("arguments[0].click();", submit_btn)

    def run(self):
        # start_time = datetime.now()
        # while True:
            # if datetime.now() >= start_time + timedelta(minutes=30):
            #     self.driver.quit()
            #     time.sleep(3)
            #     self.driver = webdriver.Chrome(
            #         service=Service(ChromeDriverManager().install()),
            #         options=self.options,
            #     )
            #     start_time = datetime.now()
            try:
                self.get_orders()
                self.orders_to_deliver -= self.orders_to_remove
                self.orders_to_remove = set()
                for order_link in self.orders_to_deliver:
                    self.handle_order_delivery(order_link)
                    self.orders_to_remove.add(order_link)
                    time.sleep(1)
                # break
            except Exception as e:
                print(f"Message from {self.profile} bot:\n{e}\n" + "-" * 50)
                print(traceback.format_exc())
                self.driver.quit()
                time.sleep(5)
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=self.options,
                )
            # time.sleep(5)
