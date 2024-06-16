import requests
from bs4 import BeautifulSoup
import time
import re
import datetime
from Helpers import remove_tags , process_articles


class Finance_business:
    def __init__(self, guardian_api_key, alphavantage_api_key, newsapi_key, gnews_api_key):
        '''
        This class is responsible for fetching news articles from finance and business sources
        '''
        self.guardian_api_key = guardian_api_key
        self.alphavantage_api_key = alphavantage_api_key
        self.newsapi_key = newsapi_key
        self.gnews_api_key = gnews_api_key
        self.duplicates_seuil = 100
        self.max_consecutive_same_articles = 4
        self.from_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    
# ==============================================================================================================================================
# ============================================== ALPHA VANTAGE API ===========================================================================================

    def fetch_alphavantage_news(self): # Alpha vantage API
        '''
        This function fetches finance news articles from the Alpha Vantage API
        '''
        finance_news = []
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=FOREX:USD&apikey={self.alphavantage_api_key}'
        response = requests.get(url)
        if response.status_code==200:
            data = response.json()
            try:
                feeds = data['feed']
                for feed in feeds:
                    finance_news.append({'title': feed['title'], 'content': self.remove_tags(feed['summary'])})
                time.sleep(1)
            except(Exception): 
                print("Error: Failed to retrieve finance news")
        return process_articles(finance_news)
    
# ==============================================================================================================================================
# ========================================= FORTUNE NEWS ================================================================================================
    
    def fetch_fortune_news(self):
        fortune_articles = []
        topic = 'business'
        source = 'fortune'
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f'https://newsapi.org/v2/everything?q={topic}&from={self.from_date}&to={to}&sources={source}&language=en&sortBy=popularity&pageSize=100&apiKey={self.newsapi_key}'
        publish_dates = set()  # to avoid duplicate articles
        count_duplicates_per_request = 0
        consecutive_same_articles = 0

        while True:
            if len(fortune_articles) % 10 == 0:
                print(f"number of articles retrieved so far is : {len(fortune_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(fortune_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_fortune(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content) if content else None
                    if content:
                        publish_date = article['publishedAt']
                        if publish_date not in publish_dates:
                            publish_dates.add(publish_date)
                            fortune_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                        else:
                            count_duplicates_per_request += 1
                            continue

                if previous_article_count == len(fortune_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:
                    break
                if count_duplicates_per_request > self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from fortune news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Failed to retrieve data from fortune news source:", response.status_code)
                break
        return process_articles(fortune_articles)


    def scrape_article_fortune(self ,url):
        try:
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
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True and len(GNews_articles)<100:
            print(f"number of articles retrieved so far is : {len(GNews_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data['articles']
                previous_article_count = len(GNews_articles)
                for article in articles:
                    content = self.scrape_article_content_gnews(article['url'])
                    if content is None:
                        break
                    content = remove_tags(content)
                    print(content)
                    print("=====================================================================================================")
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        GNews_articles.append({"title":article['title'] ,"content":content , "publishdate":article['publishedAt'] })
                    else:
                        count_duplicates_per_request+=1
                        continue

                    # Check for consecutive iterations with same number of articles
                if previous_article_count == len(GNews_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break 

                if count_duplicates_per_request>self.duplicates_seuil:
                    break
            else:
                print("Failed to retrieve data:", response.status_code)
                break
        return process_articles(GNews_articles)

    def scrape_article_content_gnews(self , url):
        # Fetch the HTML content of the webpage
        response = requests.get(url)
        html_content = response.text

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all <article> tags and extract the text inside them
        article_tags = soup.find_all('article')
        article_text = ''
        for article in article_tags:
            # Remove any unnecessary tags and clean up the text
            cleaned_text = article.get_text(strip=True)
            # Append the cleaned text to the article_text variable
            article_text += cleaned_text + '\n\n'

        return article_text.strip()
# ==============================================================================================================================================
# ========================================= Engadget NEWS ================================================================================================
    def fetch_engadget_news(self):
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=engadget.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        Engadget_articles = []
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True :
            if(len(Engadget_articles)%10 == 0):
                print(f"number of articles retrieved so far is : {len(Engadget_articles)}")
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
                    print(f"Number of duplicate articles retrieved from fortune news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from fortune news source is : {len(Engadget_articles)}")
                break
        return process_articles(Engadget_articles)
    
    
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
                print(f"number of articles retrieved so far is : {len(forbes_articles)}")
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
                    print(f"Number of duplicate articles retrieved from fortune news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from fortune news source is : {len(forbes_articles)}")
                break
        return process_articles(forbes_articles)
    
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
# ================================================================================================================================================================================
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
                        print(f"number of articles retrieved so far is : {len(coindesk_articles)} ...")
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
                        print(f"number of articles retrieved so far is : {len(bitcoinist_articles)} ...")
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
                        print(f"number of articles retrieved so far is : {len(investing_articles)} ...")
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
                        print(f"number of articles retrieved so far is : {len(coinjournal_articles)} ...")
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
        f = (datetime.datetime.now() - datetime.timedelta(days=29)).strftime('%Y-%m-%d')
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
                print(f"number of articles retrieved so far is : {len(wired_articles)}")
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
                print(f"Number of articles retrieved so far is: {len(usa_today_articles)}")
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
            response = requests.get(url)
            if response.status_code == 200:
                if len(ambcrypto_articles) % 10 == 0:
                    print(f"Number of articles retrieved so far is: {len(ambcrypto_articles)} ...")
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
            response = requests.get(url)
            if response.status_code == 200:
                if len(business_insider_articles) % 10 == 0:
                    print(f"Number of articles retrieved so far is: {len(business_insider_articles)} ...")
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
                    print(f"Number of articles retrieved so far is: {len(readwrite_articles)} ...")
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
