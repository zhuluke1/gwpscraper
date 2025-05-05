import random
import time
import requests
import json
import html
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import browsercookie
import argparse
from typing import Dict, List, Optional, Union
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import re
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

'''optional arguments:
  -h, --help            show this help message and exit
  -o ORIGIN, --origin ORIGIN
                        Origin IATA airport code.
  -d DATES, --dates DATES
                        Show flights for: Today: 1 Tommorrow: 2 Both: 3
  -c, --cjs             Use browser cookies.
  -r RESUME, --resume RESUME
                        Index of airport to resume from. Use index 21 to only
                        search for contiguous US destinations.'''
 
# Global Variables
destination_count = 0
destinations_avail: Dict[str, str] = {}
roundtrip_avail: Dict[str, str] = {}

# Updated destinations dictionary
all_destinations = {
    'ANU': 'Antigua and Barbuda', 
    'NAS': 'Bahamas', 
    'BZE': 'Belize', 
    'LIR': 'Costa Rica', 
    'SJO': 'San José', 
    'PUJ': 'Punta Cana, DR', 
    'SDQ': 'Santo Domingo, DR', 
    'SAL': 'El Salvador', 
    'GUA': 'Guatemala', 
    'KIN': 'Jamaica', 
    'MBJ': 'St. James', 
    'SJD': 'Los Cabos, MX', 
    'GDL': 'Guadalajara, MX', 
    'PVR': 'Puerto Vallarta, MX', 
    'MTY': 'Monetrrey, MX', 
    'CUN': 'Cancun, MX', 
    'CZM': 'Cozumel, MX',  
    'SXM': 'St. Maarten', 
    'BQN': 'Aguadilla, Puerto Rico', 
    'PSE': 'Ponce, Puerto Rico', 
    'SJU': 'San Juan, Puerto Rico',
    'PHX': 'Phoenix', 
    'XNA': 'Arkansas', 
    'LIT': 'Little Rock, AR', 
    'OAK': 'Oakland', 
    'ONT': 'Ontario', 
    'SNA': 'Orange County', 
    'SMF': 'Sacramento', 
    'SAN': 'San Diego', 
    'SFO': 'San Francisco', 
    'DEN': 'Colorado', 
    'BDL': 'Connecticut', 
    'FLL': 'Fort Lauderdale, FL', 
    'RSW': 'Fort Myers, FL', 
    'JAX': 'Jacksonville, FL', 
    'MIA': 'Miami, FL', 
    'MCO': 'Orlando, FL', 
    'PNS': 'Pensacola, FL', 
    'SRQ': 'Sarasota, FL', 
    'TPA': 'Tampa, FL', 
    'PBI': 'West Palm Beach, FL', 
    'ATL': 'Atlanta, Georgia', 
    'SAV': 'Savannah, Georgia', 
    'BMI': 'Illinois', 
    'MDW': 'Chicago',
    'ORD': 'Chicago', 
    'IND': 'Indiana', 
    'CID': 'Cedar rapids, Iowa', 
    'DSM': 'Des Moines, Iowa', 
    'CVG': 'Kentucky', 
    'MSY': 'Louisiana', 
    'PWM': 'Maine', 
    'BWI': 'Maryland', 
    'BOS': 'Massachusetts', 
    'DTW': 'Michigan', 
    'GRR': 'Grand Rapids, MI', 
    'MSP': 'Minnesota', 
    'MCI': 'Missouri', 
    'STL': 'St. Louis', 
    'MSO': 'Montana', 
    'OMA': 'Nebraska', 
    'LAS': 'Las Vegas', 
    'TTN': 'New Jersey', 
    'BUF': 'New York', 
    'ISP': 'Long Island/Islip', 
    'SWF': 'Newburgh', 
    'LGA': 'New York City', 
    'SYR': 'Syracuse', 
    'CLT': 'North Carolina', 
    'RDU': 'Raleigh, NC', 
    'FAR': 'North Dakota', 
    'CLE': 'Ohio', 
    'CMH': 'Columbus', 
    'OKC': 'Oklahoma', 
    'PDX': 'Oregon', 
    'MDT': 'Pennsylvania', 
    'PHL': 'Philadelphia', 
    'PIT': 'Pittsburgh', 
    'CHS': 'Charleston, South Carolina', 
    'MYR': 'Myrtle Beach, SC', 
    'TYS': 'Tennessee', 
    'MEM': 'Memphis', 
    'BNA': 'Nashville', 
    'AUS': 'Austin, Texas', 
    'DFW': 'Dallas/Fort Worth', 
    'ELP': 'El Paso', 
    'IAH': 'Houston',
    'HOU': 'Houston', 
    'SAT': 'San Antonio', 
    'STT': 'U.S. Virgin Islands', 
    'SLC': 'Utah', 
    'DCA': 'Virginia', 
    'ORF': 'Norfolk', 
    'SEA': 'Washington', 
    'GRB': 'Wisconsin', 
    'MSN': 'Madison', 
    'MKE': 'Milwaukee'
}

