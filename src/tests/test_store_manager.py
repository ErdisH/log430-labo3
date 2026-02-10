"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1. Créez un article (`POST /products`)
    product_data = {'name': 'Some Item', 'sku': '12345', 'price': 99.90}
    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    print(response.get_data(as_text=True))
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['product_id'] > 0 

    # 2. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    product_id = data['product_id']
    response = client.post('/stocks',
                           json = {'product_id' : product_id, 
                                   'quantity': 5}
                           )
    
    assert response.status_code == 201
    product_data = response.get_json()

    # 3. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    response = client.get(f'/stocks/{product_id}')

    assert response.status_code == 200

    stock_data = response.get_json()
    assert stock_data['quantity'] == 5

    # 4. Faites une commande de l'article que vous avez crée, 2 unités (`POST /orders`)
    response = client.post(
        '/orders',
        json={
            'user_id': 1,
            'items': [
                {'product_id': product_id, 'quantity': 2}
            ]
        }
    )

    assert response.status_code == 201
    order_data = response.get_json()
    assert order_data['order_id'] > 0

    # 5. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 200
    stock_data = response.get_json()
    assert stock_data['quantity'] == 3

    # 6. Étape extra: supprimez la commande et vérifiez le stock de nouveau. Le stock devrait augmenter après la suppression de la commande.
    order_id = order_data['order_id']

    delete_resp = client.delete(f'/orders/{order_id}')
    assert delete_resp.status_code in (200, 204)

    if delete_resp.status_code == 200:
        delete_data = delete_resp.get_json()
        assert delete_data['deleted'] is True

    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 200
    stock_data = response.get_json()
    assert stock_data['quantity'] == 5