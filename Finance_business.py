import requests # for sending HTTP requests
from bs4 import BeautifulSoup #  for web scraping
import time # for time.sleep
import re # for regular expressions
import datetime # for date and time
from Helpers import remove_tags , process_articles # for removing html tags and processing articles

# ==============================================================================================================================================
class Finance_business: 
    def __init__(self, guardian_api_key, alphavantage_api_key, newsapi_key, gnews_api_key):
        '''
        This class is responsible for fetching news articles from finance and business sources

        Parameters:
        ----------
        guardian_api_key : str
            The Guardian API key
        alphavantage_api_key : str
            The Alpha Vantage API key
        newsapi_key : str
            The News API key
        gnews_api_key : str
            The GNews API key
        
        '''
        self.guardian_api_key = guardian_api_key # Guardian API key 
        self.alphavantage_api_key = alphavantage_api_key # Alpha Vantage API key
        self.newsapi_key = newsapi_key # News API key
        self.gnews_api_key = gnews_api_key # GNews API key
        self.duplicates_seuil = 100 # threshold for number of duplicate articles
        self.max_consecutive_same_articles = 4 # threshold for number of consecutive same articles
        # self.from_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') # start date for fetching news articles
      
        self.from_date = (datetime.datetime.now() - datetime.timedelta(hours=12)).strftime('%Y-%m-%d') # start date for fetching news articles
    
# ==============================================================================================================================================
# ============================================== ALPHA VANTAGE API ===========================================================================================

    def fetch_alphavantage_news(self): # Alpha vantage API for finance news
        '''
        This function fetches finance news articles from the Alpha Vantage API 
        '''
        finance_news = [] # list to store finance news articles
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=FOREX:USD&apikey={self.alphavantage_api_key}' # url to fetch finance news
        response = requests.get(url) # send a GET request to the url
        if response.status_code==200: # if the response is successful
            data = response.json() # parse the response as json
            try:
                feeds = data['feed'] # get the feed data
                for feed in feeds: # loop through the feeds
                    finance_news.append({'title': feed['title'], 'content': self.remove_tags(feed['summary'])}) # append the title and content of the feed to the finance_news list
                time.sleep(1) # sleep for 1 second
            except(Exception):  # handle exceptions
                print("Error: Failed to retrieve finance news") # print error message
        return process_articles(finance_news) # return the processed finance news articles
    
# ==============================================================================================================================================
# ========================================= FORTUNE NEWS ================================================================================================
    
    def fetch_fortune_news(self): # Fortune API for finance news
        fortune_articles = [] # list to store fortune news articles
        topic = 'business' # topic of the news
        source = 'fortune' # source of the news
        to = datetime.datetime.now().strftime('%Y-%m-%d') # end date of the news
        url = f'https://newsapi.org/v2/everything?q={topic}&from={self.from_date}&to={to}&sources={source}&language=en&sortBy=popularity&pageSize=100&apiKey={self.newsapi_key}'
        publish_dates = set()  # to avoid duplicate articles
        count_duplicates_per_request = 0 # Track number of duplicate articles per request
        consecutive_same_articles = 0 # Track consecutive iterations with same article count

        while True:
            if len(fortune_articles) % 10 == 0: # Print number of articles retrieved so far
                print(f"number of articles retrieved so far from fortune is : {len(fortune_articles)}") # print message to console 
            response = requests.get(url) # send a GET request to the url
            if response.status_code == 200: # if the response is successful
                data = response.json() # parse the response as json
                articles = data.get('articles', []) # get the articles data
                previous_article_count = len(fortune_articles) # Store previous article count
                for article in articles: # loop through the articles
                    title = article['title'] # get the title of the article
                    content = self.scrape_article_fortune(article['url']) # get the content of the article
                    if content is None: # if the content is None
                        break # break the loop
                    content = remove_tags(content) if content else None # remove html tags from the content
                    if content: # if the content is not None
                        publish_date = article['publishedAt']   # get the publish date of the article
                        if publish_date not in publish_dates: # if the publish date is not in the publish dates set
                            publish_dates.add(publish_date) # add the publish date to the publish dates set
                            fortune_articles.append({'title': title, 'content': content, 'publishdate': publish_date}) # append the title, content and publish date of the article to the fortune_articles list
                        else: # if the publish date is in the publish dates set
                            count_duplicates_per_request += 1 # increment the count_duplicates_per_request by 1
                            continue # continue to the next iteration

                if previous_article_count == len(fortune_articles): # Check for consecutive iterations with same number of articles
                    consecutive_same_articles += 1 # increment the consecutive_same_articles by 1
                if consecutive_same_articles >= self.max_consecutive_same_articles: # Replace with desired threshold
                    break # break the loop
                if count_duplicates_per_request > self.duplicates_seuil: # if the count_duplicates_per_request is greater than the duplicates_seuil
                    print(f"Number of duplicate articles retrieved from fortune news source is : {count_duplicates_per_request} , breaking ...")
                    break # break the loop
                time.sleep(1)
            else:
                print(f"Failed to retrieve data from fortune news source:", response.status_code)
                break
        return process_articles(fortune_articles)

    # Function to scrape article content from Fortune website
    def scrape_article_fortune(self ,url): # function to scrape article content from Fortune website
        try: # try block
            # Send a GET request to the URL
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all <div> tags with class "paywall"
            paywall_divs = soup.find_all('div', class_='paywall')

            # Initialize an empty list to store article text
            article_text = []

            # Loop through each paywall div and extract text from <p> tags
            for div in paywall_divs:
                # Find all <p> tags within the current div
                paragraphs = div.find_all('p')
                # Extract text from each paragraph and append to article_text list
                for p in paragraphs:
                    article_text.append(p.get_text())

            # Join the text from all paragraphs to form the full article content
            full_article = '\n'.join(article_text)

            return full_article

        except requests.exceptions.RequestException as e:
            print("Error fetching URL:", e)
            return None      
        
