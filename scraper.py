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

        # For some reason missing this data from 2006 on the website
        if current_year == 2006:
            continue

        url_100 = "https://www.billboard.com/charts/year-end/" + str(current_year) + "/hot-r-and-and-b-hip-hop-songs"
        raw_html_100 = simple_get(url_100)
        html_100 = BeautifulSoup(raw_html_100, 'html.parser')

        # Creates a list of strings that are the titles of the top songs in order
        all_titles = html_100.findAll("div", {"class": "ye-chart-item__title"})
        all_titles = [div.string.splitlines()[1] for div in all_titles]

        # Creates a list of strings that are the artists of the top songs in order
        # For loop deals with the fact that in the html the artists are sometimes stored differently
        all_artists = html_100.findAll("div", {"class": "ye-chart-item__artist"})
        for i in range(len(all_artists)):
            if all_artists[i].a is not None:
                all_artists[i] = all_artists[i].a.string.splitlines()[1]
            else:
                all_artists[i] = all_artists[i].string.splitlines()[1]

        # Creates a list of strings that are the ranks of the top songs in order
        # Necessary because some ranks are missing in the dataset
        all_ranks = [div.string[1: -1] for div in html_100.findAll("div", {"class": "ye-chart-item__rank"})]

        # Loops through every entry and looks it up on tunebat and then writes it to the csv file
        for i in range(len(all_ranks)):

            # Sometimes url lookup will randomly fail, so the try except allows us to just retry if that happens
            try:

                # Gets the current songs information
                rank = int(all_ranks[i])
                title = all_titles.pop(0)
                artist = all_artists.pop(0)

                # Deletes featuring and everything after it because this leads to it not being on tunebat
                if "Featuring" in artist:
                    artist = artist[:artist.index("Featuring")]

                tunebat_link = "https://tunebat.com/Search?q=" + title.replace(" ", "+") + "+" + artist.replace(" ", "+")
                raw_html_tunebat = simple_get(tunebat_link)
                html_tunebat = BeautifulSoup(raw_html_tunebat, 'html.parser')

                # Loops through the links on the search results page and finds the first one that directs to
                # a song info page. We will then visit that page
                for link in html_tunebat.find_all('a', href=True):
                    if link['href'][0: 5] == "/Info":
                        tunebat_link = "https://tunebat.com" + link['href']
                        raw_html_tunebat = simple_get(tunebat_link)
                        html_tunebat = BeautifulSoup(raw_html_tunebat, 'html.parser')
                        break

                # Will contain all the data for the song that Tunebat gives
                values = []

                # First table of values on site
                for data in html_tunebat.find_all("div", {"class": "row main-attribute-value"}):
                    values.append(data.string)

                # Second table of values on site
                for data in html_tunebat.findAll("td", {"class": "attribute-table-element"}):
                    values.append(data.string)

                    # Prevents repeats
                    if len(values) == 12:
                        break

                # Creates the values array
                display_row = values
                values.insert(0, artist)
                values.insert(0, title)
                values.insert(0, rank)
                values.insert(0, current_year)
                print(display_row)  # Progress meter

                # Writes the row to the csv file
                song_writer.writerow(values)

            except:
                i -= 1  # Subtracts 1 from i when a request fails so we can try the link again

        songs_file.flush()  # Every year flush the cache so that a failure does not mean loss of all data
