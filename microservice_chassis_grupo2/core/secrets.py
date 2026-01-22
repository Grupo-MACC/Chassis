import base64
import boto3
from typing import Dict, Optional


class SecretsError(Exception):
    """Excepción base para errores de secretos"""
    pass


class SSMSecrets:
    def __init__(self, region: Optional[str] = None):
        self.client = boto3.client("ssm", region_name=region)

    def get_parameter(self, name: str, decrypt: bool = True) -> str:
        """
        Obtiene un parámetro individual de SSM
        """
        try:
            response = self.client.get_parameter(
                Name=name,
                WithDecryption=decrypt
            )
            return response["Parameter"]["Value"]
        except self.client.exceptions.ParameterNotFound:
            raise SecretsError(f"SSM parameter not found: {name}")
        except Exception as e:
            raise SecretsError(f"Error getting SSM parameter {name}: {e}")


class SecretsManager:
    def __init__(self, region: Optional[str] = None):
        self.client = boto3.client("secretsmanager", region_name=region)

    def get_secret(self, secret_id: str) -> str:
        """
        Obtiene un secreto de Secrets Manager
        """
        try:
            response = self.client.get_secret_value(
                SecretId=secret_id
            )

            if "SecretString" in response:
                return response["SecretString"]

            # Secret binario (poco común)
            return base64.b64decode(response["SecretBinary"]).decode("utf-8")

        except self.client.exceptions.ResourceNotFoundException:
            raise SecretsError(f"Secret not found: {secret_id}")
        except Exception as e:
            raise SecretsError(f"Error getting secret {secret_id}: {e}")

    def create_secret(self, name: str, secret_value: str, description: str = "", overwrite: bool = False) -> str:
        """
        Crea un nuevo secreto en Secrets Manager
        
        Args:
            name: Nombre del secreto
            secret_value: Valor del secreto (string o JSON)
            description: Descripción opcional del secreto
            overwrite: Si es True, sobrescribe el secreto si ya existe
        
        Returns:
            ARN del secreto creado o actualizado
        
        Raises:
            SecretsError: Si el secreto ya existe (y overwrite=False) o hay error al crearlo
        """
        try:
            response = self.client.create_secret(
                Name=name,
                SecretString=secret_value,
                Description=description
            )
            return response["ARN"]
        except self.client.exceptions.ResourceExistsException:
            if overwrite:
                return self.update_secret(name, secret_value)
            raise SecretsError(f"Secret already exists: {name}")
        except Exception as e:
            raise SecretsError(f"Error creating secret {name}: {e}")

    def update_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Actualiza el valor de un secreto existente
        
        Args:
            secret_id: Nombre o ARN del secreto
            secret_value: Nuevo valor del secreto
        
        Returns:
            ARN del secreto actualizado
        """
        try:
            response = self.client.put_secret_value(
                SecretId=secret_id,
                SecretString=secret_value
            )
            return response["ARN"]
        except self.client.exceptions.ResourceNotFoundException:
            raise SecretsError(f"Secret not found: {secret_id}")
        except Exception as e:
            raise SecretsError(f"Error updating secret {secret_id}: {e}")


class KMSService:
    def __init__(self, region: Optional[str] = None):
        self.client = boto3.client("kms", region_name=region)

    def decrypt(self, ciphertext_base64: str) -> str:
        """
        Descifra manualmente un ciphertext usando KMS.
        Útil si guardas datos cifrados fuera de SSM/Secrets Manager.
        """
        try:
            ciphertext = base64.b64decode(ciphertext_base64)

            response = self.client.decrypt(
                CiphertextBlob=ciphertext
            )

            return response["Plaintext"].decode("utf-8")

        except Exception as e:
            raise SecretsError(f"Error decrypting with KMS: {e}")