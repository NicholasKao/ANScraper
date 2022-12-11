# coding: utf-8
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime as dt
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import numpy as np
import configparser
import time
import calendar
import pymysql


class ANScraper:

    def __init__(self, config_file='config.txt'):

        # Load and read config
        self.config = configparser.RawConfigParser()
        self.config.read(config_file)

        # Create Chrome driver instance
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito")
        self.browser = webdriver.Chrome(ChromeDriverManager().install())

    def login(self):
        # Logging In
        self.browser.get('https://www.actionnetwork.com/login')
        self.browser.find_element_by_id("email").send_keys(
            self.config.get('ActionNetwork', 'email'))
        self.browser.find_element_by_id("password").send_keys(
            self.config.get('ActionNetwork', 'password'))
        self.browser.find_element_by_id('login-submit').click()
        # Wait for new page to load before moving on to make sure page loaded
        time.sleep(2)

    def quit(self):
        self.browser.quit()

    def scrape_data(self, date, options=[], backfilling = False):
        day_dict = {'Mon':'Monday','Tue':'Tuesday', 'Wed':'Wednesday','Thu':'Thursday','Fri':'Friday','Sat':'Saturday','Sun':'Sunday'}
        month_dict = {'Jan':1,'Feb':2,'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
        time.sleep(2)
        # Scrape the Header and Spreads Table
        odds_data = []
        try:
            odds_table = self.browser.find_element_by_tag_name('tbody')
            table_rows = odds_table.find_elements_by_tag_name('tr')
            for row in table_rows:
                game_data = {}
                game_info = row.find_element_by_class_name('public-betting__game-info').text.split('\n')
                if game_info[0] == 'PPD':
                    game_data['WeekDay'] = 'PPD'
                    game_data['Month'] = 'PPD'
                    game_data['Day'] = 'PPD'
                    game_data['Time'] = 'PPD'
                    game_data['Year'] = 'PPD'
                    game_data['AwayRot'] = None
                    game_data['AwayTeam'] = game_info[1]
                    game_data['HomeRot'] = None
                    game_data['HomeTeam'] = game_info[2]
                    continue
                elif game_info[0] == 'CANCELLED':
                    game_data['WeekDay'] = 'PPD'
                    game_data['Month'] = 'PPD'
                    game_data['Day'] = 'PPD'
                    game_data['Time'] = 'PPD'
                    game_data['Year'] = 'PPD'
                    if len(game_info) == 3:
                        game_data['AwayRot'] = None
                        game_data['AwayTeam'] = game_info[1]
                        game_data['HomeRot'] = None
                        game_data['HomeTeam'] = game_info[2]
                    else:
                        game_data['AwayRot'] = game_info[1]
                        game_data['AwayTeam'] = game_info[2]
                        game_data['HomeRot'] = game_info[3]
                        game_data['HomeTeam'] = game_info[4]
                    continue
                elif game_info[0] == 'TBD':
                    game_data['WeekDay'] = 'TBD'
                    game_data['Month'] = 'TBD'
                    game_data['Day'] = 'TBD'
                    game_data['Time'] = 'TBD'
                    game_data['Year'] = 'TBD'
                    if len(game_info) == 3:
                        game_data['AwayRot'] = None
                        game_data['AwayTeam'] = game_info[1]
                        game_data['HomeRot'] = None
                        game_data['HomeTeam'] = game_info[2]
                    else:
                        game_data['AwayRot'] = game_info[1]
                        game_data['AwayTeam'] = game_info[2]
                        game_data['HomeRot'] = game_info[3]
                        game_data['HomeTeam'] = game_info[4]
                else:
                    try:
                        if backfilling:
                            game_data['WeekDay'] = day_dict[date.split(' ')[0]]
                            game_data['Month'] = month_dict[date.split(' ')[1]]
                            game_data['Day'] = pd.to_numeric(date.split(' ')[2])
                            game_data['Time'] = game_info[0].split(', ')[1]
                        else:
                            game_data['WeekDay'] = day_dict[game_info[0].split(' ')[0]]
                            game_data['Month'] = game_info[0].split(',')[0].split(' ')[1].split('/')[0]
                            game_data['Day'] = game_info[0].split(',')[0].split(' ')[1].split('/')[1]
                            game_data['Time'] = game_info[0].split(', ')[1]
                    except Exception as e: ## error occurs when game is current day
                        game_data['WeekDay'] = calendar.day_name[dt.today().weekday()]
                        game_data['Month'] = dt.today().date().month
                        game_data['Day'] = dt.today().date().day
                        game_data['Time'] = game_info[0]
                    game_data['Year'] = dt.today().date().year ## fix this, need to grab actual year
                    if len(game_info) == 3:
                        game_data['AwayRot'] = None
                        game_data['AwayTeam'] = game_info[1]
                        game_data['HomeRot'] = None
                        game_data['HomeTeam'] = game_info[2]
                    else:
                        game_data['AwayRot'] = game_info[1]
                        game_data['AwayTeam'] = game_info[2]
                        game_data['HomeRot'] = game_info[3]
                        game_data['HomeTeam'] = game_info[4]
                
                try:
                    open_info = row.find_element_by_class_name('public-betting__open-container').text
                    game_data[f'{options[0][0]}Open'] = open_info.split('\n')[0].replace('+','').replace('PK','0')
                    game_data[f'{options[0][1]}Open'] = open_info.split('\n')[1].replace('+','').replace('PK','0')
                except:
                    game_data[f'{options[0][0]}Open'] = None
                    game_data[f'{options[0][1]}Open'] = None
                    game_data[f'CurrentBest{options[0][0]}Line'] = None
                    game_data[f'CurrentBest{options[0][1]}Line'] = None
                    game_data[f'CurrentBest{options[0][0]}LineJuice'] = None
                    game_data[f'CurrentBest{options[0][1]}LineJuice'] = None
                    game_data[f'{options[0][0]}Ticket%'] = None
                    game_data[f'{options[0][1]}Ticket%'] = None
                    game_data[f'{options[0][0]}Money%'] = None
                    game_data[f'{options[0][1]}Money%'] = None
                    game_data['TicketCount'] = None
                    odds_data.append(game_data)
                    continue

                try:
                    current_odds = row.find_element_by_class_name('public-betting__odds-container').text
                    game_data[f'CurrentBest{options[0][0]}Line'] = current_odds.split('\n')[0].replace('+','').replace('PK','0')
                    game_data[f'CurrentBest{options[0][1]}Line'] = current_odds.split('\n')[2].replace('+','').replace('PK','0')
                    if options[0] != ['AwayML','HomeML']:
                        game_data[f'CurrentBest{options[0][0]}LineJuice'] = current_odds.split('\n')[1].replace('+','')
                        game_data[f'CurrentBest{options[0][1]}LineJuice'] = current_odds.split('\n')[3].replace('+','')
                except:
                    game_data[f'CurrentBest{options[0][0]}Line'] = None
                    game_data[f'CurrentBest{options[0][1]}Line'] = None
                    if options[0] != ['AwayML','HomeML']:
                        game_data[f'CurrentBest{options[0][0]}LineJuice'] = None
                        game_data[f'CurrentBest{options[0][1]}LineJuice'] = None
                try:
                    ticket_data = row.find_elements_by_class_name('public-betting__percents-container')[0].text
                    game_data[f'{options[0][0]}Ticket%'] = ticket_data.split('\n')[0].replace('%','')
                    game_data[f'{options[0][1]}Ticket%'] = ticket_data.split('\n')[1].replace('%','')
                except:
                    game_data[f'{options[0][0]}Ticket%'] = None
                    game_data[f'{options[0][1]}Ticket%'] = None

                try:
                    money_data = row.find_elements_by_class_name('public-betting__percents-container')[1].text
                    game_data[f'{options[0][0]}Money%'] = money_data.split('\n')[0].replace('%','')
                    game_data[f'{options[0][1]}Money%'] = money_data.split('\n')[1].replace('%','')
                except:
                    game_data[f'{options[0][0]}Money%'] = None
                    game_data[f'{options[0][1]}Money%'] = None

                game_data['TicketCount'] = row.find_element_by_class_name('public-betting__number-of-bets').text.replace(',','')
                if game_data['TicketCount'] == 'N/A':
                    game_data['TicketCount'] = None

                odds_data.append(game_data)
        except NoSuchElementException as e:
            print('No Data Present')
            #print(f'\t{e}')
            return([])
        return(odds_data)

    def join_data(self, spreads, totals, mls, options = []):
        spread_data = pd.DataFrame(spreads)
        total_data = pd.DataFrame(totals)
        ml_data = pd.DataFrame(mls)
        total_data['TicketCount'] = spread_data['TicketCount']
        ml_data['TicketCount'] = spread_data['TicketCount']
        odds_table = spread_data.merge(total_data, how = 'outer', on=['WeekDay','Month','Day','Time','Year','AwayRot','AwayTeam','HomeRot','HomeTeam','TicketCount']).merge(ml_data, how = 'outer', on=['WeekDay','Month','Day','Time','Year','AwayRot','AwayTeam','HomeRot','HomeTeam','TicketCount'])
        odds_table['Closed'] = np.where(odds_table['Time'].str.contains('PM') | odds_table['Time'].str.contains('AM'), 'No','Yes')
        return(odds_table)
    
    
    def scrape(self, league, backfill = False):
        self.browser.get(f'https://www.actionnetwork.com/{league}/public-betting')
        page_date = self.browser.find_element_by_class_name
        
        if backfill:
            while backfill:
                try:
                    buttons = self.browser.find_elements_by_class_name("day-nav__button")
                    if len(buttons) == 2:
                        buttons[0].click()
                        page_date = self.browser.find_element_by_class_name("day-nav__display").text
                        print(page_date)
                        self.into_db(self.scrape_line_types(page_date), league)
                    else:
                        break
                except Exception as e:
                    print(e)
                    break
        else:
            self.into_db(self.scrape_line_types(page_date, league), league)
                
    def scrape_line_types(self, date, league):
        line_types = self.browser.find_elements_by_class_name("odds-types-checkboxes__input")
        print(line_types)
        ## For defaulting to spread data being already clicked
        if league in ['nfl','ncaaf','ncaab','nba']:
            spread_data = self.scrape_data(date, [['Away','Home']])
            line_types[1].click()
            line_types[0].click()
            total_data = self.scrape_data(date, [['Over','Under']])
            line_types[2].click()
            line_types[1].click()
            ml_data = self.scrape_data(date, [['AwayML','HomeML']])
            line_types[0].click()
            line_types[2].click()
        elif league in ['mlb','nhl']:
            ml_data = self.scrape_data(date, [['AwayML','HomeML']])
            line_types[0].click()
            line_types[2].click()
            spread_data = self.scrape_data(date, [['Away','Home']])
            line_types[1].click()
            line_types[0].click()
            total_data = self.scrape_data(date, [['Over','Under']])
        if spread_data:
            return(self.join_data(spread_data, total_data, ml_data))
        else:
            return(pd.DataFrame([]))
    
    def into_db(self, data, table):
        if not data.empty:
            #connection = pymysql.connect(user = self.config.get('an','user'), password = self.config.get('an','password'), host = self.config.get('an','host'), database = 'ActionNetwork')
            connection = pymysql.connect(user = 'root', password = 'sports4ever!M',host = '127.0.0.1', database = 'ActionNetwork')
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                query = f"""SELECT * FROM {table} WHERE Closed = 'Yes'"""
                cursor.execute(query)
            closed_data = cursor.fetchall()
            if len(closed_data) > 0:
                previously_closed = pd.DataFrame(closed_data)
            else:
                previously_closed = pd.DataFrame([])
            with connection.cursor() as cursor:
                for idx, row in data.iterrows():
                    if not previously_closed.empty and len(previously_closed[(previously_closed['Month'] == int(row['Month'])) & (previously_closed['Day'] == int(row['Day'])) & (previously_closed['Year'] == int(row['Year'])) & (previously_closed['HomeTeam'] == (row['HomeTeam'])) & (previously_closed['Closed'] == 'Yes')] > 0):
                        continue
                    else:
                        try:
                            if not pd.isna(row['OverOpen']):
                                row['OverOpen'] = row['OverOpen'][1:] #remove the prepended "o" from the line
                            if not pd.isna(row['CurrentBestOverLine']):
                                row['CurrentBestOverLine'] = row['CurrentBestOverLine'][1:]
                            if not pd.isna(row['CurrentBestUnderLine']):
                                row['CurrentBestUnderLine'] = row['CurrentBestUnderLine'][1:]

                            values = f"""'{row['Month']}', '{row['Day']}', '{row['Year']}', '{row['WeekDay']}', '{row['Time']}', '{row['AwayRot']}', "{row['AwayTeam']}", '{row['HomeRot']}', "{row['HomeTeam']}", '{row['AwayOpen']}', '{row['HomeOpen']}', '{row['CurrentBestAwayLine']}', '{row['CurrentBestAwayLineJuice']}', '{row['CurrentBestHomeLine']}', '{row['CurrentBestHomeLineJuice']}', '{row['AwayTicket%']}', '{row['AwayMoney%']}', '{row['HomeTicket%']}', '{row['HomeMoney%']}', '{row['OverOpen']}', '{row['CurrentBestOverLine']}', '{row['CurrentBestOverLineJuice']}', '{row['CurrentBestUnderLine']}', '{row['CurrentBestUnderLineJuice']}', '{row['OverTicket%']}', '{row['OverMoney%']}', '{row['UnderTicket%']}', '{row['UnderMoney%']}', '{row['AwayMLOpen']}', '{row['HomeMLOpen']}', '{row['CurrentBestAwayMLLine']}', '{row['CurrentBestHomeMLLine']}', '{row['AwayMLTicket%']}', '{row['AwayMLMoney%']}', '{row['HomeMLTicket%']}', '{row['HomeMLMoney%']}', '{row['TicketCount']}', '{dt.now()}', NULL, '{row['Closed']}'""".replace( "'None'","NULL").replace("'nan'",'NULL')

                            query = f"""INSERT INTO {table} VALUES ({values});"""
                            cursor.execute(query)
                        except Exception as e:
                            print(e)
                            print(row)
            connection.commit()
                
                
if __name__ == "__main__":
    scraper = ANScraper()
    scraper.login()
    NBA = scraper.scrape('nba')
    NFL = scraper.scrape('nfl')
    NCAAF = scraper.scrape('ncaaf')
    NCAAB = scraper.scrape('ncaab')
    NHL = scraper.scrape('nhl')
    MLB = scraper.scrape('mlb')
    scraper.quit()