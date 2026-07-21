import boto3
import random
from datetime import datetime, timedelta, UTC


def populate_existing_table():
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
    table = dynamodb.Table("Transactions")

    now = datetime.now(UTC)
    sample_items = []

    # Scenario A: Budiono Santoso -> Fair transaction pattern
    for i in range(2):
        tx_time = now - timedelta(hours=i*2)
        sample_items.append({
            'userId': "Budiono Santoso",
            'transactionId': f'tx_100{i}',
            'amount': random.randint(50, 400),
            'timestamp': tx_time.isoformat().replace('+00:00', 'Z'),
            'location': 'Jakarta'
        })

    # Scenario B: Budisan Onotoso -> Trigger 'Velocity Check'
    for i in range(6): 
        tx_time = now - timedelta(minutes=i*4)
        sample_items.append({
            'userId': 'Budisan Onotoso',
            'transactionId': f'tx_200{i}',
            'amount': random.randint(100, 300),
            'timestamp': tx_time.isoformat().replace('+00:00', 'Z'),
            'location': 'Surabaya'
        })

    # Scenario C: Budi Aja -> Have a single transaction of extreme value
    sample_items.append({
        'userId': 'Budi Aja',
        'transactionId': 'tx_3001',
        'amount': 7500,
        'timestamp': now.isoformat().replace('+00:00', 'Z'),
        'location': 'Medan'
    })

    # Scenario D: Budi Ajelah -> A single normal transaction
    sample_items.append({
        'userId': 'Budi Ajelah',
        'transactionId': 'tx_4001',
        'amount': 1200,
        'timestamp': now.isoformat().replace('+00:00', 'Z'),
        'location': 'Denpasar'
    })

    try:
        with table.batch_writer() as batch:
            for item in sample_items:
                batch.put_item(Item=item)
                print(f"Input success: {item['userId']} | Transaction ID: {item['transactionId']} | Total: {item['amount']}")
        print("\n[SUCCESS] Successful upload data to Amazon DynamoDB")
    except Exception as e:
        print(f"\n[ERROR] Failed upload data. Detail: {e}")


if __name__ == '__main__':
    populate_existing_table()