# ============================================= GNEWS API ============================================================================================
    # Function to fetch finance news articles from the GNews API
    def fetch_gnews_articles(self):
        '''
        This function fetches finance news articles from the GNews API
        '''
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (f'https://gnews.io/api/v4/search?'
               f'from={self.from_date}&to={to}&'
               'lang=en&country=us&max=100&apikey=' + self.gnews_api_key) 
        GNews_articles =[]
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0 # Track number of duplicate articles per request
        consecutive_same_articles = 0 # Track consecutive iterations with same article count
        while True and len(GNews_articles)<100: # Loop until 100 articles are retrieved
            print(f"number of articles retrieved so far from gnews is : {len(GNews_articles)}") # Print number of articles retrieved so far
            response = requests.get(url) # Send a GET request to the URL
            if response.status_code == 200: # If the response is successful
                data = response.json() # Parse the response as JSON
                articles = data['articles'] # Get the articles data
                previous_article_count = len(GNews_articles) # Store previous article count
                for article in articles: # Loop through the articles
                    content = self.scrape_article_content_gnews(article['url']) # Get the content of the article
                    if content is None: # If the content is None
                        break # Break the loop
                    content = remove_tags(content) # Remove HTML tags from the content
                    print(content) # Print the content
                    print("=====================================================================================================")
                    publish_date=article['publishedAt'] # Get the publish date of the article
                    if publish_date not in publish_dates: # If the publish date is not in the publish dates set
                        publish_dates.add(publish_date) # Add the publish date to the publish dates set
                        GNews_articles.append({"title":article['title'] ,"content":content , "publishdate":article['publishedAt'] })
                    else: # If the publish date is in the publish dates set
                        count_duplicates_per_request+=1 # Increment the count_duplicates_per_request by 1
                        continue # Continue to the next iteration

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(GNews_articles):   # Check for consecutive iterations with same number of articles
                    consecutive_same_articles += 1 # Increment the consecutive_same_articles by 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break  # Break the loop

                if count_duplicates_per_request>self.duplicates_seuil:  # If the count_duplicates_per_request is greater than the duplicates_seuil
                    break # Break the loop
            else:
                print("Failed to retrieve data:", response.status_code) # Print error message
                break # Break the loop
        return process_articles(GNews_articles)

    def scrape_article_content_gnews(self , url): # Function to scrape article content from GNews API
        # Fetch the HTML content of the webpage
        response = requests.get(url) # Send a GET request to the URL
        html_content = response.text # Get the HTML content of the webpage

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser') # Parse the HTML content using BeautifulSoup

        # Find all <article> tags and extract the text inside them
        article_tags = soup.find_all('article') # Find all <article> tags
        article_text = '' # Initialize an empty string to store the article text
        for article in article_tags: # Loop through each article tag
            # Remove any unnecessary tags and clean up the text
            cleaned_text = article.get_text(strip=True)
            # Append the cleaned text to the article_text variable
            article_text += cleaned_text + '\n\n'

        return article_text.strip()
