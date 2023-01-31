from bs4 import BeautifulSoup
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
# source which helped a lot: https://github.com/mws75/UserName_by_Tag


class BirdEyeScraper:
    def __init__(self):
        self.url = "https://birdeye.so/find-gems"
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
        print("getting page")
        print(self.url)
        try:
            self.driver = webdriver.Chrome()
            self.driver.implicitly_wait(30)
            self.driver.get(self.url)
            print("successfully requested site")
        except:
            print("Unable to reach site")
            time.sleep(500)
            quit()
            return None

    def set_page_data(self):
        """
        Saves the current page html
        """
        self.page_data = BeautifulSoup(self.driver.page_source, 'html.parser')

    def set_page_number(self):
        """
        Sets the tab page number which will needed when we go through in it
        """
        spans = self.page_data.find_all("span")
        self.pages = -1
        for span in spans:
            if any("Page" in s for s in span.contents):
                self.pages = span.contents[0].split(" ")[-1]
                break

    def set_next_btn(self):
        """
        Sets the next button which we need when we want to go through the tab
        """
        self.btns = self.driver.find_elements(By.CLASS_NAME, "ant-btn.ant-btn-default.sc-dGXBhE.doBqGu")
        self.btn_idx = -1
        for i, btn in enumerate(self.btns):
            if btn.accessible_name == "right":
                self.btn_idx = i

    def gather_all_data(self):
        """
        Gather the gems in the tab
        """
        for i in range(int(self.pages)):
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            trs = soup.find_all("tr")
            for tr in trs:
                cells = tr.find_all('td')
                # Extract the text from each cell and store it in a list
                row_data = [cell.text for cell in cells]
                self.raw_data.append(row_data)
            self.btns[self.btn_idx].click()
            self.driver.implicitly_wait(10)

    def sort_out_the_same_coins(self):
        """
        Some coins exist multiple times which we want to sort out
        """
        coin_names = []
        sorted_raw_data = []
        for coin in self.raw_data:
            if len(coin) == 0:
                continue
            if coin[1] not in coin_names:
                coin_names.append(coin[1])
                sorted_raw_data.append(coin)
        self.raw_data = sorted_raw_data


    def parse_data(self):
        """
        Parse in raw data
        TODO: make it configurable
        """
        potential_coins = []
        for coin in self.raw_data:
            if len(coin) == 0:
                continue
            if "$" in coin[-1]:
                fdmc_str = coin[-1].split("$")[1]
                if len(fdmc_str) == 0:
                    continue
                multiplier = 1
                if "M" in fdmc_str:
                    multiplier = 1000000
                elif "B" in fdmc_str:
                    multiplier = 1000000000
                elif "K" in fdmc_str:
                    multiplier = 1000
                fdmc = float(fdmc_str[:-1]) * multiplier
                coin[17] = fdmc

                if fdmc <= 100000:
                    potential_coins.append(coin)
        potential_coins = sorted(potential_coins, key=lambda row: row[17], reverse=True)

        return potential_coins

    def write2csv(self, data):
        """
        :param data:
        :return:
        """
        fields = ["Number", "Token", "Trending", "Price", "30m", "1h",
                  "2h", "24h", "TVL", "24h_vol", "24h", "24h_trades",
                  "24h_views", "Watchers", "Holders", "Markets", "Total_supply", "FDMC"]
        with open("output.csv", "w") as file:
            write = csv.writer(file)
            write.writerow(fields)
            write.writerows(data)
        print("Data saved!")

    def find_gems(self):
        """

        :return:
        """
        self.connect()
        if self.driver is None:
            return
        self.set_page_data()
        # Get page number:
        self.set_page_number()
        # Get next button
        self.set_next_btn()
        # Gather all data from the subpages
        self.gather_all_data()
        # parse in data
        self.sort_out_the_same_coins()
        potential_coins = self.parse_data()
        self.write2csv(potential_coins)


scraper = BirdEyeScraper()
scraper.find_gems()
