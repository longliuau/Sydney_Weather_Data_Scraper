from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WW
from selenium.webdriver.support import expected_conditions as EC
from time import sleep


driver = webdriver.PhantomJS()
driver.get('http://www.bom.gov.au/climate/data/')
assert 'Climate' in driver.title

class elements_ready(object):
    def __init__(self, locator, thres):
        self.locator = locator
        self.thres = thres
    def __call__(self, drive):
        content = Select(driver.find_element(*self.locator)).options
        if len(content) > self.thres:
            return True
        else:
            return False

def conv_not_day(x):
    if (x.get('class') is not None) and ('notDay' in x.get('class')):
        return 'aaa'
    else:
        return x.text.strip()

item_list = ['Solar exposure', 'Rainfall', 'Temperature', 'Temperature']
year_list = ['2010', '2011', '2012', '2013']

frame_columns = ['Solar', 'Rain', 'Temp_Max', 'Temp_Min']
data_store = {}
item_id = 0 # for identifying which item is collected
for item in item_list:
    item_data = []
    item_id += 1
    select = Select(driver.find_element_by_name('ncc_obs_code_group'))
    data_about = select.select_by_visible_text(item)

    if item_id > 2:
        wait = WW(driver, 10)
        wait.until(EC.element_to_be_clickable((By.ID, 'elementSubSelect')))
        subselect = Select(driver.find_element_by_id('elementSubSelect'))
        if item_id < 4:
            subselect.select_by_value('122')
        else:
            subselect.select_by_value('123')

    loc_text = driver.find_element_by_name('p_locSearch')
    loc_text.clear()
    location = loc_text.send_keys('sydney')
    find_button = driver.find_element_by_id('text')
    find_button.click()

    sleep(0.5)
    wait = WW(driver, 10)
    wait.until(elements_ready((By.ID, 'matchList'), 4))

    m_list = driver.find_element_by_name('matchList')
    m_list.find_elements_by_tag_name('option')[0].click()

    wait = WW(driver, 10)
    wait.until(elements_ready((By.ID, 'nearest10'), 2))

    station_list = driver.find_element_by_name('nearest10')
    station_avl = station_list.find_elements_by_tag_name('option')
    for station in station_avl:
        if ('066062 Sydney (Observatory Hill) NSW (1.1km away)    ') in station.get_attribute('value'):
            station.click()

    wait = WW(driver, 10)
    wait.until(EC.element_to_be_clickable((By.ID, 'year_select')))

    windows = driver.window_handles
    main_window = windows[0]

    for year in year_list:

        year_select = Select(driver.find_element_by_name('year_select'))
        year_select.select_by_visible_text(year)

        driver.find_element_by_id('getData').click()
        existing_windows = windows
        windows = driver.window_handles
        new_window = [i for i in existing_windows if i not in windows]
        driver.switch_to.window(windows[-1])

        r = driver.page_source

        driver.switch_to.window(main_window)

        soup = BeautifulSoup(r, 'html.parser')

        data_table = soup.select('#dataTable tr')
        data_month_day_one = data_table[2:30]
        data_month_day_two = data_table[30:33]

        day_count = 0

        data_matrix = []
        for data in data_month_day_one:
            data_row = [day.text.strip() for day in data.findAll('td')]
            data_matrix.append(data_row)

        for data in data_month_day_two:
            day = data.findAll('td')
            data_row = map(conv_not_day, day)
            data_matrix.append(data_row)

        data_frame = pd.DataFrame(data_matrix)
        data_trans = filter(lambda x: x!='aaa', data_frame.T.stack().values)
        item_data += data_trans
    data_store[frame_columns[item_id - 1]] = item_data

weather_data = pd.DataFrame(data_store, index=pd.date_range(start=(year_list[0] + '0101'), end=(year_list[-1] + '1231')))

weather_data = weather_data.apply(pd.to_numeric)