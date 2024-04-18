import logging
import re
import types
from abc import abstractmethod
from typing import Any, List, Dict, Union

import jwt
import msal


def decode_token(jwt_token: str) -> Dict:
    """
    Decode a JWT token to extract the payload.
    This function decodes a given JWT token using a specified secret to retrieve the payload.

    Args:
        jwt_token (str): The JWT token to decode.
    Returns:
        Dict: A dictionary containing the decoded payload of the JWT token.
    """

    token_header = jwt.get_unverified_header(jwt_token)
    payload_token = jwt.decode(jwt_token,
                               "secret",
                               algorithms=[token_header.get("alg")],
                               options={"verify_signature": False})
    return payload_token


class TokenValidator:

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Any:
        raise Exception("Not implemented")


class DelegatedValidator(TokenValidator):
    """
    A class for acquiring tokens using Microsoft Authentication Library (MSAL).
    This class provides method to acquire an access token from delegated applications.
    """

    def __call__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 tenant_id: str,
                 client_secret: str,
                 scope: List[str],
                 authority: str,
                 ) -> Dict[str, Union[str, int]]:

        """
        Validates user credentials and retrieves an access token from the tenant.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.
            client_id (str): The client ID of the application.
            tenant_id (str): The tenant ID of the Azure AD.
            client_secret (str): The client secret of the application.
            scope (List[str]): The list of scopes for the access token.
            authority (str): The authority URL for the authentication.

        Returns:
            Dict[str, str]: A JSON object containing token information.

        Raises:
            Exception: If an error occurs during the token acquisition process.
        """

        app = msal.ClientApplication(
            client_id=client_id,
            authority=authority,
            client_credential=client_secret
        )

        result = {}

        accounts = app.get_accounts(username=username)
        if accounts:
            logging.info("Account(s) exists in cache, probably with token too. Let's try.")
            result = app.acquire_token_silent(scope, account=accounts[0], force_refresh=True)

        if not result:
            logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
            result = app.acquire_token_by_username_password(
                username=username, password=password, scopes=scope)
        if result.get("error"):
            description = re.sub(pattern="\r\n|\n|\r", repl=" --- ", string=result.get("error_description"))
            raise types.new_class(name=result.get("error"), bases=(Exception,))(description)
        return result


class ApplicationValidator(TokenValidator):
    """
    A class for validating tokens using the Client Credentials Flow (Application Flow) with MSAL.
    This class provides methods to acquire an access token from a tenant using the client credentials of the application.

    """

    def __call__(self,
                 client_id: str,
                 tenant_id: str,
                 client_secret: str,
                 scope: List[str],
                 authority: str
                 ) -> Dict[str, Union[str, int]]:
        """
        Retrieves an access token from the tenant using the Client Credentials Flow.

        Args:
            client_id (str): The client ID of the application.
            tenant_id (str): The tenant ID of the Azure AD.
            client_secret (str): The client secret of the application.
            scope (List[str]): The list of scopes for the access token.
            authority (str): The authority URL for the authentication.

        Returns:
            Any: A JSON object containing token information.

        Raises:
            Exception: If an error occurs during the token acquisition process.
        """

        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )

        result = app.acquire_token_for_client(scopes=scope)

        if result.get("error"):
            description = re.sub(pattern="\r\n|\n|\r", repl=" --- ", string=result.get("error_description"))
            raise types.new_class(name=result.get("error"), bases=(Exception,))(description)

        return result
