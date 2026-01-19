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

    def get_parameters_by_path(
        self,
        path: str,
        recursive: bool = True,
        decrypt: bool = True
    ) -> Dict[str, str]:
        """
        Obtiene todos los parámetros bajo un path
        Devuelve un dict {nombre_parametro: valor}
        """
        parameters = {}
        next_token = None

        try:
            while True:
                kwargs = {
                    "Path": path,
                    "Recursive": recursive,
                    "WithDecryption": decrypt,
                }
                if next_token:
                    kwargs["NextToken"] = next_token

                response = self.client.get_parameters_by_path(**kwargs)

                for param in response["Parameters"]:
                    key = param["Name"].split("/")[-1]
                    parameters[key] = param["Value"]

                next_token = response.get("NextToken")
                if not next_token:
                    break

            return parameters

        except Exception as e:
            raise SecretsError(f"Error getting SSM parameters by path {path}: {e}")


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