import json
import os
import requests
from bs4 import BeautifulSoup
import regex
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from helper.envconfig import load_env

currentDir = os.getcwd()

access_rights = 0o755
load_env()
def mkdirp(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory) 


def link_checker(url):
    urlEncode = url.replace(" ", "+")
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    page = session.get(urlEncode)

    soup = BeautifulSoup(page.content, 'html.parser')
    passages = soup.find_all('div', class_='passage-content')
    return passages

with open("json/monitor.json") as monitor_file:
    monitor = json.load(monitor_file)
    with open("json/books.json") as json_file:
        data = json.load(json_file)
        translations = data["shortcut"][monitor["currentTranslation"]:]
        for translation in translations:
            tanslateDir = currentDir + "/json/" + translation
            if os.path.isdir(tanslateDir) == False:
                os.mkdir(tanslateDir, access_rights)
            testaments = ["old", "new"]
            testaments = testaments[monitor["currentTestament"]:]
            for testament in testaments:
                new_testament_translations = ['DLNT', 'PHILLIPS', 'MOUNCE', 'NMB', 'NTE', 'RGT', 'WE']
                if (translation in new_testament_translations) and (translation == 'old'):
                    continue
                testament_books = data[testament][monitor["currentBook"]:]
                for book in testament_books:
                    for k, v in book.items():
                        abbrev = v.split("|")
                        abbBook = abbrev[0]
                        numOfVerses = int(abbrev[1]) + 1
                        current_verses = range(1, numOfVerses)[monitor["currentChapter"]:]

                        book_url = os.environ["DOMAIN"]+"?search="+k+"&version="+translation

                        book_passages = link_checker(book_url)
                        
                        if len(book_passages) == 0:
                            print("\n\n\n======================================================\n\n\n\n")
                            print("Translation", translation)
                            print("Book", k)
                            print("Book does not exist")
                            print("\n\n======================================================\n\n")
                            continue

                        for chapter in current_verses:
                            url = "https://www.biblegateway.com/passage/?search="+k+"+"+str(chapter)+"&version="+translation

                            passages = link_checker(url)
                            # If Page does not exist move to next chapter
                            if len(passages) == 0:
                                continue

                            passageWrapper = passages[0].find_all("div", class_="text-html")

                            # print(passageWrapper.prettify())
                            currentPassage = passageWrapper[0]
                            
                            verses = currentPassage.find_all('p')
                            dataChapter = {}
                            for verse in verses:
                                eachVerses = verse.find_all("span", class_="text")

                                # print(eachVerses)
                                for eachVerse in eachVerses:
                                    replacer = abbBook+"-"+str(chapter)+"-"
                                    verseNum = eachVerse.get("class")[1].replace(replacer, "")

                                    scripture = regex.search(r"(?P<num>^\d[\d\-\s]*)(?P<verse>.+)", eachVerse.get_text())
                                    scripture = scripture if scripture is not None else regex.search(r"(?P<verse>.+)", eachVerse.get_text())
                                    
                                    if scripture is not None:
                                        dataChapter[verseNum] = dataChapter[verseNum] +" "+ scripture["verse"] if verseNum in dataChapter else scripture["verse"]


                                    dataChapter[verseNum] = dataChapter[verseNum].replace("\u2019", "'").replace("\u2018", "'") 
                            
                            # Get Dirrectory path
                            fileDir = tanslateDir+"/"+testament+"/"+k
                            mkdirp(fileDir.replace(" ", "_"))
                            filepathSpace = fileDir+"/"+str(chapter)+".json"
                            filepath = filepathSpace.replace(" ", "_")

                            monitor["currentChapter"] = int(monitor["currentChapter"]) + 1

                            with open(filepath, 'w') as outfile:
                                json.dump(dataChapter, outfile)
                                with open("json/monitor.json", 'w') as output_monitor_file:
                                   json.dump(monitor, output_monitor_file) 
                            print("\n\n\n======================================================\n\n\n\n")
                            print("Translation", translation)
                            print("Book", k)
                            print("Chapter", chapter)
                            print("\n\n======================================================\n\n")

                        
                    monitor["currentChapter"] = 0
                    monitor["currentBook"] = monitor["currentBook"] + 1

                monitor["currentChapter"] = 0
                monitor["currentBook"] = 0
                monitor["currentTestament"] = monitor["currentTestament"] + 1

            monitor["currentChapter"] = 0
            monitor["currentBook"] = 0
            monitor["currentTestament"] = 0
            monitor["currentTranslation"] = monitor["currentTranslation"] + 1
