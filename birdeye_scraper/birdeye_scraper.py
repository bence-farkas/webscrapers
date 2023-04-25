import csv
import datetime
import yaml
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from tqdm import tqdm
# source which helped a lot: https://github.com/mws75/UserName_by_Tag


class BirdEyeScraper:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.chain = self.config["chain"]
        self.url = f"https://birdeye.so/find-gems?chain={self.chain}"
        self.driver = None
        self.page_data = None
        self.pages = -1
        self.btn_idx = -1
        self.btns = None
        self.raw_data = []

    def connect(self):
        """
        Connects to the url via Google Chrome browser
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.config["implicit_wait"])
            self.driver.get(self.url)
        except WebDriverException as e:
            print(e.__dict__["msg"])
            self.driver.quit()

    def set_page_data(self):
        """
        Saves the current page html
        """
        self.page_data = BeautifulSoup(self.driver.page_source, 'html.parser')

    def set_page_number(self):
        """
        Sets the tab page number which will be needed when we go through it
        """
        wait = WebDriverWait(self.driver, self.config["explicit_wait"])
        try:
            span_element = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(., 'Page')]")))
            self.pages = int(span_element.text.split(" ")[-1].replace(',', ''))
        except TimeoutException:
            print("Timeout waiting for the page number span element to load")
            self.pages = -1

    def set_next_btn(self):
        """
        Sets the next button which we need when we want to go through the tab
        """
        self.btns = self.driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(self.btns):
            if btn.accessible_name == "right":
                self.btn_idx = i
                break

    def gather_all_data(self):
        """
        Gather the gems in the tab
        """
        for _, i in tqdm(enumerate(range(self.pages)), total=self.pages):
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            trs = soup.find_all("tr")
            for tr in trs:
                cells = tr.find_all('td')
                # Extract the text from each cell and store it in a list
                row_data = [cell.text for i, cell in enumerate(cells) if i != 2]
                if len(row_data) > 0 and '\xa0' not in row_data:
                    divs = tr.find_all('div')
                    token_url = "https://birdeye.so" + divs[1].contents[1].contents[0].attrs['href']
                    row_data.append(token_url)
                    self.raw_data.append(row_data)
            self.btns[self.btn_idx].click()
            self.driver.implicitly_wait(self.config["implicit_wait"])

    def sort_out_the_same_coins(self):
        """
        Some coins exist multiple times which we want to sort out
        """
        coin_names = set()
        sorted_raw_data = []

        for coin in self.raw_data:
            if len(coin) > 0 and '\xa0' not in coin and coin[-1] not in coin_names:
                coin_names.add(coin[-1])
                sorted_raw_data.append(coin)
        self.raw_data = sorted_raw_data

    def get_token_holders_ratio(self, coins):
        """

        :param coins:
        :return:
        """
        updated_coins = []
        for _, coin in tqdm(enumerate(coins), total=len(coins)):
            holders_ratio = []
            potential_coin = True
            url = coin[-1]
            self.driver.get(url)
            self.set_page_data()
            tbodies = self.page_data.find_all("tbody")
            if len(tbodies) == 0:
                continue
            holder_tbody = tbodies[0]
            holder_tbody.find_all("tr")
            trs = holder_tbody.find_all("tr")
            for tr in trs:
                cells = tr.find_all('td')
                row_data = [cell.text for cell in cells]
                if len(row_data) == 0 or 'No dat' in row_data[-1][:-1]:
                    potential_coin = False
                    break
                ratio = float(row_data[-1][:-1].replace(',', ''))
                holders_ratio.append(ratio)
                if ratio >= self.config["max_token_share"]:
                    potential_coin = False
                    break
            if potential_coin:
                coin.append(holders_ratio)
                updated_coins.append(coin)
        return updated_coins

    def parse_data(self):
        """
        Parse in raw data
        TODO: make it configurable
        """
        print(datetime.datetime.now(), "Parsing data...")

        def parse_fdmc(fdmc_str):
            if len(fdmc_str) == 0:
                return None
            multiplier = 1
            if "M" in fdmc_str:
                multiplier = 1000000
            elif "B" in fdmc_str:
                multiplier = 1000000000
            elif "K" in fdmc_str:
                multiplier = 1000
            return float(fdmc_str[:-1]) * multiplier

        potential_coins = [coin[0:17] + [parse_fdmc(coin[-2].split("$")[1])] + coin[18:] for coin in self.raw_data if
                            len(coin) > 0 and "$" in coin[-2] and self.config["min_fdmc"] <=
                            parse_fdmc(coin[-2].split("$")[1]) <= self.config["max_fdmc"]]

        if len(potential_coins) > 0:
            potential_coins = sorted(potential_coins, key=lambda row: row[17], reverse=True)

        return potential_coins

    def write2csv(self, data, mode, outfile_name):
        """
        :param fields:
        :param mode:
        :param outfile_name:
        :param data:
        :return:
        """
        fields = ["Number", "Token", "Trending", "Price", "30m", "1h",
                  "2h", "24h", "TVL", "24h_vol", "24h", "24h_trades",
                  "24h_views", "Watchers", "Holders", "Markets", "Total_supply", "FDMC", "TOKEN_URL", "HOLDERS_RATIO"]
        with open(outfile_name, mode) as file:
            write = csv.writer(file)
            write.writerow(fields)
            write.writerows(data)

    def load_config(self, file_path: str):
        """
        Loads yaml configuration file
        :param file_path: The path of the configuration file
        :return:
        """
        with open(file_path, "r") as stream:
            try:
                config = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        return config

    def find_gems(self):
        """
        """
        print(datetime.datetime.now(), "Connecting to the following site: ", self.url)
        self.connect()
        if self.driver is None:
            print(datetime.datetime.now(), "Failed to load webpage! Exiting now.")
            return
        print(datetime.datetime.now(), "Successfully connected!")
        print(datetime.datetime.now(), "Getting page data...")
        self.set_page_data()
        # Get page number:
        self.set_page_number()
        if self.pages == -1:
            print(datetime.datetime.now(), "Failed to load webpage! Exiting now.")
            return
        # Get next button
        self.set_next_btn()
        print(datetime.datetime.now(), "Success!")
        # Gather all data from the subpages
        print(datetime.datetime.now(), "Gather all token info, please wait...")
        self.gather_all_data()
        print(datetime.datetime.now(), "Success!")
        # parse in data
        print(datetime.datetime.now(), "Sorting potential coins, please wait...")
        self.sort_out_the_same_coins()
        potential_coins = self.parse_data()
        potential_coins = self.get_token_holders_ratio(potential_coins)
        self.driver.close()
        self.driver.quit()
        print(datetime.datetime.now(), "Success!")
        print(datetime.datetime.now(), "Saving data to csv...")
        self.write2csv(potential_coins, mode="w", outfile_name=self.config["output_path"])
        print(datetime.datetime.now(), "Data saved to:", self.config["output_path"], "Bye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", type=str, help="The configuration path")
    args = parser.parse_args()

    scraper = BirdEyeScraper(args.config)
    scraper.find_gems()
