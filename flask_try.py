
import boto3


s3 = boto3.client(
    's3',
    endpoint_url='https://s3.filebase.com/',  # Filebase endpoint
    aws_access_key_id='00824DA011D6F5948962',
    aws_secret_access_key='uJQbUQBQagv3G2GYmPSphARFwMhVuqa8ko766ZHT',
    region_name='us-east-1'
)

BUCKET_NAME = 'project-images'
OBJECT_KEY = 'sample2.jpg'

url = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': BUCKET_NAME,
        'Key': OBJECT_KEY
    },
    ExpiresIn=3600  # 1 hour
)
print(url)