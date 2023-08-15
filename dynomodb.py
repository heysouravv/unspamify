import boto3
from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key,Attr
import os
from uuid import uuid4
import hashlib
from datetime import datetime
def init_user(mailbox:str, user_email:str,refresh_token:str):
    load_dotenv()
    session = boto3.Session(
        aws_access_key_id=os.getenv('ACCESS_KEY'),
        aws_secret_access_key=os.getenv('ACCESS_KEY_PRIVATE'),
        region_name=os.getenv('REGION')
    )

    # Create a DynamoDB client and resource
    dynamodb_client = session.client('dynamodb')
    dynamodb_resource = session.resource('dynamodb')
    desired_hash = hashlib.sha256(user_email.encode('utf-8')).hexdigest()
    table_name = 'unspamifyUsers'
    table = dynamodb_resource.Table(table_name)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('privateHash').eq(desired_hash)
    )
    if not response.get('Items'):
        try:
            item = {
                'date_created': str(datetime.now().strftime('%d-%m-%y:%H:%M')),
                'mailbox': mailbox,
                'user_email': user_email,
                'refresh_token': refresh_token,
                'email_discovered' : 0,
                'email_removed' : 0,
                'last_checked' : '',
                'privateHash' : desired_hash
            }
            put_response = table.put_item(Item=item)
            print("PutItem succeeded:", put_response)
        except Exception as e:
            print("Error:", e)
    else:
        print("Item with privateHash already exists")
