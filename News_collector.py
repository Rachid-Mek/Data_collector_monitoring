import requests
from bs4 import BeautifulSoup
import time
import re
import datetime
from Helpers import remove_tags, process_articles

# ==============================================================================================================================================

class News_collector:
    def __init__(self, guardian_api_key, newsapi_key): 
        self.guardian_api_key = guardian_api_key  
        self.newsapi_key = newsapi_key 
        self.duplicates_seuil=100
        self.max_consecutive_same_articles=4
        self.from_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d') 
        


# ============================================== GUARDIAN API ===========================================================================================
    def fetch_guardian_news(self):
        ''' 
        This function fetches news articles from the guardian api
        '''
        self.endpoint = 'https://content.guardianapis.com/search'
        self.params = {
            'api-key': self.guardian_api_key,
            'show-fields': 'headline,body',
            f'from-date': self.from_date,
            'to-date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'order-by': 'newest',
            'page-size': 200
        }
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        collected_articles = []
        consecutive_same_articles = 0
        while True:
            if len(collected_articles) % 10 == 0: 
                print(f"Number of collected documents so far from the guardian are : {len(collected_articles)} ....")
            response = requests.get(self.endpoint, self.params)
            data = response.json() 
            articles = data['response']['results']
            previous_article_count = len(collected_articles)
            for article in articles:
                title = article['fields']['headline']
                content = remove_tags(article['fields']['body'])
                publish_date=article['webPublicationDate']
                if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        collected_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                else:
                    count_duplicates_per_request+=1
                    continue
            if previous_article_count == len(collected_articles):
                consecutive_same_articles += 1

            if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                break
            if count_duplicates_per_request>self.duplicates_seuil:
                print(f"Number of duplicate articles retrieved from the guardien news source is : {count_duplicates_per_request} , breaking ...")
                break
            time.sleep(1)
        return process_articles(collected_articles)

   
