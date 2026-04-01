import requests
from celery import shared_task

@shared_task
def trigger_invoice_generation(order_data):
    url = "http://127.0.0.1:8001/generate-invoice/"
    try:
        response = requests.post(url, json=order_data, timeout=10)
        return response.json()
    except requests.exceptions.RequestException as e:
        # Celery can automatically retry this later if it fails!
        print(f"FastAPI Invoice Service Error: {e}")