def create_driver() -> webdriver.Chrome:
    """Create a Chrome driver instance."""
    try:
        options = Options()
        # Remove headless mode to allow manual verification
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')  # Start with maximized window
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Add additional options to make detection harder
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Add more realistic browser behavior
        options.add_argument('--enable-javascript')
        options.add_argument('--enable-cookies')
        options.add_argument('--enable-plugins')
        options.add_argument('--enable-sync')
        options.add_argument('--enable-automation')
        
        # Add user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36')
        
        # Create driver with service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        # Maximize window
        driver.maximize_window()
        
        # Add additional properties to make detection harder
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        })
        
        # Disable webdriver mode
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        return driver
    except Exception as e:
        logger.error(f"Error creating driver: {str(e)}")
        raise

def get_flight_html(
    origin: str,
    date: datetime,
    driver: webdriver.Chrome,
    roundtrip: int,
    start_index: int = 0,
    destinations: Dict[str, str] = all_destinations
) -> None:
    """Get flight availability for given origin and date using Selenium."""
    date_str = date.strftime("%b-%d,-%Y").replace("-", "%20")
    destination_keys = list(destinations.keys())
    
    try:
        # First, visit the main page
        logger.info("Accessing main page...")
        driver.get("https://www.flyfrontier.com/")
        
        # Wait for manual verification if needed
        logger.info("Please complete any verification if prompted...")
        logger.info("The browser window should be visible. Complete any verification steps and then press Enter...")
        input("Press Enter after completing verification...")
        
        # Add a random delay to simulate human behavior
        time.sleep(random.uniform(3.0, 5.0))
        logger.info("Successfully accessed main page")
        
        for i in range(start_index, len(destination_keys)):
            try:
                dest = destination_keys[i]
                
                if dest == origin:
                    logger.info(f"Skipping identical origin and destination: {origin}")
                    continue
                
                logger.info(f"Checking flights from {origin} to {dest} ({i + 1}/{len(destination_keys)})")
                
                # Get schedule data
                schedule_url = f"https://booking.flyfrontier.com/Flight/RetrieveSchedule?calendarSelectableDays.Origin={origin}&calendarSelectableDays.Destination={dest}"
                driver.get(schedule_url)
                
                # Check for verification page
                if "verify" in driver.current_url.lower() or "captcha" in driver.current_url.lower():
                    logger.info("Verification required. Please complete the verification...")
                    input("Press Enter after completing verification...")
                    driver.get(schedule_url)
                
                # Add random delay
                time.sleep(random.uniform(2.0, 4.0))
                
                try:
                    # Wait for the response to be loaded
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "pre"))
                    )
                    
                    # Get the JSON response
                    schedule_data = json.loads(driver.find_element(By.TAG_NAME, "pre").text)
                    disabled_dates = schedule_data['calendarSelectableDays']['disabledDates']
                    last_available_date = schedule_data['calendarSelectableDays']['lastAvailableDate']
                    
                    formatted_date = date.strftime('%m/%d/%Y')
                    
                    if formatted_date in disabled_dates or last_available_date == '0001-01-01 00:00:00':
                        logger.info(f"No flights available on {formatted_date} from {origin} to {dest}")
                        continue
                        
                except (TimeoutException, json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error getting schedule data: {str(e)}")
                    time.sleep(random.uniform(5.0, 8.0))  # Longer delay on error
                    continue
                
                # Add longer delay between requests
                time.sleep(random.uniform(3.0, 5.0))
                
                # Get flight data
                url = f"https://booking.flyfrontier.com/Flight/InternalSelect?o1={origin}&d1={dest}&dd1={date_str}&ADT=1&mon=true&promo="
                driver.get(url)
                
                # Check for verification page again
                if "verify" in driver.current_url.lower() or "captcha" in driver.current_url.lower():
                    logger.info("Verification required. Please complete the verification...")
                    input("Press Enter after completing verification...")
                    driver.get(url)
                
                # Add random delay
                time.sleep(random.uniform(2.0, 4.0))
                
                try:
                    # Wait for the response to be loaded
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "pre"))
                    )
                    
                    # Get the JSON response
                    flight_data = json.loads(driver.find_element(By.TAG_NAME, "pre").text)
                    
                    if flight_data:
                        origin_success = extract_json(flight_data, origin, dest, date, roundtrip)
                        
                        if roundtrip == 1 and origin_success:
                            new_dest = {origin: all_destinations[origin]}
                            get_flight_html(dest, date + timedelta(days=1), driver, -1, 0, new_dest)
                            roundtrip = 1
                            
                except (TimeoutException, json.JSONDecodeError) as e:
                    logger.error(f"Error getting flight data: {str(e)}")
                    time.sleep(random.uniform(5.0, 8.0))  # Longer delay on error
                    continue
                    
            except KeyboardInterrupt:
                logger.info("\nScript interrupted by user. Saving progress...")
                print_dests(origin)
                driver.quit()
                sys.exit(0)
            except Exception as e:
                logger.error(f"Error processing {origin} to {dest}: {str(e)}")
                time.sleep(random.uniform(5.0, 8.0))  # Longer delay on error
                continue
                
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        try:
            driver.quit()
        except:
            pass

