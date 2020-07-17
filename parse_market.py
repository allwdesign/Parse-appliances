import csv
import logging
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin


def write_csv_output():
    """Save information about wash machine into CSV file."""
    with open('output_wash.csv', 'a', encoding='utf-8', newline='') as f:
        output_writer = csv.DictWriter(
            f,
            ['Page Url', 'Category', 'Brand', 'Model', 'Image Urls'])
        output_writer.writeheader()

        for (url, category, brand, model, img_url) in get_value_for_csv():
            output_writer.writerow({
                'Page Url': url,
                'Category': category,
                'Brand': brand,
                'Model': model,
                'Image Urls': img_url})


def get_value_for_csv():
    """Get the data to write into the CSV file.

    Return: generator object with data (url, category, brand, model, img_url).
    """
    appliances = parse(
        xpath="//div[@data-tid-prop='eadaba91']/h3/a",
        attr="href",
        next_path="//a[contains(@class, 'n-pager__button-next')]")

    for i, url in enumerate(appliances):
        logging.info(f'{i} URL: {url}')
        # Go to detail page with description
        get_specified_page(url=url)

        # Finds and return all images on the description page.
        d_imgs = parse(
            xpath="//div[@id='ProductImageGallery']/div/meta[@itemprop='url']",
            attr="content")

        # Go to reviews
        get_specified_page(
            xpath="//li[@class='_1OM4gu7kXK QjE88eF2HX']/div/a[@class='_2XmtVnQ64x']",
            domain=DOMAIN)

        r_next = ("//div[contains(@class, '_2_5RybEwCd')]/"
                  "a[contains(@class, '_2qvOOvezty _19m_jhLgZR _1tnkq5973M')]")
        # Reviews Images
        r_imgs = parse(
            xpath="//picture[contains(@data-tid-prop, 'dc1632ca')]/img",
            attr="src",
            next_path=r_next)

        imgs = d_imgs + r_imgs
        logging.info(f'IMGS: {imgs}')

        names = browser.find_elements_by_xpath("//span[@itemprop='name']")
        category, brand = [x.text for x in names]

        h1_tags = browser.find_elements_by_xpath("//h1")
        model = h1_tags[0].text.split(brand)[1].strip()

        if imgs:
            for img_url in imgs:
                yield (url, category, brand, model, img_url)


def wait_if_captcha(func):
    """If the page is captcha, then it waits until the user enters captcha."""
    def modified(*args, **kwargs):
        if browser.title == "Ой!":
            logging.info("Captcha")
            time.sleep(15)

        return func(*args, **kwargs)

    return modified


@wait_if_captcha
def get_specified_page(xpath="", url="", domain="", t=5):
    """Gets the specified page."""
    try:
        if not url:
            elements = browser.find_elements_by_xpath(xpath)
            url = elements[0].get_attribute('href')
            logging.info(f'Get the page: {url}')

        browser.get(urljoin(domain, url))
        time.sleep(t)
        return True
    except NoSuchElementException as e:
        logging.error(e)
        return
    except IndexError as e:
        logging.error(e)
        return


def parse(links=[], xpath="", attr="", next_path=""):
    """Find all links to the necessary elements on the page if necessary,
    go to the next page.

    Return: a list of all URLs.
    """
    urls = links[:]
    logging.info(f'Parse elements with attribute: {attr}.')

    elements = browser.find_elements_by_xpath(xpath)
    if elements:
        urls += [el.get_attribute(attr) for el in elements]

    while get_specified_page(next_path):
        return parse(urls, xpath, attr, next_path)

    return urls


def main():
    urls = [
        "https://market.yandex.ru/"
        "catalog--stiralnye-mashiny-v-krasnodare/16673392/"
        "list?hid=90566&local-offers-first=0&onstock=1",
        ]

    get_specified_page(url=urls[0])
    write_csv_output()
    browser.quit()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    SELENIUM_DRIVER_EXECUTABLE_PATH = '/usr/local/bin/geckodriver'
    DOMAIN = 'https://market.yandex.ru'
    browser = webdriver.Firefox(executable_path=SELENIUM_DRIVER_EXECUTABLE_PATH)
    browser.maximize_window()
    main()
