from bs4 import BeautifulSoup # For HTML parsing
import requests
import time
import urllib.parse
#   from selenium import webdriver
import json
import pandas as pd
import re
import argparse

def find_num_pages(query, location, delay):
    base_url = 'https://www.indeed.com/jobs?q={}&l={}&start=0'.format(query, location)
    page_nums = [link.get_text() for link in get_soup(base_url, delay).find_all('span', {'class': 'pn'})]
    while('Next' in "".join(page_nums)):
        base_url = "=".join(base_url.split("=")[:-1]) + "=" + str(int(base_url.split("=")[-1])+10)
        page_nums = [link.get_text() for link in get_soup(base_url, delay).find_all('span', {'class': 'pn'})]
    if len(page_nums) == 0:
        print("NO RESULTS!!")
        exit()
    return int(page_nums[-1]) + 1

def get_soup(url, delay):
    #     driver = webdriver.Firefox(executable_path=r'D:\Downloads\geckodriver-v0.24.0-win64\geckodriver.exe')
    #     driver.get(url)
    #     html = driver.page_source
    #     soup = BeautifulSoup(html, 'html.parser')
    #     driver.close()
    response = requests.get(url)
    time.sleep(delay)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup

def grab_job_links(soup):
    urls = []
    for link in soup.find_all('div', {'class': 'title'}):
        url = link.a.get('href')
        urls.append(r"https://www.indeed.com" + url)
    return urls

def grab_all_job_links(query, location, num_pages, delay):
    urls = []
    for i in range(1, num_pages+1):
        num = (i-1) * 10
        base_url = 'https://www.indeed.com/jobs?q={}&l={}&start={}'.format(query, location, num)
        try:
            soup = get_soup(base_url, delay)
            urls += grab_job_links(soup)
        except:
            continue
    return urls

def clean_text(text):
    text = ''.join(c for c in str(text) if ord(c) < 128)
    return re.sub('\s+', ' ', text).strip()

def get_posting(url, delay):
    print(url)
    soup = get_soup(url, delay)
    title = soup.find(name='h3', attrs={'class': "icl-u-xs-mb--xs icl-u-xs-mt--none jobsearch-JobInfoHeader-title"}).get_text()
    posting = soup.find(name='div', attrs={'class': "jobsearch-jobDescriptionText"}).get_text()
    return clean_text(title), clean_text(posting)

def get_postings_dict(urls, delay):
    print("Parsing {} urls".format(len(urls)))
    postings_dict = {}
    for i, url in enumerate(urls):
        title, posting = get_posting(url, delay)
        postings_dict[i] = {}
        postings_dict[i]['title'], postings_dict[i]['posting'], postings_dict[i]['url'] = title, posting, url
        if i % 10 == 9:
            print("{} urls parsed, {} urls left to go".format(i+1, len(urls) - 1 - i))
    return postings_dict

def save_json(query, location, postings_dict):
    file_name = urllib.parse.unquote(query + '_' + location + '.json')
    with open(file_name, 'w') as f:
        json.dump(postings_dict, f , indent=4)

def save_csv(query, location, postings_dict):
    file_name = urllib.parse.unquote(query + '_' + location + '.csv')
    df = pd.DataFrame(columns=["title", "posting", "url"])
    for v in postings_dict.values():
        df = df.append(v , ignore_index=True)
    df.to_csv(file_name)

def main(args):
    location = urllib.parse.quote(args.location)
    query = urllib.parse.quote(args.query)
    delay = args.delay
    print("Generating urls..")
    if(args.pages == 'all'):
        num_pages = find_num_pages(query, location, delay)
    else:
        num_pages = int(args.pages)
    if num_pages < 1:
        print("Number of pages must be >= 1 .")
        exit()
    all_urls = grab_all_job_links(query, location, num_pages, delay)
    postings_dict = get_postings_dict(all_urls, delay)
    save_json(query, location, postings_dict)
    save_csv(query, location, postings_dict)
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=r'Scrapes Job title, Description and url @https://www.indeed.com into csv and json')
    parser.add_argument('-l', '--location', type=str, default="United_States", help="location")
    parser.add_argument('-q', '--query', type=str, required=False, help="query to be searched")
    parser.add_argument('-p', '--pages', type=str, required=True, help="number of pages to be searched or all")
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='delay between url request. shorter => faster but easy to get blocked')
    args = parser.parse_args()
    main(args)