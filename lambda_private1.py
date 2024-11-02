import boto3
import json
from datetime import datetime

# Hardcoded AWS Credentials (for testing)
AWS_ACCESS_KEY_ID = '<YOUR_ACCESS_KEY_ID>'  # Replace with your actual Access Key ID
AWS_SECRET_ACCESS_KEY = '<YOUR_SECRET_ACCESS_KEY>'  # Replace with your actual Secret Access Key
AWS_DEFAULT_REGION = '<YOUR_REGION>'  # Replace with your actual region

# Hardcoded S3 Configuration
S3_BUCKET_NAME = '<YOUR_S3_BUCKET_NAME>'  # S3 bucket for uploads

# Hardcoded SNS Configuration
SNS_TOPIC_NAME = '<YOUR_SNS_TOPIC_NAME>'  # Name of the SNS topic
SNS_TOPIC_ARN = '<YOUR_SNS_TOPIC_ARN>'  # ARN of the SNS topic
SNS_SUBSCRIBED_EMAIL = '<YOUR_SUBSCRIBED_EMAIL>'  # Email subscribed to SNS notifications

# Initialize clients
rekognition_client = boto3.client(
    'rekognition',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

dynamodb_client = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Specify the DynamoDB table name
DYNAMODB_TABLE_NAME = '<YOUR_DYNAMODB_TABLE_NAME>'  # Ensure this matches your DynamoDB table name
table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)

# Initialize SNS client
sns_client = boto3.client(
    'sns',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def write_to_dynamodb(image_name, labels):
    """Write image metadata to DynamoDB."""
    try:
        item = {
            'image_name': image_name,  # Primary key attribute
            'labels': labels,
            'deleted_image_info': {
                'image_name': image_name,
                'deletion_time': datetime.now().isoformat()  # Store the deletion timestamp
            }
        }
        print(f"Attempting to insert item: {item}")

        # Put the item in the DynamoDB table
        response = table.put_item(Item=item)

        # Check the response for any errors
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
            print(f"Failed to write to DynamoDB: {response}")
        else:
            print(f"Successfully inserted {item} into DynamoDB table {DYNAMODB_TABLE_NAME}.")

        return item  # Return the item for SNS notification

    except Exception as e:
        print(f"Error writing to DynamoDB: {str(e)}")
        return None

def send_sns_notification(item):
    """Send an SNS notification with the item details."""
    if item:
        message = json.dumps(item)
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='Image Analysis Result'
        )
        print(f"Sent SNS notification: {message}")
    else:
        print("No item to send in SNS notification.")

def lambda_handler(event, context):
    # Specify your bucket name
    bucket_name = S3_BUCKET_NAME

    # Get the latest file
    original_key = get_latest_file(bucket_name)

    if original_key is None:
        print("No files found in the bucket.")
        return

    try:
        print(f"Processing file from bucket: {bucket_name}")
        print(f"Original filename: {original_key}")

        # Analyze image
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': original_key
                }
            },
            MaxLabels=15
        )

        # Extract labels
        labels = [label['Name'] for label in response['Labels']]
        print(f"Detected labels: {labels}")

        # Delete the image from S3
        s3_client.delete_object(Bucket=bucket_name, Key=original_key)
        print(f"Deleted {original_key} from S3 bucket {bucket_name}.")

        # Write labels to DynamoDB and get the item for SNS
        item = write_to_dynamodb(original_key, labels)

        # Send SNS notification with the item
        send_sns_notification(item)

        return {
            'statusCode': 200,
            'body': json.dumps({'labels': labels})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_latest_file(bucket_name):
    """Retrieve the latest file in the specified S3 bucket."""
    response = s3_client.list_objects_v2(Bucket=bucket_name)

    # Check if there are any objects in the bucket
    if 'Contents' not in response:
        return None

    # Find the latest file
    latest_file = None
    latest_time = None

    for obj in response['Contents']:
        if latest_time is None or obj['LastModified'] > latest_time:
            latest_time = obj['LastModified']
            latest_file = obj['Key']

    return latest_file
