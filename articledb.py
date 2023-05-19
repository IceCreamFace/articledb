import sqlite3
from newspaper import Article
import feedparser
import hashlib

def make_article_hash(article_link):
    md5_hash = hashlib.md5()
    md5_hash.update(article_link.encode('utf-8'))
    return md5_hash.hexdigest()

def create_article_table(conn):
    #create cursosr
    cursor = conn.cursor()
    
    #careate table
    create_table_querey = '''
    CREATE TABLE IF NOT EXISTS articles (
        id VACHAR(32) PRIMARY KEY,
        title TEXT,
        author TEXT,
        content TEXT,
        summary TEXT,
        pub_date DATE
    );
    '''
    cursor.execute(create_table_querey)

    
def load_feeds():
    RSS_FEED_FILE = 'rss_feeds.txt'
    try:
        with open(RSS_FEED_FILE,'r') as file:
            rss_feeds = file.read().splitlines()
        return rss_feeds
    except FileNotFoundError:
        print("Could not find the file {}. Please check your file path.".format(RSS_FEED_FILE))
        exit()

def get_article(article_link):
    try:
        article = Article(article_link)
        article.download()
        article.parse()
        return article
    except Exception as e:
        print("Error in parsing article: ", e)
        return None

def get_article_links(feed):
    try:
        rss_feed = feedparser.parse(feed)
        entries = rss_feed.entries
        article_links = []

        for entry in entries:
            article_links.append(entry.link)
        return article_links
    except Exception as e:
        print("Error in parsing RSS feed: ", e)
        return None

def insert_article(conn,article):
    # Check if article is empty
    if article is None:
        return None
    if  article.text is None or article.text == "":
        print("Looks like article is empty, not adding")
        return None

    article_hash = make_article_hash(article.url)
    print(f"Title: {article.title} Hash: {article_hash}")

    #Check if their are multiple Authors
        #if there are comma serperate them into one string 
    if len(article.authors) > 1:
        for author in article.authors:
            article_authors = ', '.join(article.authors)

        #if there's no author give an empty string
    elif len(article.authors) < 1:
        article_authors = ""

       #if there's one author just put their name in
    else: 
        article_authors = article.authors[0]
    try:
        cursor = conn.cursor()
        insert_query = '''
        INSERT INTO articles (id,title ,author, content,summary, pub_date)
        VALUES (?, ?, ?, ?, ?, ?)
        '''
        article_data = (
                    article_hash,
                    article.title, 
                    article_authors,
                    article.text, 
                    article.summary,
                    article.publish_date
                    )
        cursor.execute(insert_query,article_data)

        #commit changes
        conn.commit()
    except sqlite3.Error as e:
        print("Error adding article: ",e)

def connect_db():
    # Create connection to sqlite
    try:
        db_connection = sqlite3.connect('articles.db')
    except sqlite3.Error as e:
        print("Error connecting to DB: ",e)
        exit(1)
    return db_connection

db_connection = connect_db()
# load RSS feeds
rss_feeds = load_feeds()
# Make  the table if it doesnt exist
create_article_table(db_connection)

for feed in rss_feeds:
    #Get all the links from a feed
    article_links = get_article_links(feed)

    for article_link in article_links:
            #get the article frm a link
           article = get_article(article_link)
           #put the article in a database
           insert_article(db_connection,article)
           
#close the connection to the DB
db_connection.close()