# ==============================================================================================================================================
# ========================================= Engadget NEWS ================================================================================================
    # Function to fetch finance news articles from the Engadget API
    def fetch_engadget_news(self):
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=engadget.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        Engadget_articles = []
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True :
            if(len(Engadget_articles)%10 == 0):
                print(f"number of articles retrieved so far from engadget is : {len(Engadget_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(Engadget_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_engadget(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        Engadget_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(Engadget_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from engadget news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from engadget news source is : {len(Engadget_articles)}")
                break
        return process_articles(Engadget_articles)
    
    # Function to scrape article content from Engadget website
    def scrape_article_engadget(self, url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the section tag with class "caas-body" (adjust selector as needed)
            section_element = soup.find('div', class_='caas-body-content')
            # Check if section is found
            if not section_element:
                return None
            # Extract text from paragraphs within the section
            article_text = ''
            for p_tag in section_element.find_all('p'):
            # Remove HTML tags and leading/trailing whitespaces
                article_text += p_tag.get_text(strip=True) + '\n'

            # Return cleaned text (optional: additional cleaning steps here)
            return article_text

        except requests.exceptions.RequestException as e:
            print(f"Error: An error occurred while fetching the webpage: {e}")
            return None
        except Exception as e:
            print(f"Error: An unexpected error occurred: {e}")
            return None
# ==============================================================================================================================================
# =============================== FORBES ===============================================================================================================
    # Function to fetch finance news articles from the Forbes API
    def fetch_forbes_news(self):
        '''
        This function fetches finance news articles from the Forbes API
        '''
        forbes_articles = []
 
        f = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=forbes.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True :
            if(len(forbes_articles)%10 == 0):
                print(f"number of articles retrieved so far from forbes is : {len(forbes_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(forbes_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_forbes(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        forbes_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(forbes_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from forbes news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from forbes news source is : {len(forbes_articles)}")
                break
        return process_articles(forbes_articles)
    # Function to scrape article content from Forbes website
    def scrape_article_forbes(self, url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all article elements with desired class
            article_elements = soup.find_all('div', class_='article-body fs-article fs-responsive-text current-article')

            # Check if any articles are found
            if not article_elements:
                return None
            # ignore figure tags
            for article in article_elements:
                for figure_tag in article.find_all('figure'):
                    figure_tag.decompose()
            # Combine text from paragraphs within all articles
            article_text = ''
            for article in article_elements:
                for p_tag in article.find_all('p'):
                    # Remove HTML tags and leading/trailing whitespaces
                    article_text += p_tag.get_text(strip=True) 

            return article_text

        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None
        
# ================================================================================================================================================================================
# ===================================== CNBC NEWS ===========================================================================================================================================
    # Function to fetch finance news articles from the CNBC API
    def fetch_cnbc_news(self):
        '''
        This function fetches finance news articles from the CNBC API
        '''
        cnbc_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=cnbc.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True :
            if(len(cnbc_articles)%10 == 0):
                print(f"number of articles retrieved so far from CNBC is : {len(cnbc_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(cnbc_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_cnbc(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        cnbc_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(cnbc_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from cnbc news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from cnbc news source is : {len(cnbc_articles)}")
                break
        return process_articles(cnbc_articles)
    # Function to scrape article content from CNBC website
    def scrape_article_cnbc(self, url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all article elements with desired class
            article_elements = soup.find_all('div', class_='group')
            # ignore em tags
            for article in article_elements:
                for em_tag in article.find_all('em'):
                    em_tag.decompose()
            # ignore a tags     
            for article in article_elements:
                for em_tag in article.find_all('a'):
                    em_tag.decompose()
            # Check if any articles are found
            if not article_elements:
                return None

            # Combine text from paragraphs within all articles
            article_text = ''
            for article in article_elements:
                for p_tag in article.find_all('p'):
                    # Remove HTML tags and leading/trailing whitespaces
                    article_text += p_tag.get_text(strip=True) + ' \n'

            # Return cleaned text (optional: additional cleaning steps here)
            return article_text
 
        except Exception as e:
            return None
        
# ================================================================================================================================================================================
# ===================================== COIN DESK NEWS ===========================================================================================================================================
    # Function to fetch finance news articles from the CoinDesk API
    def fetch_coindesk_news(self):
        '''
        This function fetches finance news articles from the CoinDesk API
        '''
        coindesk_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=coindesk.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True :
            if len(coindesk_articles) % 10 == 0:
                print(f"number of articles retrieved so far from coindesk is : {len(coindesk_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(coindesk_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_coindesk(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        coindesk_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                    
                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(coindesk_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break
        return process_articles(coindesk_articles)
    # Function to scrape article content from CoinDesk website
    def scrape_article_coindesk(self, url):
        """
            Scrapes text from the main content area of an article webpage.

            Args:
                url (str): The URL of the article webpage to scrape.

            Returns:
                str: The cleaned text content from the main article area, or None if an error occurs.
            """
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the main content element with the desired class (might need adjustment)
            main_content_element = soup.find('section', class_='at-body')

            # Check if main content element is found
            if not main_content_element:
                print(f"Main content element with class 'at-body' not found on {url}")
                return None
            # ignore i tags
            for i in main_content_element.find_all('i'):
                i.decompose()
            # Extract text from paragraphs within the main content
            article_text = ''
            for p_tag in main_content_element.find_all('p'):
                # Remove HTML tags and leading/trailing whitespaces
                article_text += p_tag.get_text(strip=True) + '\n'   

            # Return cleaned text (optional: additional cleaning steps here)
            return article_text.strip()  # Remove any leading/trailing whitespaces from the entire text

       
        except Exception as e:
            return None
# ================================================================================================================================================================================
# ==================================== bitcoinist NEWS ============================================================================================================================================
    # Function to fetch finance news articles from the Bitcoinist API
    def fetch_bitcoinist_news(self):
        '''
        This function fetches finance news articles from the Bitcoinist API
        '''
        bitcoinist_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=bitcoinist.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0

        while True :
            if len(bitcoinist_articles) % 10 == 0:
                print(f"number of articles retrieved so far from bitcoinist is : {len(bitcoinist_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(bitcoinist_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_bitcoinist(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        bitcoinist_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(bitcoinist_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break
        return process_articles(bitcoinist_articles)
    # Function to scrape article content from Bitcoinist website
    def scrape_article_bitcoinist(self, url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the main content element with the desired class (might need adjustment)
            main_content_element = soup.find('div', class_=lambda x: x=='content-inner' and 'related-reading-shortcode' not in x)

            # Check if main content element is found
            if not main_content_element:
                return None
        
            # Extract text from paragraphs within the main content
            article_text = ''
            for p_tag in main_content_element.find_all('p'):
                # Remove HTML tags and leading/trailing whitespaces
                article_text += p_tag.get_text(strip=True) + ' \n'  
        
            

            return article_text.strip()  # Remove any leading/trailing whitespaces from the entire text

      
        except Exception as e:
            return None
        
# ================================================================================================================================================================================
# ================================ INVESTING NEWS ================================================================================================================================================
    # Function to fetch finance news articles from the Investing API
    def fetch_investing_news(self):
        '''
        This function fetches finance news articles from the Investing API
        '''
        investing_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=investing.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True :
            if len(investing_articles) % 10 == 0:
                print(f"number of articles retrieved so far from investing is : {len(investing_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(investing_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_investing(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        investing_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(investing_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request>self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break
        return process_articles(investing_articles)
    # Function to scrape article content from Investing website
    def scrape_article_investing(self, url):
         
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the main content element with the desired class (might need adjustment)
            main_content_element = soup.find('div', class_=lambda x: x=='WYSIWYG articlePage' )

            # Check if main content element is found
            if not main_content_element:
                return None
        
            # Extract text from paragraphs within the main content
            article_text = ''
            for p_tag in main_content_element.find_all('p'):
            # Remove HTML tags and leading/trailing whitespaces
                article_text += p_tag.get_text(strip=True) + ' \n'  
            # remove the line that start with By and end with \n
            article_text = re.sub(r'By.*\n', '', article_text)
            # remove the line that start with (Reporting and writing by  and end with )
            article_text = re.sub(r'\(Reporting and writing by.*\)', '', article_text)
            return article_text.strip()  # Remove any leading/trailing whitespaces from the entire text

        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None
        
# ================================================================================================================================================================================
# ============================ COINJOURNAL NEWS ====================================================================================================================================================
    def fetch_coinjournal_news(self):
        '''
        This function fetches finance news articles from the CoinJournal API
        '''
        coinjournal_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=coinjournal.net&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0 
        while True :
            if len(coinjournal_articles) % 10 == 0:
                print(f"number of articles retrieved so far from coinjournal is : {len(coinjournal_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(coinjournal_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_coinjournal(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        coinjournal_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                    
                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(coinjournal_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request>self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break
        return process_articles(coinjournal_articles)
    
    def scrape_article_coinjournal(self, url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the main content element with the desired class (might need adjustment)
            main_content_element = soup.find('div', class_=lambda x: x=='post-article-content' and 'post-meta' not in x )
            # Check if main content element is found
            if not main_content_element:
                return None
            # ignore figure tag
            for figure_tag in main_content_element.find_all('figure'):
                figure_tag.decompose()
            # Extract text from paragraphs within the main content
            article_text = ''
            for p_tag in main_content_element.find_all('p'):

            # Remove HTML tags and leading/trailing whitespaces
                article_text += p_tag.get_text(strip=True) + ' \n'  
            return article_text.strip()  # Remove any leading/trailing whitespaces from the entire text
        except Exception as e:
            return None
        
# ================================================================================================================================================================================
# ==============================================================WIRED NEWS========================================================================================================
    def fetch_wired_news(self):
        '''
        This function fetches finance news articles from the Wired API
        '''
        wired_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=(
            f'https://newsapi.org/v2/everything?'
            'domains=wired.com&'
            f'from={self.from_date}&to={to}&'
            'sortBy=popularity&'
            'apiKey=00664c93e32e4db8ae93f46a260d5fd1'
            )
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0 
        
        while True :
            if(len(wired_articles)%10 == 0):
                print(f"number of articles retrieved from the wired so far is : {len(wired_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(wired_articles)

                for article in articles:
                    title = article['title']
                    content = self.scrape_article_wired(article['url'])
                    if content is None:
                        print("Error: Failed to retrieve article content")
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        wired_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                    
                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(wired_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from wired news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(2)
            else:
                print(f"Number of total articles retrieved from wired news source is : {len(wired_articles)}")
                break
        return process_articles(wired_articles)
    
    def scrape_article_wired(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('div', class_='body__inner-container')
            article_text = ''
            if articles:
                for article in articles:
                    paragraphs = article.find_all('p')
                    for paragraph in paragraphs:
                        article_text += paragraph.get_text()
                return article_text
            else:
                return None
        else:
            print("Error:", response.status_code)
            return None
        
# ================================================================================================================================================================================
# ===================================== USA TODAY NEWS ============================================================================================================================================
    # Function to fetch finance news articles from the USA Today API     
    def fetch_usa_today(self):
        usa_today_articles = []
        f = (datetime.datetime.now() - datetime.timedelta(days=29)).strftime('%Y-%m-%d')
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (
            f'https://newsapi.org/v2/everything?'
            f'sources=usa-today&'
            f'from={self.from_date}&to={to}&'
            f'sortBy=popularity&'
            f'apiKey=00664c93e32e4db8ae93f46a260d5fd1'
        )
        publish_dates = set()
        count_duplicates_per_request = 0
        consecutive_same_articles = 0  # Track consecutive iterations with same article count

        while True:
            if len(usa_today_articles) % 10 == 0:
                print(f"Number of articles retrieved from USA TODAY so far is: {len(usa_today_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(usa_today_articles)  # Store previous article count

                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_usa_today(article['url'])
                    if content:
                        content = remove_tags(content)
                    publish_date = article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        usa_today_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                    else:
                        count_duplicates_per_request += 1
                        continue

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(usa_today_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request > self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from usa today news source is: {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from usa today news source is: {len(usa_today_articles)}")
                break

        return process_articles(usa_today_articles)


    def scrape_article_content_usa_today(self ,url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find('div', class_='gnt_ar_b')
            if articles:
                paragraphs = articles.find_all('p')
                content = ''
                for paragraph in paragraphs:
                    text = paragraph.get_text()
                    # Filter out unwanted paragraphs
                    if "Swapna Venugopal Ramaswamy is a White House Correspondent for USA TODAY.You can follow her on X @SwapnaVenugopal" not in text:
                        content += text.replace('Submit', '') + '\n'
                return content.strip()
        return None
    
# ================================================================================================================================================================================
# ===================================== ambcrypto_news ============================================================================================================================================
    # Function to fetch finance news articles from the Ambcrypto API
    def fetch_ambcrypto_news(self):
        ambcrypto_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (f'https://newsapi.org/v2/everything?'
            f'domains=ambcrypto.com&'
            f'from={self.from_date}&to={to}&'
            f'sortBy=popularity&'
            f'apiKey=00664c93e32e4db8ae93f46a260d5fd1')

        publish_dates = set()
        count_duplicates_per_request = 0
        consecutive_same_articles = 0  # Track consecutive iterations with same article count

        while True:
            if len(ambcrypto_articles) % 10 == 0:
                print(f"Number of articles retrieved so far from ambcrypto is: {len(ambcrypto_articles)} ...")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(ambcrypto_articles)

                for article in articles:
                    title = article['title']
                    content = self.scrape_article_ambcrypto(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date = article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        ambcrypto_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                    else:
                        count_duplicates_per_request += 1
                        continue

                if previous_article_count == len(ambcrypto_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request > self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break  # Exit loop on non-200 status code

        return process_articles(ambcrypto_articles)

    
    def scrape_article_ambcrypto(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', class_='single-post-wrapper')
            article_text = ''
            if articles:
                for article in articles:
                    paragraphs = article.find_all('p')
                    for paragraph in paragraphs:
                        article_text += paragraph.get_text() + '\n'  # Add a newline after each paragraph
                return article_text.strip()
            else:
                return None
        else:
            print("Error:", response.status_code)
            return None

# ================================================================================================================================================================================
# ===================================== BUSINESS INSIDER NEWS ============================================================================================================================================
    # Function to fetch finance news articles from the Business Insider API
    def fetch_businessinsider_news(self):
        business_insider_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (f'https://newsapi.org/v2/everything?'
            'domains=businessinsider.com&'
            f'from={self.from_date}&to={to}&'
            f'sortBy=popularity&'
            f'apiKey=00664c93e32e4db8ae93f46a260d5fd1')

        publish_dates = set()
        count_duplicates_per_request = 0
        consecutive_same_articles = 0  # Track consecutive iterations with same article count

        while True:
            if len(business_insider_articles) % 10 == 0:
                print(f"Number of articles retrieved so far from Business Insider is: {len(business_insider_articles)} ...")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(business_insider_articles)

                for article in articles:
                    title = article['title']
                    content = self.scrape_article_business_insider(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date = article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        business_insider_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                    else:
                        count_duplicates_per_request += 1
                        continue

                if previous_article_count == len(business_insider_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request > self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break

        return process_articles(business_insider_articles)
    
    def scrape_article_business_insider(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            article = soup.find('div', class_='content-lock-content') 

            if article:
                paragraphs = article.find_all('p')
                article_text = ''
                for paragraph in paragraphs:
                    article_text += paragraph.get_text() + '\n'

                # Remove unwanted sections
                unwanted_sections = [section for section in article.find_all('div', class_='content-recommendations-component in-content-recirc three-related-posts')]
                for section in unwanted_sections:
                    article_text = article_text.replace(str(section), '')

                return article_text.strip()
            else:
                return None
        else:
            print("Error:", response.status_code)
            return None
# ================================================================================================================================================================================
# ===================================== TECHCRUNCH NEWS ============================================================================================================================================
    # Function to fetch finance news articles from the TechCrunch API
    def fetch_readwrite_news(self):
        readwrite_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (f'https://newsapi.org/v2/everything?'
            f'domains=readwrite.com&'
            f'from={self.from_date}&to={to}&'
            f'sortBy=popularity&'
            f'apiKey=00664c93e32e4db8ae93f46a260d5fd1')

        publish_dates = set()
        count_duplicates_per_request = 0
        consecutive_same_articles = 0

        while True:
            response = requests.get(url)
            if response.status_code == 200:
                if len(readwrite_articles) % 10 == 0:
                    print(f"Number of articles retrieved so far from readwrite is: {len(readwrite_articles)} ...")
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(readwrite_articles)

                for article in articles:
                    title = article['title']
                    content = self.scrape_article_readwrite(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    publish_date = article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        readwrite_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                    else:
                        count_duplicates_per_request += 1
                        continue

                if previous_article_count == len(readwrite_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request > self.duplicates_seuil:
                    break
                time.sleep(1)
            else:
                break

        return process_articles(readwrite_articles)

    def scrape_article_readwrite(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Target specific class or id containing the main content
            article = soup.find('div', class_='entry-content')   # Adjust based on website structure

            if article:
                paragraphs = article.find_all('p')[:-1]  # Exclude the last p tag using slicing
                article_text = ''
                for paragraph in paragraphs:
                    article_text += paragraph.get_text() + '\n'

                return article_text.strip()
            else:
                return None
        else:
            print("Error:", response.status_code)
            return None

# =========================================================================================================================================
# =========================================================================================================================================