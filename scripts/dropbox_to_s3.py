import os
import logging
from datetime import datetime
import dropbox
import boto3
from botocore.exceptions import NoCredentialsError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def transfer_from_dropbox_to_s3():
    # Load configuration
    dropbox_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    dropbox_folder = os.environ.get('DROPBOX_FOLDER_PATH', '')
    
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket = os.environ.get('S3_BUCKET_NAME')
    s3_prefix = os.environ.get('S3_PREFIX', 'dropbox-sync')

    if not all([dropbox_token, aws_access_key, aws_secret_key, s3_bucket]):
        logging.error("Missing required environment variables for authentication.")
        return False

    try:
        logging.info("Initializing Dropbox client...")
        dbx = dropbox.Dropbox(dropbox_token)
        
        logging.info("Initializing AWS S3 client...")
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        logging.info(f"Listing files in Dropbox folder: '{dropbox_folder}'")
        folder_contents = dbx.files_list_folder(dropbox_folder)
        
        for entry in folder_contents.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                local_tmp_path = f"/tmp/{entry.name}"
                s3_key = f"{s3_prefix}/{entry.name}"
                
                logging.info(f"Downloading '{entry.name}' from Dropbox...")
                dbx.files_download_to_file(local_tmp_path, entry.path_lower)
                
                logging.info(f"Uploading '{entry.name}' to S3 bucket '{s3_bucket}'...")
                s3.upload_file(local_tmp_path, s3_bucket, s3_key)
                
                logging.info(f"Successfully transferred: {entry.name}")
                
                # Cleanup local temp file
                if os.path.exists(local_tmp_path):
                    os.remove(local_tmp_path)
                    
        logging.info("All files transferred successfully.")
        return True
        
    except dropbox.exceptions.ApiError as dbx_err:
        logging.error(f"Dropbox API error occurred: {dbx_err}")
    except NoCredentialsError:
        logging.error("AWS credentials not correctly provided.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        
    return False

if __name__ == "__main__":
    logging.info("Starting scheduled Dropbox to S3 transfer job.")
    success = transfer_from_dropbox_to_s3()
    if success:
        logging.info("Job completed successfully.")
    else:
        logging.error("Job failed.")
