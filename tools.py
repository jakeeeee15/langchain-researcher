import urllib3
import os
from langchain.tools import tool
from bs4 import BeautifulSoup
from ddgs import DDGS

# @tool
def get_info_from_query(query):
    """Gets the text from the query. Can be used for searching the internet
        Just pass the query and function will search on the internet and give the text
    """
    search_result_urls = []
    num = 1
    with DDGS() as ddgs:
        raw_response = ddgs.text(query, max_results=num)

        for res in raw_response:
            search_result_urls.append(res.get("href"))


    http = urllib3.PoolManager()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    final_text=""
    for url in search_result_urls:
        try:
            response = http.request('GET', url, headers=headers, timeout=10.0)

            if response.status != 200:
                return "fetch failed with status " + str(response.status)
            html_text = response.data.decode('utf-8', errors='replace')

        except urllib3.exceptions.HTTPError as e:
            print('Fetch failed due to ' + str(e))
            return "fetch failed due to " + str(e)

        soup = BeautifulSoup(html_text, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        raw_text = soup.get_text()
        lines = (line.strip() for line in raw_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        clean_text = clean_text[:3000]
        final_text += clean_text


    return final_text


if __name__ == '__main__':
    print(get_info_from_query("who won fifa 26"))




