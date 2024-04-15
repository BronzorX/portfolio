import logging
import re
import types
from abc import abstractmethod
from typing import Any, List, Dict

import msal


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
                 ) -> Dict[str, str]:

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

        # Firstly, check the cache to see if this end user has signed in before
        accounts = app.get_accounts(username=username)
        if accounts:
            logging.info("Account(s) exists in cache, probably with token too. Let's try.")
            result = app.acquire_token_silent(scope, account=accounts[0], force_refresh=True)

        if not result:
            logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
            # See this page for constraints of Username Password Flow.
            # https://github.com/AzureAD/microsoft-authentication-library-for-python/wiki/Username-Password-Authentication
            result = app.acquire_token_by_username_password(
                username=username, password=password, scopes=scope)
        if result.get("error"):
            description = re.sub(pattern="\r\n|\n|\r", repl=" --- ", string=result.get("error_description"))
            raise types.new_class(name=result.get("error"), bases=(Exception,))(description)
        return result


class ApplicationValidator(TokenValidator):

    def __call__(self,
                 client_id: str,
                 tenant_id: str,
                 client_secret: str,
                 scope: List[str],
                 authority: str
                 ) -> Any:
        """
        Get the access token using the Client Credentials Flow (Application Flow).
        :return: A JSON object containing token information.
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


