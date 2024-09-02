import requests
import pandas as pd
from datetime import datetime
from time import time

def fetch_data(api_key):
    url = 'https://uzshopping.retailcrm.ru/api/v5/orders'

    current_date = datetime.now().date()
    date = current_date.strftime('%Y-%m-%d')
    params = {
        'apiKey': api_key,
        'filter[createdAtFrom]': '2024-08-01',
        'filter[createdAtTo]': '2024-08-01',
    }

    r = requests.get(url, params=params)
    total_pages = r.json()['pagination']['totalPageCount']

    # Створення DataFrame
    df = pd.DataFrame(range(total_pages), columns=['p']).assign(st=0., en=0., t=None, r=None)

    def req(*a, **kw):
        response = requests.request(*a, **kw)
        return response.json()

    def apr(df, n, cr, ct, cs, ce, *a, **kw):
        def tsk(df, n, cr, cs, ce, *a, **kw):
            while True:
                try:
                    j = req(*a, **kw)
                    if j['success']:
                        break
                except Exception as e:
                    print(e, str(e))

            df.loc[n, cr] = [j]

        tsk(df, n, cr, cs, ce, *a, **kw)

    # Виконання запитів та оновлення DataFrame
    for n, row in df.iterrows():
        apr(df, n, 'r', 't', 'st', 'en', 'get', url, params={**params, 'page': row['p'] + 1})

    xx = df['r'].sum()
    df1 = pd.json_normalize({'data': xx}, record_path=['data', 'orders'], max_level=0)

    mask = ['number', 'status', 'customFields', 'items']
    df2 = df1[mask]

    df_items_expanded = df2.explode('items')

    def get_price_quantity(item):
        if isinstance(item, dict) and 'prices' in item and item['prices']:
            price_info = item['prices'][0]
            return price_info.get('price'), price_info.get('quantity')
        return None, None

    df_items_expanded[['price', 'quantity']] = df_items_expanded['items'].apply(lambda x: get_price_quantity(x)).apply(pd.Series)

    df_items_expanded['externalId'] = df_items_expanded['items'].apply(lambda x: x.get('offer', {}).get('externalId') if isinstance(x, dict) else None)
    df_items_expanded['comment'] = df_items_expanded['items'].apply(lambda x: x.get('comment') if isinstance(x, dict) else None)
    df_items_expanded['name'] = df_items_expanded['items'].apply(lambda x: x.get('offer', {}).get('name') if isinstance(x, dict) else None)

    def get_custom_field(field, custom_fields):
        return custom_fields.get(field) if isinstance(custom_fields, dict) else None

    df_items_expanded['item_buyer_id'] = df_items_expanded['customFields'].apply(lambda x: get_custom_field('buyer_id', x))
    df_items_expanded['item_offer_id'] = df_items_expanded['customFields'].apply(lambda x: get_custom_field('offer_id', x))
    df_items_expanded['idupsellsite'] = df_items_expanded['customFields'].apply(lambda x: get_custom_field('idupsellsite', x))
    df_items_expanded['upsell_site'] = df_items_expanded['customFields'].apply(lambda x: get_custom_field('upsell_site', x))

    df_items_expanded = df_items_expanded.rename(columns = {'number': 'Номер замовлення',
                      'status': 'Статус',
                      'externalId': 'Product_id',
                      'name': 'Назва товару',
                      'quantity': 'Кількість товару',
                      'price': 'Ціна товару',
                      'item_offer_id': 'offer_id(заказа)',
                      'item_buyer_id': 'buyer_id',
                      'idupsellsite': 'upsell',
                      'upsell_site': 'upsell from site',
                      'comment': 'call-center'})


    df_items_expanded.drop(['customFields', 'items'], axis = 1)

    df = df_items_expanded

    df.dropna(subset=['Product_id'], inplace=True)
    df.dropna(subset=['buyer_id'], inplace=True)
    df['offer_id(товара)'] = df['Product_id'].apply(lambda x: '-'.join(x.split('-')[:3]))
    df['Загальна сума'] = df['Ціна товару'] * df['Кількість товару']


    desired_column_order = ['Номер замовлення', 'Статус', 'offer_id(товара)', 'Product_id', 'Назва товару', 'Кількість товару', 'Ціна товару', 'Загальна сума', 'offer_id(заказа)', 'buyer_id', 'upsell', 'upsell from site', 'call-center']

    df = df.reindex(columns=desired_column_order)

    unique_order_numbers = df['Номер замовлення'].nunique()

    df_wo_testy_dupl = df[~df['Статус'].isin(['testy','duplicate'])]
    leads = df_wo_testy_dupl['Номер замовлення'].nunique()

    df_wo_testy_dupl_trash = df[~df['Статус'].isin(['testy','duplicate', 'trash'])]
    clear_leads = df_wo_testy_dupl_trash['Номер замовлення'].nunique()

    appruv_temp = df_wo_testy_dupl_trash[~df_wo_testy_dupl_trash['Статус'].isin(['duplicate',
    'testy', 'trash', 'new', 'perezvon-1', 'telegram', 'no-call', 'cancel-other', 'peredumal',
    '1d-nedozvon','2d-nedozvon','3d-nedozvon'])]
    appruv = appruv_temp['Номер замовлення'].nunique()
    avg_appruv_sum = appruv_temp['Загальна сума'].sum() / appruv

    df_new = appruv_temp.dropna(subset=['upsell'])

    return df_new