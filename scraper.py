from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import csv


# These three functions courtesy of https://realpython.com/python-web-scraping-practical-introduction/
def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can
    make it do anything.
    """
    print(e)


# brocklewis9@gmail.com
# Open the file
with open('songs.csv', mode='w', encoding="utf-8", newline='') as songs_file:
    song_writer = csv.writer(songs_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for current_year in range(2002, 2019):

        # For some reason missing this data
        if current_year == 2006:
            continue

        url_100 = "https://www.billboard.com/charts/year-end/" + str(current_year) + "/hot-r-and-and-b-hip-hop-songs"
        raw_html_100 = simple_get(url_100)
        html_100 = BeautifulSoup(raw_html_100, 'html.parser')

        all_titles = html_100.findAll("div", {"class": "ye-chart-item__title"})
        all_titles = [div.string.splitlines()[1] for div in all_titles]

        all_artists = html_100.findAll("div", {"class": "ye-chart-item__artist"})

        all_ranks = [div.string[1: -1] for div in html_100.findAll("div", {"class": "ye-chart-item__rank"})]
        print(all_ranks)
        for i in range(len(all_artists)):
            if all_artists[i].a is not None:
                all_artists[i] = all_artists[i].a.string.splitlines()[1]
            else:
                all_artists[i] = all_artists[i].string.splitlines()[1]

        # For some reason hot 100 missing some titles

        for i in range(len(all_ranks)):

            try:
                rank = int(all_ranks[i])
                title = all_titles.pop(0)
                artist = all_artists.pop(0)

                if "Featuring" in artist:
                    artist = artist[:artist.index("Featuring")]

                tunebat_link = "https://tunebat.com/Search?q=" + title.replace(" ", "+") + "+" + artist.replace(" ", "+")
                # delete words off artist until result found
                # delete x's

                raw_html_tunebat = simple_get(tunebat_link)
                html_tunebat = BeautifulSoup(raw_html_tunebat, 'html.parser')
                for link in html_tunebat.find_all('a', href=True):
                    if link['href'][0: 5] == "/Info":
                        tunebat_link = "https://tunebat.com" + link['href']
                        raw_html_tunebat = simple_get(tunebat_link)
                        html_tunebat = BeautifulSoup(raw_html_tunebat, 'html.parser')
                        break

                values = []

                for data in html_tunebat.find_all("div", {"class": "row main-attribute-value"}):
                    values.append(data.string)

                for data in html_tunebat.findAll("td", {"class": "attribute-table-element"}):
                    values.append(data.string)

                    if len(values) == 12:
                        break

                display_row = values
                values.insert(0, artist)
                values.insert(0, title)
                values.insert(0, rank)
                values.insert(0, current_year)
                print(display_row)

                song_writer.writerow(values)

            except:
                i -= 1

        songs_file.flush()