# ==============================================================================================================================================
# ================================================ BBC NEWS =========================================================================================

    def fetch_bbc_news(self):
        bbc_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f'https://newsapi.org/v2/everything?sources=bbc-news&from={self.from_date}&to={to}&language=en&sortBy=popularity&apiKey={self.newsapi_key}'
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True:
            if len(bbc_articles) % 10 == 0:
                print(f"number of articles retrieved so far from bbc news is : {len(bbc_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(bbc_articles)
                for article in articles:
                    title = article['title']
                    content = self.get_article_content(article['url'])
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        bbc_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(bbc_articles):
                    consecutive_same_articles += 1

                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from fortune news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from bbc news api is : {len(bbc_articles)}")
                break
        return process_articles(bbc_articles)

    def get_article_content(self, article_url):
        response = requests.get(article_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        article_content = ' '.join([p.get_text() for p in soup.find_all('p')])
        return article_content
# =========================================================================================================================================
# ================================================ AL JAZEERA NEWS =========================================================================================

    def fetch_al_jazeera_english(self):
            aljaz_articles = []
            topic = 'general'
            publish_dates=set() # to avoid duplicate articles
            count_duplicates=0

            to = datetime.datetime.now().strftime('%Y-%m-%d')
            url = f'https://newsapi.org/v2/everything?q={topic}&from={self.from_date}&to={to}&sources=al-jazeera-english&language=en&sortBy=popularity&pageSize=100&apiKey={self.newsapi_key}'
            rep=0
            consecutive_same_articles = 0
            while True :
                if len(aljaz_articles) % 10 == 0:
                    print(f"number of articles retrieved so far from al jazeera news is : {len(aljaz_articles)}")
                response = requests.get(url)
                if response.status_code == 200 and response.json().get('totalResults', 0) > 0:
                    data = response.json()
                    articles = data.get('articles', [])
                    previous_article_count = len(aljaz_articles)
                    for article in articles:
                        title = article['title']
                        content = self.scrape_article_content_aljaz(article['url'])
                        if content is None :
                            break
                        content = remove_tags(content)
                        publish_date=article['publishedAt']
                        if publish_date not in publish_dates:
                            publish_dates.add(publish_date)
                            aljaz_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                            rep=0
                        else:
                            count_duplicates+=1
                            rep=rep+1
                    if previous_article_count == len(aljaz_articles):
                        consecutive_same_articles += 1
                    if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                        break
                    if count_duplicates>self.duplicates_seuil:
                        print(f"Number of duplicate articles retrieved from jazeera news source is : {count_duplicates} , breaking ...")
                        break
                    if (rep==5):
                        break
                    time.sleep(1)
                else:
                    print(f"Number of total articles retrieved from al-jazeera-english source is : {len(aljaz_articles)}")
                    break
            return process_articles(aljaz_articles)
    
    def scrape_article_content_aljaz(self ,url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the main tag with id "main-content-area"
            main_content = soup.find('div', class_='wysiwyg wysiwyg--all-content css-ibbk12')

            if main_content:
                # # ignore div with class="more-on"
                for tag in main_content.find_all('div', class_=['more-on','article-source','article-info-block css-ti04u9']):
                    tag.decompose()
                for tag in main_content.find_all('figure'):
                    tag.decompose()
                # Extract text content from main tag and remove tags
                article_text = main_content.get_text(separator='\n', strip=True)

                # Remove phrases matching specific patterns
                article_text =re.sub(r'list \d+ of \d+','',article_text)
    
                article_text = ' '.join(article_text.split())

                return article_text
            else:
                print("Main content area not found.")
                return None
        except Exception as e:
            print("Error:", e)
            return None
         

# =========================================================================================================================================
# ================================================ ABC NEWS =========================================================================================

    def fetch_abc_news(self):
                abc_articles = [] 
                topic = 'general'
    
                to = datetime.datetime.now().strftime('%Y-%m-%d')
                url = f'https://newsapi.org/v2/everything?q={topic}&from={self.from_date}&to={to}&sources=abc-news&language=en&sortBy=popularity&pageSize=100&apiKey={self.newsapi_key}'
                publish_dates=set() # to avoid duplicate articles
                count_duplicates_per_request=0
                consecutive_same_articles = 0
                while True :
                    if len(abc_articles) % 10 == 0:
                        print(f"number of articles retrieved so far from abc news is : {len(abc_articles)}")
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        articles = data.get('articles', [])
                        previous_article_count = len(abc_articles)
                        for article in articles:
                            title = article['title']
                            content = self.scrape_article_content_abc(article['url'])
                            if content is None :
                                break
                            content = remove_tags(content)
                            publish_date=article['publishedAt']
                            if publish_date not in publish_dates:
                                publish_dates.add(publish_date)
                                abc_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                            else:
                                count_duplicates_per_request+=1
                                continue
                        if previous_article_count == len(abc_articles):
                            consecutive_same_articles += 1
                        if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                            break
                        if count_duplicates_per_request>self.duplicates_seuil:
                            print(f"Number of duplicate articles retrieved from fortune news source is : {count_duplicates_per_request} , breaking ...")
                            break
                        time.sleep(1)
                    else:
                        print(f"Number of total articles retrieved from abc news source is : {len(abc_articles)}")
                        break
                return process_articles(abc_articles)
    def scrape_article_content_abc(self ,url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the div tag with class "xvlfx ZRifP TKoO eaKKC bOdfO"
            article_div = soup.find('div', class_='xvlfx ZRifP TKoO eaKKC bOdfO')

            if article_div:
                # Extract text content from div tag and remove tags
                article_text = article_div.get_text(separator='\n', strip=True)
                
                # Remove extra spaces, tabs, and newlines
                article_text = ' '.join(article_text.split())

                return article_text
            else:
                print("Article content div not found.")
                return None
        except Exception as e:
            print("Error:", e)
            return None
# =========================================================================================================================================
# ============================================ ABC AU NEWS =============================================================================================
    def fetch_abc_news_au_articles(self):
        abc_au_articles = []
        if len(abc_au_articles) % 10 == 0:
            print(f"number of articles retrieved so far is : {len(abc_au_articles)}")
        topic = 'general'
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f'https://newsapi.org/v2/everything?q={topic}&from{self.from_date}&to{to}&sources=abc-news-au&language=en&sortBy=popularity&pageSize=100&apiKey={self.newsapi_key}'
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True  :
            print(f"number of articles retrieved so far from abc news au is : {len(abc_au_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(abc_au_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_abc_au(article['url'])
                    if content is None :
                        break
                    content = remove_tags(content)
                    if content is None:
                        break
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        abc_au_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(abc_au_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from abc au news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from abc au news source is : {len(abc_au_articles)}")
                break
        return process_articles(abc_au_articles)
    
    def scrape_article_content_abc_au(self ,url):
        try:
            # Send a GET request to the URL
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the <div> with class "LayoutContainer_container__jw05j Article_body__y7ykc"
            article_div = soup.find('div', class_='LayoutContainer_container__jw05j Article_body__y7ykc')

            # Initialize an empty list to store article text
            article_text = []

            # Find all <p> tags within the article_div and extract text from them
            if article_div:
                paragraphs = article_div.find_all('p')
                for p in paragraphs:
                    for em in p.find_all('em'):
                        em.decompose()  # Remove <em> tags and their content
                    article_text.append(p.get_text())

            # Join the text from all paragraphs to form the full article content
            full_article = '\n'.join(article_text)

            return full_article

        except requests.exceptions.RequestException as e:
            print("Error fetching URL:", e)
            return None
# =========================================================================================================================================
# =========================================== CNN NEWS ================================================================================================
    def get_cnn_news(self):
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = ( 'https://newsapi.org/v2/everything?'
                'sources=cnn&'
                'language=en&'
                f'from={self.from_date}&'
                f'to={to}&'
                'sortBy=popularity&'
                'pageSize=100&'
                'apiKey=00664c93e32e4db8ae93f46a260d5fd1')
        cnn_articles = []
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True:
            response = requests.get(url)
            print(f"number of articles retrieved so far from cnn news is : {len(cnn_articles)}")
            if response.status_code == 200:
                articles = response.json()['articles']
                previous_article_count = len(cnn_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_cnn(article['url'])
                    publish_date=article['publishedAt']
                    if content and publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        content = remove_tags(content)
                        cnn_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                    else :
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(cnn_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from cnn news source is : {count_duplicates_per_request} , breaking ...")
                    break
        return process_articles(cnn_articles)
    
    def scrape_article_content_cnn(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find('div', class_='article__content-container')
            if articles:
                paragraphs = articles.find_all('p', class_='paragraph inline-placeholder')
                article_text = ''.join([p.text for p in paragraphs])
                return article_text
            else:
                return None

# =========================================================================================================================================
# ================================================ FOX NEWS =========================================================================================
    def fetch_fox_news(self):
        fox_articles = []
        topic = 'general'
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f'https://newsapi.org/v2/everything?q={topic}&from={self.from_date}&to={to}&sources=fox-news&language=en&sortBy=popularity&pageSize=100&apiKey={self.newsapi_key}'
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True:
            print(f"number of articles retrieved so far from fox news is : {len(fox_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(fox_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_fox(article['url'])
                    if content is None :
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        fox_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(fox_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from fox news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from fox news source is : {len(fox_articles)}")
                break

        return process_articles(fox_articles)
    
    def scrape_article_content_fox(self ,url):     
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the div tag with class "article-content"
            article_content_div = soup.find('div', class_='article-content') # for fox news

            if article_content_div:
                for tag in article_content_div.find_all('div', class_=['featured featured-video video-ct']): # ignore div with class="featured featured-video video-ct"
                    tag.decompose()
                # ignore figure tags
                for tag in article_content_div.find_all('figure'): # ignore figure tags
                    tag.decompose()
                # ignore div tag author-bio
                for tag in article_content_div.find_all('div', class_=['author-bio']): # ignore div tag author-bio
                    tag.decompose()
                p_tags = article_content_div.find_all('p') # find all p tags
                article_text = '\n'.join([p.get_text(strip=True) for p in p_tags]) # extract text from p tags and join them
                article_text = re.sub(r'FIRST ON FOX:','',article_text) # remove phrases matching specific patterns
                article_text = re.sub(r'CLICK HERE TO GET THE FOX NEWS APP','',article_text) # remove phrases matching specific patterns
                # Remove extra spaces, tabs, and newlines
                article_text = ' '.join(article_text.split()) # remove extra spaces, tabs, and newlines

                return article_text
            else:
                return None
        except Exception as e:
            print("Error:", e)
            return None
# =========================================================================================================================================
# ================================================ THE WASHINGTON POST ========================================================================================
    def fetch_washington_post(self):
        washington_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=f'https://newsapi.org/v2/everything?domains=washingtonpost.com&from={self.from_date}&to={to}&apiKey=3d40d72f4efd4810901e62b9253c8731'
        publish_dates=set() 
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True:
            print(f"number of articles retrieved so far from washington post is : {len(washington_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(washington_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_washington_post(article['url'])
                    if content is None :
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        washington_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(washington_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from washington post news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from washington post news source is : {len(washington_articles)}")
                break

        return process_articles(washington_articles)
    
    def scrape_article_content_washington_post(self ,url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find the main tag with id "main-content-area"
            main_content = soup.find('div', class_="meteredContent grid-center")

            if main_content:

                for tag in main_content.find_all('figure'):
                    tag.decompose()
                for tag in main_content.find_all('div', class_=[' mb-md hide-for-print']):
                    tag.decompose() 
                for tag in main_content.find_all('div', id=['gift-share-inline']):
                    tag.decompose()
                # Extract text content from main tag and remove tags
                article_text = main_content.get_text(separator='\n', strip=True)
                article_text = ' '.join(article_text.split())
                return article_text
            else:
                print("Main content area not found.")
                return None
        except Exception as e:
            print("Error:", e)
            return None
        
# =========================================================================================================================================
# ======================================= NPR ORG NEWS ==================================================================================================
    def fetch_npr_news(self):
        npr_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f'https://newsapi.org/v2/everything?domains=npr.org&from={self.from_date}&to={to}&apiKey=3d40d72f4efd4810901e62b9253c8731'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True:
            if len(npr_articles) % 10 == 0:
                print(f"number of articles retrieved so far from bbc news is : {len(npr_articles)}")

            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(npr_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_npr(article['url'])
                    if content is None :
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        npr_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                        print(f"number of articles retrieved so far is : {len(npr_articles)}")

                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(npr_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from npr news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from npr news source is : {len(npr_articles)}")
                break
        return process_articles(npr_articles)  
    
    def scrape_article_content_npr(self ,url):
        try:
            # Fetch the HTML content of the webpage
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for unsuccessful requests (improves error handling)
            html_content = response.text

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all article elements with desired class
            article_elements = soup.find_all('div', id='storytext')
            # ignore a tags
            for article in article_elements:
                for em_tag in article.find_all('a'):
                    em_tag.decompose()

            # Check if any articles are found
            if not article_elements:
                return None
            # ignore figure tags
            for article in article_elements:
                for figure_tag in article.find_all('figure'):
                    figure_tag.decompose()
            # ignore a class with class=bucketwrap image large
            for article in article_elements:
                for figure_tag in article.find_all('div', class_='bucketwrap image large'):
                    figure_tag.decompose()
            # Combine text from paragraphs within all articles
            article_text = ''
            for article in article_elements:
                for p_tag in article.find_all('p'):
                    # Remove HTML tags and leading/trailing whitespaces
                    article_text += p_tag.get_text(strip=True) + ' \n'

            # Return cleaned text (optional: additional cleaning steps here)
            return article_text
        except requests.exceptions.RequestException as e:
            return None
        
# =========================================================================================================================================
# ================================================ AP NEWS =========================================================================================
    def fetch_ap_news(self):
        print("Fetching articles from ap news source ...")
        ap_articles = []
        f = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = f'https://newsapi.org/v2/everything?domains=apnews.com&from={self.from_date}&to={to}&apiKey={self.newsapi_key}'
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0

        while True:
            if len(ap_articles) % 10 == 0:
                print(f"number of articles retrieved so far from bbc news is : {len(ap_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(ap_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_ap(article['url'])
                    if content is None :
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        ap_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(ap_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request>self.duplicates_seuil  :
                    print(f"Number of duplicate articles retrieved from ap news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from ap news source is : {len(ap_articles)}")
                break
        return process_articles(ap_articles)
    
    def scrape_article_content_ap(self ,url):
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
            main_content_element = soup.find('div', class_='RichTextStoryBody RichTextBody')

            # Check if main content element is found
            if not main_content_element:
                print(f"Main content element with class 'RichTextStoryBody RichTextBody' not found on {url}")
                return None

            # Extract text from paragraphs within the main content
            article_text = ''
            for p_tag in main_content_element.find_all('p'):
                # Remove HTML tags and leading/trailing whitespaces
                article_text += p_tag.get_text(strip=True) + '\n\n'  # Add double newlines for separation

            # Return cleaned text (optional: additional cleaning steps here)
            return article_text.strip()  # Remove any leading/trailing whitespaces from the entire text

        except requests.exceptions.RequestException as e:
            print(f"Error: An error occurred while fetching the webpage: {e}")
            return None
        except Exception as e:
            print(f"Error: An unexpected error occurred: {e}")
            return None
        
# =========================================================================================================================================
        #==================================================NEW YORK POST================================================================================
    def fetch_new_york_post(self):
        newyork_articles = []
        f = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (
            f'https://newsapi.org/v2/everything?'
            'domains=nypost.com&'
            f'from={self.from_date}&to={to}&'
            'sortBy=popularity&'
            'apiKey=00664c93e32e4db8ae93f46a260d5fd1')
        publish_dates=set() # to avoid duplicate articles
        count_duplicates_per_request=0
        consecutive_same_articles = 0

        while True:
            if len(newyork_articles) % 10 == 0:
                print(f"number of articles retrieved so far from newyork post is : {len(newyork_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(newyork_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_new_york_post(article['url'])
                    if content is None :
                        break
                    content = remove_tags(content)
                    publish_date=article['publishedAt']
                    if publish_date not in publish_dates:
                        publish_dates.add(publish_date)
                        newyork_articles.append({'title': title, 'content': content, 'publishdate':publish_date})
                    else:
                        count_duplicates_per_request+=1
                        continue
                if previous_article_count == len(newyork_articles):
                    consecutive_same_articles += 1
                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break

                if count_duplicates_per_request>self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from new york post news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1)
            else:
                print(f"Number of total articles retrieved from new york post news source is : {len(newyork_articles)}")
                break

        return process_articles(newyork_articles)
    
    def scrape_article_content_new_york_post(self ,url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find('main', id='main')
            if articles:
                paragraphs = articles.find_all('p')
                content = ''
                for paragraph in paragraphs:
                    text = paragraph.get_text()
                    # Filter out unwanted paragraphs
                    if "Stay up on the very latest with Evening Update" not in text:
                        content += text.replace('Submit', '') + '\n'
                content = content.replace('Thanks for contacting us. We\'ve received your submission.', '')
                content = content.replace('Advertisement', '')
                return content.strip()
            else:
                return None
        else:
            return None
        
# =========================================================================================================================================
#==================================================USA TODAY================================================================================
    def fetch_usa_today(self):
        usa_today_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url=(f'https://newsapi.org/v2/everything?'
             'sources=usa-today&'
             f'from={self.from_date}&to={to}&'
            'sortBy=popularity&'
             'apiKey=00664c93e32e4db8ae93f46a260d5fd1')
        publish_dates=set()
        count_duplicates_per_request=0
        consecutive_same_articles = 0
        while True:
            if len(usa_today_articles) % 10 == 0:
                print(f"number of articles retrieved so far from usa today is : {len(usa_today_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(usa_today_articles)
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
                    if previous_article_count == len(usa_today_articles):
                        consecutive_same_articles += 1
                    if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                        break

                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break 
                if count_duplicates_per_request > self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from usa today news source is : {count_duplicates_per_request} , breaking ...")
                    break
                time.sleep(1) 
            else:
                print(f"Number of total articles retrieved from usa today news source is : {len(usa_today_articles)}")
                break

        return process_articles(usa_today_articles)
    
    
    def scrape_article_content_usa_today(self ,url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            div_element = soup.find('div', class_='gnt_ar_b')
            if div_element:
                paragraphs = div_element.find_all('p')[:-1] # remove the last paragraph
                article_text = '\n'.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
                return article_text.strip()
            else:
                div_element = soup.find('div', id='content-container')
                if div_element:
                    paragraphs = div_element.find_all('p')[:-2]
                    article_text = '\n'.join(paragraph.get_text(strip=True) for paragraph in paragraphs)
                    return article_text.strip()
                else:
                    print("Div element not found.")
                    return None
        else:
            print("Error:", response.status_code)
            return None
        

# =========================================================================================================================================
    def fetch_sky_news(self):
        usa_today_articles = []
        to = datetime.datetime.now().strftime('%Y-%m-%d')
        url = (f'https://newsapi.org/v2/everything?'
            'domains=skysports.com&'
            f'from={self.from_date}&to={to}&'
            'sortBy=publishedAt&'
            'apiKey=00664c93e32e4db8ae93f46a260d5fd1')
        publish_dates = set()
        count_duplicates_per_request = 0
        consecutive_same_articles = 0
        while True:
            if len(usa_today_articles) % 10 == 0:
                print(f"Number of articles retrieved so far from sky news is: {len(usa_today_articles)}")
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                previous_article_count = len(usa_today_articles)
                for article in articles:
                    title = article['title']
                    content = self.scrape_article_content_sky(article['url'])
                    if content:
                        content = remove_tags(content)
                        publish_date = article['publishedAt']
                        if publish_date not in publish_dates:
                            publish_dates.add(publish_date)
                            usa_today_articles.append({'title': title, 'content': content, 'publishdate': publish_date})
                        else:
                            count_duplicates_per_request += 1
                            continue
                    if previous_article_count == len(usa_today_articles):
                        consecutive_same_articles += 1
                    if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                        break

                if consecutive_same_articles >= self.max_consecutive_same_articles:  # Replace with desired threshold
                    break
                if count_duplicates_per_request > self.duplicates_seuil:
                    print(f"Number of duplicate articles retrieved from Sky Sports source is: {count_duplicates_per_request}, breaking...")
                    break
                time.sleep(1)
            else:
                print(f"Failed to retrieve articles with status code {response.status_code}")
                break

        print(f"Number of total articles retrieved from Sky Sports source is: {len(usa_today_articles)}")
        return process_articles(usa_today_articles)

    

    def scrape_article_content_sky(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find('div', class_='section-wrap')
            if articles:
                body = articles.find('div', class_='sdc-article-body sdc-article-body--lead')
                if body:
                    paragraphs = body.find_all('p')
                    article_text = ''.join([p.text for p in paragraphs])
                    return article_text
                else:
                    print(f"No article body found in {url}")
                    return None
            else:
                print(f"No articles found in {url}")
                return None
        else:
            print(f"Failed to retrieve {url} with status code {response.status_code}")
            return None

# =========================================================================================================================================
# =========================================================================================================================================