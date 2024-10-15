import os
import pandas as pd
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def return_driver():
    os.system("pkill -f -9 chromium")
    os.system("pkill -f -9 chrome")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options, service=service)

    return driver


class GraphSearcher:
    def __init__(self):
        self.visited = set()
        self.order = []

    def visit_and_get_children(self, node):
        """ Record the node value in self.order, and return its children
        param: node
        return: children of the given node
        """
        raise Exception("must be overridden in sub classes -- don't change me here!")

    def dfs_search(self, node):
        self.visited = set()
        self.order = []
        self.dfs_visit(node)

    def dfs_visit(self, node):
        if node in self.visited:
            return
        self.visited.add(node)
        children = self.visit_and_get_children(node)
        for i in children:
            self.dfs_visit(i)
            
    def bfs_search(self,node):
        self.visited = set()
        self.order = []
        queue = [node]

        while queue:
            current_node = queue.pop(0)  # Remove and return the first element of the list
            if current_node not in self.visited:
                self.visited.add(current_node)
                children = self.visit_and_get_children(current_node)
                for child in children:
                    if child not in self.visited:
                        queue.append(child)
       
    

class MatrixSearcher(GraphSearcher):
    def __init__(self, df):
        super().__init__() # call constructor method of parent class
        self.df = df

    def visit_and_get_children(self, node):
        # TODO: Record the node value in self.order
        self.order.append(node)
        
        children = []
        # TODO: use `self.df` to determine what children the node has and append them
        for n, val in self.df.loc[node].items():
            if val == 1:
                children.append(n)
        return children
                        

class FileSearcher(GraphSearcher):
    def __init__(self):
        super().__init__()
    
    def visit_and_get_children(self, node):
        path = os.path.join('file_nodes', node)
        with open(path, 'r') as file:
            content = file.readlines()
            value = content[0].strip()
            children = content[1].strip().split(',') if content[1].strip() != '' else []
        self.order.append(value)
        return children

    def concat_order(self):
        return ''.join(self.order)
    

class WebSearcher(GraphSearcher):
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.data_frames = []  # To store table fragments from each page visited.

    def visit_and_get_children(self, node_url):
        self.order.append(node_url)
        self.driver.get(node_url)
        elements = self.driver.find_elements(By.TAG_NAME,'a')  # Finds all hyperlinks on the page.
        urls = [element.get_attribute('href') for element in elements]  # Extracts the URLs.
        
        # Try to read any table fragments on the page and store them.
        try:
            df = pd.read_html(self.driver.page_source)  # This returns a list of DataFrames.
            self.data_frames.extend(df)  # Store each DataFrame from the page.
        except ValueError:
            pass  # No tables found, do nothing.
        return urls

    def table(self):
        if not self.data_frames:
            return pd.DataFrame()  # Returns an empty DataFrame if no tables have been stored.
        return pd.concat(self.data_frames, ignore_index=True).dropna(axis = 1)
                        

def reveal_secrets(driver,url,travellog):
    # Generate password from the "clue" column
    password = ''.join(travellog['clue'].astype(str))
    # Visit the URL
    driver.get(url)
    
    # Automate typing the password and clicking "GO"
    password_input = driver.find_element(By.ID, "password-textbox")  # Adjust the element selector as needed
    password_input.send_keys(password)
    
    go_button = driver.find_element(By.ID, "submit-button")  # Adjust the element selector as needed
    go_button.click()
    
    # Wait for the page to load
    time.sleep(5)  # Adjust the sleep time as needed, or use WebDriverWait for better accuracy
    
    # Click the "View Location" button and wait
    view_location_button = driver.find_element(By.ID, "view-location-button")  # Adjust the element selector as needed
    view_location_button.click()
    
    # Wait for the result to finish loading
    time.sleep(5)  # Adjust as necessary
    
    # Get the image URL and download it
    image_element = driver.find_element(By.ID, "image")  # Adjust the element selector as needed
    image_url = image_element.get_attribute('src')
    
    # Use requests to download the image
    response = requests.get(image_url)
    if response.status_code == 200:
        with open('Current_Location.jpg', 'wb') as file:
            file.write(response.content)
    
    # Return the current location text
    current_location_element = driver.find_element(By.ID, "location")  # Adjust the element selector as needed
    return current_location_element.text