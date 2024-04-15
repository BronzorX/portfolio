from typing import List, Dict

import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from general_scripts.msal_azure_library.constants import ErrorsToHandle
from general_scripts.msal_azure_library.exceptions import ErrorItemNotFound


class RequestResponseHandler:
    """
    A class for handling HTTP request and response operations.

    This class provides methods to initialize a request session with retries and handle HTTP response objects.

    Methods:
        init_request_object: Initializes a request session with retry settings.
        handle_response_json: Handles the HTTP response and returns the JSON content.
        handle_response_content: Handles the HTTP response and returns the content as bytes.

    """

    def __init_request_object(self,
                              uri: str,
                              retries: int = 3,
                              status_force_retry: List[int] = None,
                              backoff_factor: int = 10
                              ) -> requests.Session:
        if status_force_retry is None:
            status_force_retry = [408, 504, 429]
        retry_obj = Retry(status_forcelist=status_force_retry,
                          raise_on_status=True,
                          backoff_factor=backoff_factor,
                          total=retries)
        session = requests.Session()
        session.mount(prefix=uri, adapter=HTTPAdapter(max_retries=retry_obj))
        return session

    def init_request_object(self,
                            uri: str,
                            retries: int = 3,
                            status_force_retry: List[int] = None,
                            backoff_factor: int = 10
                            ) -> requests.Session:
        """
        Initializes a request session.

        Args:
            uri (str): The base URI for the HTTP requests.
            retries (int, optional): The number of retries for failed requests (default is 3).
            status_force_retry (List[int], optional): List of HTTP status codes that force a retry (default is [408, 504]).
            backoff_factor (int, optional): The backoff factor between retries (default is 10).

        Returns:
            requests.Session: A session object configured with retry settings.

        """
        if status_force_retry is None:
            status_force_retry = [408, 504]
        return self.__init_request_object(uri=uri,
                                          retries=retries,
                                          status_force_retry=status_force_retry,
                                          backoff_factor=backoff_factor)

    def handle_response_json(self,
                             response: Response
                             ) -> Dict:
        """
        Handles the HTTP response and returns the JSON content.

        Args:
            response (Response): The HTTP response object.

        Returns:
            Dict: The JSON content of the response.

        Raises:
            requests.HTTPError: If the response status code indicates an error.
        """

        json_error = response.json().get("error", {})
        error_code = json_error.get("code", "")
        if error_code == ErrorsToHandle.ERROR_ITEM_NOT_FOUND.value:
            raise ErrorItemNotFound()
        response.raise_for_status()
        return response.json()

    def handle_response_content(self, response: Response) -> bytes:
        """
        Handles the HTTP response and returns the content as bytes.

        Args:
            response (Response): The HTTP response object.

        Returns:
            bytes: The content of the response as bytes.

        Raises:
            requests.HTTPError: If the response status code indicates an error.

        """
        response.raise_for_status()
        return response.content
