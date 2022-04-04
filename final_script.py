from bs4 import BeautifulSoup
import json
import urllib.request
from urllib.error import HTTPError
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="test123")

cursor = conn.cursor()

file_name = "Send money all over the world - online, cheap, fast.html"

with open(file_name, "r") as html_file:
    content = html_file.read()

soup = BeautifulSoup(content, "lxml")

webpage_string = soup.find(attrs={'ng-controller': 'countryBoxController'}).get('ng-init')[11:-1]

webpage_json = json.loads(webpage_string)


def get_countryname_by_cur(cur_code, numeric_code=''):
    if cur_code == 'EUR':
        return ''
    with urllib.request.urlopen(f'https://restcountries.com/v2/currency/{cur_code}?fields=name,numericCode') as url:
        data = json.loads(url.read().decode())

    if len(data) == 1:
        return data[0]['name']
    else:
        for d in data:
            if d['numericCode'] == numeric_code:
                return d['name']


def country_codes_fetch():
    countries = webpage_json['Countries']
    list_of_concodes = []
    for country in countries:
        code_alpha2 = country['CodeAlpha2']
        list_of_concodes.append(code_alpha2)
    return list_of_concodes


list_of_concodes = country_codes_fetch()

for concode in list_of_concodes:
    try:
        with urllib.request.urlopen(f'https://www.sendvalu.com/service/orders/price-config/{concode}') as url:
            data = json.loads(url.read().decode())

    except HTTPError:
        continue

    del_curs = data['Value']['DeliveryCurrencies']

    for del_cur in del_curs:

        recip_country_cur_name = del_cur['CurrencyPriceConfig']['Currency']['Name']
        recip_country_name = get_countryname_by_cur(del_cur['CurrencyPriceConfig']['Currency']['Code'],
                                                    del_cur['CurrencyPriceConfig']['Currency']['Number'])

        client_currencies_list = del_cur['ClientCurrencies']

        for client_currency in client_currencies_list:
            sender_country_cur_name = client_currency['Currency']['Name']
            sender_country_name = get_countryname_by_cur(client_currency['Currency']['Code'],
                                                         client_currency['Currency']['Number'])

            cursor.execute(f'''INSERT INTO "Sendvalu"(recip_country, recip_currency, sender_country, sender_currency)
                              VALUES ('{recip_country_name}', '{recip_country_cur_name}', '{sender_country_name}', '{sender_country_cur_name}')''')
            conn.commit()
    print(f'{concode} parsed')
