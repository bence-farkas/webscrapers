# Birdeye scraper

## About
Birdeye scraper is web scraper that gathers information about cryptocurrency coins from the website birdeye.so. 
The information gathered is saved into a csv file. 
The script is written in Python and uses the Google Chrome web browser for the scraping process. 
The script performs the following actions:

- Connects to the website via Google Chrome  
- Gathers information about all the coins by going through each page  
- Sorts out coins that appear multiple times  
- Gets the token holders ratio for each coin  
- Writes the information gathered into a csv file

## Detailed script description
The script defines a class BirdEyeScraper with the following methods:

1. connect: This method opens a connection to the website using Google Chrome browser in headless mode.
2. set_page_data: This method saves the current page html.
3. set_page_number: This method sets the total number of pages in the tab.
4. set_next_btn: This method sets the next button, which will be used to navigate through the tab.
5. gather_all_data: This method gathers the gems information in the tab by scraping the HTML content of each page.
6. sort_out_the_same_coins: This method sorts out coins that appear multiple times in the results.
7. get_token_holders_ratio: This method retrieves the token holders ratio for a given set of coins.
Usage

- Create an instance of the BirdEyeScraper class.  
- Call the connect method to connect to the website.  
- Call the gather_all_data method to gather the data.  
- Call the sort_out_the_same_coins method to sort out the repeated coins.  
- Call the get_token_holders_ratio method to get the token holders ratio for a set of coins.

## Example usage

After the third-party modules installation, simply call:  

`python birdeye_scraper.py`  

Please note, you have to have Google Chrome installed on your system.