def extract_json(flight_data: dict, origin: str, dest: str, date: datetime, roundtrip: int) -> bool:
    """Extract and process flight data."""
    try:
        # Check if we have valid journey data
        if not flight_data.get('journeys'):
            logger.info(f"No journey data available for {origin} to {dest}")
            return False
            
        flights = flight_data['journeys'][0].get('flights', [])
        if not flights:
            logger.info(f"No flights available for {origin} to {dest}")
            return False
            
        go_wild_count = 0
        print(f"\n{'{} to {}: {}'.format(origin, dest, all_destinations[dest]) if roundtrip != -1 else '**Return flight'} available:")
        
        for flight in flights:
            # Check if this is a Go Wild flight
            if not flight.get("isGoWildFareEnabled"):
                continue
                
            go_wild_count += 1
            info = flight['legs'][0]
            
            # Extract and format flight details
            flight_number = flight.get('flightNumber', 'N/A')
            departure_time = info.get('departureDateFormatted', 'N/A')
            arrival_time = info.get('arrivalDateFormatted', 'N/A')
            duration = flight.get('duration', 'N/A')
            price = flight.get('goWildFare', 'N/A')
            seats = flight.get('goWildFareSeatsRemaining', 'N/A')
            
            print(f"\nFlight {go_wild_count}:")
            print(f"Flight Number: {flight_number}")
            print(f"Departure: {departure_time}")
            print(f"Arrival: {arrival_time}")
            print(f"Duration: {duration}")
            print(f"Go Wild Price: ${price}")
            if seats is not None:
                print(f"Go Wild Seats Remaining: {seats}")
            print("-" * 50)
    
        if go_wild_count == 0:
            print(f"No {'next day return ' if roundtrip==-1 else ''}Go Wild flights from {origin} to {dest}")
            return False
            
        if roundtrip == -1:
            roundtrip_avail[origin] = all_destinations.get(origin)
        else:
            destinations_avail[dest] = all_destinations.get(dest)
            
        print(f"\n{origin} to {dest}: {go_wild_count} GoWild {'return ' if roundtrip==-1 else''}flights available for {date.strftime('%A, %m-%d-%y')}")
        return True
        
    except Exception as e:
        logger.error(f"Error extracting flight data: {str(e)}")
        return False

def print_dests(origin: str) -> None:
    """Print available destinations."""
    print(f"\n{len(destinations_avail)} destinations found from {origin}:")
    for dest, name in destinations_avail.items():
        print(f"{'**' if dest in roundtrip_avail else ''}{dest}: {name}")
    print("** = next day return flight available")

def main():
    parser = argparse.ArgumentParser(description='Check Frontier Airlines Go Wild Pass availability.')
    parser.add_argument('-o', '--origin', type=str, required=True, help='Origin IATA airport code.')
    parser.add_argument('-t', '--roundtrip', type=int, default=0, help='Search for roundtrip/return flights for tomorrow. 1 for yes, default is no')
    parser.add_argument('-r', '--resume', type=int, default=0, help='Index of airport to resume from. Use index 21 to only search for contiguous US destinations.')

    args = parser.parse_args()
    origin = args.origin.upper()
    fly_date = datetime.today()  # Always use today's date
    resume = args.resume
    roundtrip = args.roundtrip

    print(f"\nFlights for {fly_date.strftime('%A, %m-%d-%y')}:")
    
    driver = None
    try:
        driver = create_driver()
        get_flight_html(origin, fly_date, driver, roundtrip, resume)
    except Exception as e:
        logger.error(f"Error creating driver: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print_dests(origin)

if __name__ == "__main__":
    main()