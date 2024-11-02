# aws_photo_data


Project Description: AWS Configuration for Image Metadata Analysis System
The Image Metadata Analysis System is a cloud-based solution designed to streamline the process of image upload, analysis, and retrieval using AWS services. As a data analyst currently learning AWS, I sought to create a project that not only enhances my skills but also automatically gathers valuable data from real users. This project aims to harness the power of cloud computing to provide a user-friendly interface for managing image metadata.

Purpose

The purpose of this project is to enable users—both private and public—to easily upload images and receive real-time analysis and feedback on the content of those images. By leveraging image analysis services, users can gain insights through automatically generated labels, improving their experience and understanding of the visual data they are working with.

The system is structured to maintain a clear distinction between private functionalities, focusing on my own image analysis and management, and public capabilities that allow users to interact with the system through a web interface. By gathering data directly from real users, this project not only serves as a practical application of my AWS learning but also generates a rich dataset for future analysis.

Both workflows store their analysis results in the same DynamoDB database, ensuring that all metadata is centralized and accessible, regardless of whether the images were uploaded through the public or private interface. This cohesive approach supports efficient data management and enhances the overall utility of the project.

Workflows
Public Workflow

Users upload an image via a web page hosted on Amplify, rather than through the AWS Console.
The image is saved to a public S3 Bucket.
The S3 Bucket triggers a Lambda Function upon image upload.
The Lambda Function extracts the image name from the event.
The Lambda Function analyzes the image using an image analysis service.
The analysis service returns labels to the Lambda Function.
The Lambda Function writes the labels and image metadata to a shared DynamoDB database, ensuring centralized storage with data from the private workflow.
The Lambda Function deletes the image from the S3 Bucket.
The Lambda Function returns the labels to the user via the Amplify-hosted website.
Private Workflow

Users upload images directly to a separate private S3 Bucket.
A Lambda Function is triggered to analyze the latest uploaded file in the S3 Bucket.
The Lambda Function retrieves the latest file from the S3 Bucket.
The Lambda Function analyzes the image using an image analysis service.
The analysis service returns labels to the Lambda Function.
The Lambda Function writes the labels and image metadata to the same shared DynamoDB database, ensuring central storage for both workflows.
The Lambda Function deletes the image from the S3 Bucket.
The Lambda Function sends a notification with metadata to a notification service.
The notification service sends an email notification to the author with the analysis results.


Resources used:
AWS Account
DynamoDB Table
S3 Buckets (Private and Public)
AWS Lambda Functions (Private and Public)
Amazon Rekognition
SNS Topic
AWS Amplify
IAM Roles and Policies
CORS Configuration
Web Interface Design
