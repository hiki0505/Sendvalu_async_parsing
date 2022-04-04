import json
from bs4 import BeautifulSoup
from urllib.error import HTTPError
import psycopg2
import asyncio
import aiohttp
import time

start_time = time.time()


def country_codes_fetch(webpage_json):
    """
    Function for obtaining list of country codes, that support money transfer
    :param webpage_json: webpage in json format
    :return: list of country codes
    """
    countries = webpage_json['Countries']
    list_of_concodes = []
    for country in countries:
        code_alpha2 = country['CodeAlpha2']
        list_of_concodes.append(code_alpha2)
    return list_of_concodes


async def get_countryname_by_cur(session, cur_code, numeric_code=''):
    """
    For every currency we need to find its respective country. For that
    purpose we use 3-rd party API https://restcountries.com.
    :param session: current client session
    :param cur_code: currency numeric code
    :param numeric_code: numeric code of respective country
    :return: name of country
    """
    if cur_code == 'EUR':
        return ''
    async with session.get(url=f'https://restcountries.com/v2/currency/{cur_code}?fields=name,numericCode') as response:
        text = await response.read()
        data = json.loads(text.decode())

    if len(data) == 1:
        return data[0]['name']
    else:
        for d in data:
            if d['numericCode'] == numeric_code:
                return d['name']


async def get_country_data(session, concode, cur, con):
    """
    Get data for particular country
    :param session: current client session
    :param concode: country numeric code
    :param cur: postgres connection cursor
    :param con: postgres connection object
    :return: None
    """
    url = f'https://www.sendvalu.com/service/orders/price-config/{concode}'
    try:
        async with session.get(url=url) as response:
            text = await response.read()
            data = json.loads(text.decode())

            del_curs = data['Value']['DeliveryCurrencies']

            for del_cur in del_curs:
                recip_country_cur_name = del_cur['CurrencyPriceConfig']['Currency']['Name']
                recip_country_name = await get_countryname_by_cur(session,
                                                                  del_cur['CurrencyPriceConfig']['Currency']['Code'],
                                                                  del_cur['CurrencyPriceConfig']['Currency']['Number'])

                client_currencies_list = del_cur['ClientCurrencies']

                for client_currency in client_currencies_list:
                    sender_country_cur_name = client_currency['Currency']['Name']
                    sender_country_name = await get_countryname_by_cur(session, client_currency['Currency']['Code'],
                                                                       client_currency['Currency']['Number'])

                    cur.execute(f'''INSERT INTO "Sendvalu"(recip_country, recip_currency, sender_country, sender_currency)
                                                          VALUES ('{recip_country_name}', '{recip_country_cur_name}', '{sender_country_name}', '{sender_country_cur_name}')''')
                    con.commit()
    except (HTTPError, KeyError):
        pass


async def gather_data(cur, con):
    """
    Main function, where asynchronous parsing and writing to DB is applied
    :param cur: postgres connection cursor
    :param con: postgres connection object
    :return: None
    """
    async with aiohttp.ClientSession() as session:
        file_name = "Send money all over the world - online, cheap, fast.html"

        with open(file_name, "r") as html_file:
            content = html_file.read()

        soup = BeautifulSoup(content, "lxml")

        webpage_string = soup.find(attrs={'ng-controller': 'countryBoxController'}).get('ng-init')[11:-1]

        webpage_json = json.loads(webpage_string)

        list_of_concodes = country_codes_fetch(webpage_json)
        tasks = []
        for concode in list_of_concodes:
            task = asyncio.create_task(get_country_data(session, concode, cur, con))
            tasks.append(task)
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="test123")

    cursor = conn.cursor()

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Necessary for Windows users
    asyncio.run(gather_data(cursor, conn))
    end_time = time.time() - start_time
    print(f"\nExecution time: {end_time} seconds")
