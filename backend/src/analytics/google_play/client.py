from typing import List
from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default

class GooglePlayStorageClient:
    def __init__(self, bucket_name: str, auth_mode: str = "cloud_run_service_identity", 
                 service_account_email: str = None, secret_resource_name: str = None):
        self.bucket_name = bucket_name
        self.auth_mode = auth_mode
        self.service_account_email = service_account_email
        self.secret_resource_name = secret_resource_name
        self._storage_client = None

    def _get_client(self) -> storage.Client:
        if self._storage_client is None:
            # We are using application default credentials (ADC)
            credentials, project = default()
            self._storage_client = storage.Client(credentials=credentials)
        return self._storage_client

    def list_objects(self, prefix: str) -> List[storage.Blob]:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        return list(bucket.list_blobs(prefix=prefix))

    def download_object(self, object_name: str) -> bytes:
        client = self._get_client()
        bucket = client.bucket(self.bucket_name)
        blob = bucket.blob(object_name)
        return blob.download_as_bytes()
