import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sqlite3
from telegram import Bot
import requests

# Initialize the SQLite database
conn = sqlite3.connect('room_listings.db')
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS room_listings (
        id INTEGER PRIMARY KEY,
        title TEXT,
        link TEXT
    )
''')
conn.commit()

import requests

def send_notification(message):
    TOKEN = ""
    CHAT_ID = 0

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()
        
        if result.get("ok"):
            print("Message sent successfully.")
        else:
            print(f"Failed to send message: {result.get('description')}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while sending the message: {str(e)}")
    
def scrape_and_save():
    try:
        # Configure the Selenium webdriver for Firefox in headless mode with cache disabled
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')  # Run in headless mode (no GUI)
        options.add_argument('--disk-cache-dir=/dev/null')  # Disable caching
        driver = webdriver.Firefox(executable_path='/path/to/geckodriver', options=options)
        driver.get('https://www.woko.ch/en/zimmer-in-zuerich')

        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Click on the "Free rooms" button
        free_rooms_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-gruppeid="98"]'))
        )
        free_rooms_button.click()

        # Wait for the page to load
        time.sleep(5)

        # Get the page source after clicking the button
        page_source = driver.page_source

        # DEBUGGING -> Testing the database notifications work correctly
        # Load the local HTML file for testing
        # with open('dummy_listing.html', 'r', encoding='utf-8') as file:
        #     page_source = file.read()

        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find and save room listings
        room_listings = soup.find_all('div', class_='inserat')

        for listing in room_listings:
            title = listing.find('h3').text
            date = listing.find('span').text
            address = listing.find('tr').find_next('tr').find_all('td')[1].text.strip()
            price = listing.find('div', class_='preis').text.strip()
            link = 'https://www.woko.ch' + listing.find('a')['href']


            # # FOR DEBUGGING PURPOSES
            notification_message = f"From {date}\n{address}\n{price}\n{link}"
            # Print the room listing to the console

            #Print the current time
            print("Printing to console at current time:", datetime.datetime.now())

            print(notification_message)
            print()
            # send_notification(notification_message)


            # Check if the listing is already in the database
            cursor.execute("SELECT * FROM room_listings WHERE title=?", (title,))
            existing_listing = cursor.fetchone()

            if not existing_listing:
                # If it's not in the database, add it
                cursor.execute("INSERT INTO room_listings (title, link) VALUES (?, ?)", (title, link))
                conn.commit()

                # Format the notification message
                notification_message = f"From {date}\n{address}\n{price}\n{link}"

                # Print the room listing to the console
                print("Printing to console...")
                print(notification_message)

                send_notification(notification_message)


    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print("Error at:", datetime.datetime.now(), " - ", error_message)
        print(error_message)
        send_notification(error_message)

    finally:
        # Close the browser, even in case of an error
        if 'driver' in locals() and driver:
            driver.quit()

if __name__ == '__main__':

    send_notification("WokoBot is running!")

    while True:
        scrape_and_save()
        time.sleep(60)  # Wait for 5 minutes before checking again
