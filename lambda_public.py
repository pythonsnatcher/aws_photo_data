import boto3
import json
from datetime import datetime

# AWS Credentials (replace with actual values in production)
AWS_ACCESS_KEY_ID = '<YOUR_ACCESS_KEY_ID>'  # Replace with your actual Access Key ID
AWS_SECRET_ACCESS_KEY = '<YOUR_SECRET_ACCESS_KEY>'  # Replace with your actual Secret Access Key
AWS_DEFAULT_REGION = '<YOUR_REGION>'  # Replace with your actual region

# S3 Configuration
S3_BUCKET_NAME = '<YOUR_S3_BUCKET_NAME>'  # Hardcoded for testing

# Initialize the Rekognition client
rekognition_client = boto3.client(
    'rekognition',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Initialize the S3 client for deletion
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Initialize DynamoDB resource
dynamodb_client = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

# Specify the DynamoDB table name
DYNAMODB_TABLE_NAME = '<YOUR_DYNAMODB_TABLE_NAME>'  # Ensure this matches your DynamoDB table name
table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)


def write_to_dynamodb(image_name, labels, deleted_image_info):
    """Write image metadata and deleted S3 object info to DynamoDB."""
    try:
        item = {
            'image_name': image_name,  # Primary key attribute
            'labels': labels,
            'deleted_image_info': deleted_image_info  # Additional info about the deleted image
        }
        print(f"Attempting to insert item: {item}")

        # Put the item in the DynamoDB table
        response = table.put_item(Item=item)
        
        # Check the response for any errors
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
            print(f"Failed to write to DynamoDB: {response}")
        else:
            print(f"Successfully inserted {item} into DynamoDB table {DYNAMODB_TABLE_NAME}.")

    except Exception as e:
        print(f"Error writing to DynamoDB: {str(e)}")


def lambda_handler(event, context):
    # Extract the image name from the event
    image_name = event.get('image_name')
    if not image_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Image name not provided'})
        }

    # Analyze image
    try:
        response = rekognition_client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': S3_BUCKET_NAME,
                    'Name': image_name
                }
            },
            MaxLabels=15
        )

        # Extract labels
        labels = [label['Name'] for label in response['Labels']]

        # Prepare info about the deleted image
        deleted_image_info = {
            'image_name': image_name,
            'deletion_time': datetime.now().isoformat()  # Store the deletion timestamp
        }

        # Delete the image from S3
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=image_name)
        print(f"Deleted {image_name} from S3 bucket {S3_BUCKET_NAME}.")

        # Write labels and deletion info to DynamoDB
        write_to_dynamodb(image_name, labels, deleted_image_info)

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
