import base64
import datetime
import os
import time
from email.message import Message
from typing import Dict, Any, List, Union

import magic

from general_scripts.msal_azure_library.constants import BaseURI, QUERY_OPTIONS, OperationURI, WKEmailNamesForRequest
from general_scripts.msal_azure_library.request_handler import RequestResponseHandler
from general_scripts.msal_azure_library.token_validator import TokenValidator, DelegatedValidator, decode_token

mime = magic.Magic(mime=True)
requester = RequestResponseHandler()


class GraphConnector:
    """
    This class allows you to interact with the Azure Graph.
    At the moment it's possible to interact only with outlook mailboxes
    """
    def __init__(self,
                 connection_params: Dict[str, Any] = None,
                 validator: TokenValidator = DelegatedValidator(),
                 ):
        """
        This function initializes the class with a validator and connection parameters
        Method that initialize the objects required for the connection
        :param validator: This is the class that will validate the token
        :type validator: TokenValidator
        :param connection_params: This is a dictionary that contains the mandatory parameters to get the token
        :type connection_params: Dict[str, str]
        """
        if connection_params is None:
            connection_params = {}
        self.validator = validator
        self.connection_params = connection_params
        self._access_token_info = self._get_access_token()
        self.request_obj = requester.init_request_object(uri=BaseURI.GRAPH_URI.value,
                                                         status_force_retry=[408, 504])

    def _get_access_token(self):
        return self.validator(**self.connection_params)

    def _check_token(func) -> Any:
        def _check_and_update_token(self, *args, **kwargs) -> Any:
            """
            Function that check if a token is expired and if so, renews it. The function is treated as a decorator,
            so it can be used in every other function to keep the token always up-to-date
            """
            access_token = self._access_token_info.get("access_token")

            payload_token = decode_token(jwt_token=access_token)

            time_expired_date = datetime.datetime.fromtimestamp(payload_token.get("exp"))

            # IF THE CURRENT DATE AND TIME EXCEED THE EXPIRATION DATE OF THE TOKEN, IT IS RENEWED
            if datetime.datetime.now() >= time_expired_date:
                self._access_token_info = self._get_access_token()

            return func(self, *args, **kwargs)

        return _check_and_update_token

    def concat_msal_filter(self, filters: Dict) -> str:
        """
        Function that chains multiple MS GRAPH filters to make them usable in its API calls
        :param filters: the dictionary storing all the filters to concat
        :return: a string that will be put inside the API call
        :rtype: str
        """
        keys_list = list(filters.keys())
        url = ''

        if any(key.lower() not in QUERY_OPTIONS for key in keys_list):
            return f'Only this fields are valid for query MSGraph {QUERY_OPTIONS}'
        else:
            elem = keys_list.pop(0)
            url += "?$" + elem + "=" + filters[elem]
            for elem in keys_list:
                url += "&" + elem + "=" + filters[elem]
        return url

    def _init_header_request(self, token: str) -> Dict[str, str]:
        return {'Authorization': 'Bearer ' + token}

    def create_email_url(self, email: str = None) -> str:
        """
        Function that create the email section for graph url
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        for other Application(like ConfidentialApplication), you need to specify the email on PATH
        """
        if not email:
            return OperationURI.ME.value
        else:
            return os.path.join(OperationURI.USERS.value, email)

    @_check_token
    def create_folder(self,
                      folder_name: str,
                      is_hidden: bool = False,
                      email: str = None,
                      timeout: int = 120) -> Dict[str, str]:
        """
        Function that create a new folder on the mailbox
        :param folder_name: The display name of the new folder.
        :param is_hidden: Indicates whether the new folder is hidden.
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        return: dict that represent the metadata from folder that has been created
        See documentation from this link to get more details:
        https://docs.microsoft.com/en-us/graph/api/user-post-mailfolders?view=graph-rest-1.0&tabs=http
        """

        email_url_formatted = self.create_email_url(email=email)

        response = self.request_obj.post(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                          email_url_formatted,
                                                          OperationURI.MAIL_FOLDERS.value),
                                         json={"displayName": folder_name,
                                               "isHidden": is_hidden},
                                         headers={
                                             'Authorization': 'Bearer ' + self._access_token_info.get("access_token")},
                                         timeout=timeout
                                         )

        return requester.handle_response_json(response=response)

    @_check_token
    def delete_folder(self,
                      folder_id: str,
                      email: str = None,
                      timeout: int = 120):

        """
        Function that delete a specific folder
        :param folder_id: the id of the folder
        :param timeout: request timeout
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :return empty response if request is correct, status code 204
        See documentation from this link to get more details:
        https://docs.microsoft.com/en-us/graph/api/mailfolder-delete?view=graph-rest-1.0&tabs=http
        """

        email_url_formatted = self.create_email_url(email=email)

        self.request_obj.delete(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                 email_url_formatted,
                                                 OperationURI.MAIL_FOLDERS.value,
                                                 folder_id),
                                timeout=timeout,
                                headers=self._init_header_request(
                                    token=self._access_token_info["access_token"]),
                                )

    @_check_token
    def get_mail_folder_list(self,
                             email: str = None,
                             filters: Dict = {},
                             timeout: int = 120) -> Dict:
        """
        It uses the access token to call the Microsoft Graph API and return a list of all the folder in the user's email.
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        :param filters: filter that you can apply to the request, see this link for details:
        https://docs.microsoft.com/en-us/graph/query-parameters
        :return: A list of all the folders in the inbox.
        """
        if not filters:
            filters = {'top': '200', 'select': 'id,displayName'}
        parsed_filters = self.concat_msal_filter(filters=filters)
        email_url_formatted = self.create_email_url(email=email)
        r = self.request_obj.get(  # Use token to call downstream service
            url=os.path.join(BaseURI.GRAPH_URI.value, email_url_formatted, OperationURI.MAIL_FOLDERS.value,
                             parsed_filters),
            headers=self._init_header_request(token=self._access_token_info["access_token"]),
            timeout=timeout)
        return requester.handle_response_json(response=r)

    @_check_token
    def get_id_from_folder_name(self,
                                folder_name: str,
                                email: str = None,
                                timeout: int = 120) -> str:
        """
        Function that returns the email folder's ID from its name
        :param folder_name: the folder name from which taking the ID
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        :return: the folder id
        """
        resp_list = self.get_mail_folder_list(email=email,
                                              timeout=timeout)
        for elem in resp_list['value']:
            if elem['displayName'] == folder_name:
                return elem['id']

    @_check_token
    def search_mail_metadata_by_string(self,
                                       text: str,
                                       email: str = None,
                                       timeout: int = 120) -> Dict:
        """
        It searches for a string in the user's mailbox and returns the results
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :param text: The text to search for
        :param timeout: request timeout
        :return: A list of emails that contain the text string.
        """
        email_url_formatted = self.create_email_url(email=email)
        parsed_filters = self.concat_msal_filter(filters={"search": text})
        url = os.path.join(BaseURI.GRAPH_URI.value,
                           email_url_formatted,
                           OperationURI.MESSAGES.value,
                           ) + parsed_filters
        r = self.request_obj.get(url=url,
                                 headers=self._init_header_request(token=self._access_token_info["access_token"]),
                                 timeout=timeout)

        return requester.handle_response_json(response=r)

    @_check_token
    def read_attachments_by_id(self,
                               email_id: str,
                               email: str = None,
                               timeout: int = 120) -> Dict:
        """
        Function that takes the attachments of an email based on its id
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :param email_id: the email id taken from its content
        :param timeout: request timeout
        :return: a dict with attachment name as a key and the bytes as a value
        :rtype: Dict
        """
        # THE API CALL IS MADE WITH A DEFAULT 999 LIST OF ELEMENTS RETURN, SO THE PAGING DOESN'T NEED TO BE HANDLED
        uri_filters = self.concat_msal_filter(filters={"top": "999"})
        email_url_formatted = self.create_email_url(email=email)
        r = self.request_obj.get(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                  email_url_formatted,
                                                  OperationURI.MESSAGES.value,
                                                  email_id,
                                                  OperationURI.ATTACHMENTS.value,
                                                  uri_filters),
                                 headers=self._init_header_request(token=self._access_token_info["access_token"]),
                                 timeout=timeout)

        return requester.handle_response_json(response=r)

    @_check_token
    def read_mail_metadata_by_id(self,
                                 email_id: str,
                                 timeout: int = 120,
                                 body_type: str = "text"
                                 ) -> Dict:
        """
        It uses the access token to call the Microsoft Graph API to get the email with the given ID.
        :param email_id: The ID of the mail you want to read
        :param timeout: request timeout
        :param body_type: the body type of the email you want to read, you can choice from "text" or "html"
        :return: The response object
        """
        headers = {"Prefer": f"outlook.body-content-type={body_type}"}
        headers.update(self._init_header_request(token=self._access_token_info["access_token"]))
        r = self.request_obj.get(url=os.path.join(BaseURI.GRAPH_URI.value, OperationURI.MESSAGES.value, email_id),
                                 timeout=timeout,
                                 headers=headers)
        return requester.handle_response_json(response=r)

    @_check_token
    def read_mail_mime_by_id(
            self,
            email_id: str,
            email: str = None,
            timeout: int = 120
    ) -> Union[str, bytes]:
        """
        It uses the access token to call the Microsoft Graph API to get the email Message with the given ID.
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        :param email_id: The ID of the mail you want to read
        :return: The Message object.
        """
        email_url_formatted = self.create_email_url(email=email)
        r = self.request_obj.get(
            url=os.path.join(BaseURI.GRAPH_URI.value, email_url_formatted,
                             OperationURI.MESSAGES.value, email_id, OperationURI.VALUE.value),
            headers=self._init_header_request(token=self._access_token_info["access_token"]),
            timeout=timeout
        )
        return requester.handle_response_content(response=r)

    @_check_token
    def read_entire_email_by_id(self,
                                email_id: str,
                                timeout: int = 120,
                                body_type: str = "text") -> Dict:
        """
        Function that returns the whole email as MS GRAPH does.
        :param email_id: the email's id
        :param timeout: request timeout
        :param body_type: the body type of the email you want to read, you can choice from "text" or "html"
        :return: a dict with as keys the names of the fields and as values the values of the fields from the API
        """
        # THE METADATA IS TAKEN AND THE FIELD HAS ATTACHMENTS IS CHECKED, IF IT IS FALSE NO API CALLS ARE MADE
        email_resp = self.read_mail_metadata_by_id(email_id=email_id,
                                                   timeout=timeout,
                                                   body_type=body_type)
        if email_resp.get("hasAttachments"):
            attachments_resp = self.read_attachments_by_id(email_id=email_id,
                                                           timeout=timeout)
            attachments = attachments_resp.get("value")
        else:
            attachments = []

        email_resp["attachments"] = attachments

        return email_resp

    @_check_token
    def get_mails_metadata_from_thread(self,
                                       conversation_id: str,
                                       filters: Dict = {},
                                       email: str = None,
                                       timeout: int = 120) -> List[Dict]:
        """
        Function that returns the mails' metadata from a thread of emails
        :param conversation_id: the id of the thread from which taking the mails
        :param filters: filter that you can apply to the request, see this link for details:
        :param email: email where you want to gain information. if None, default is "me" for DelegatedApplication
        https://docs.microsoft.com/en-us/graph/query-parameters
        :param timeout: request timeout
        :return: a list of the metadatas
        """
        base_search = {"filter": f"conversationId eq '{conversation_id}'"}
        base_search.update(filters)
        return self.get_mails_metadata_from_folder(filters=base_search,
                                                   email=email,
                                                   timeout=timeout)

    @_check_token
    def get_mails_metadata_from_folder(self,
                                       email: str = None,
                                       folder_id: str = None,
                                       filters: Dict = {},
                                       sleep_seconds_per_requests: int = None,
                                       timeout: int = 120) -> List[Dict]:
        """
        Function that returns all the mails' metadata from a mail folder. It loops through all the pages and takes the
        metadata using a link given by the API  to cycle the different pages
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication,
        :param folder_id: the folder from which taking the mails
        :param filters: filter that you can apply to the request, see this link for details:
        https://docs.microsoft.com/en-us/graph/query-parameters
        :param sleep_seconds_per_requests: a time sleep that can be set to spread the various API calls
        :param timeout: request timeout
        :return: the list of metadatas from the emails
        :rtype: list dict
        """
        if not filters:
            filters = {'select': 'id'}
        filter_uri = self.concat_msal_filter(filters)
        email_url_formatted = self.create_email_url(email=email)

        url = os.path.join(BaseURI.GRAPH_URI.value,
                           email_url_formatted,
                           OperationURI.MESSAGES.value,
                           filter_uri) if not folder_id else \
            os.path.join(BaseURI.GRAPH_URI.value,
                         email_url_formatted,
                         OperationURI.MAIL_FOLDERS.value,
                         folder_id,
                         OperationURI.MESSAGES.value,
                         filter_uri)

        responses = []

        while True:
            resp = self.request_obj.get(url=url,
                                        headers=self._init_header_request(
                                            token=self._access_token_info["access_token"]),
                                        timeout=timeout)

            resp = requester.handle_response_json(response=resp)

            responses.extend(resp.get("value"))

            url = resp.get('@odata.nextLink')
            if not url:
                return responses

            if sleep_seconds_per_requests:
                time.sleep(sleep_seconds_per_requests)

    @_check_token
    def send_mail(self,
                  subject: str,
                  body: Dict[str, str],
                  to_addresses: List[str],
                  cc_addresses: List[str] = [],
                  attachments: List[Dict] = [],
                  save_to_sent_item: bool = True,
                  email: str = None,
                  timeout: int = 120
                  ) -> Dict:
        """
        It sends an email to the address specified in the address parameter
        :param subject: The subject of the email
        :param body: The content of the email
            :param content_type, str
            :param content, str
        :param attachments: List[Dict] The attachments of the email
            :param file_name, str
            :param content, bytes
        :param timeout: request timeout
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param to_addresses: The email address of the recipient to
        :param cc_addresses: The email address of the recipient cc
        :return: Dict that represent the response
        """

        email_url_formatted = self.create_email_url(email=email)

        allegati = [
            {"@odata.type": "#microsoft.graph.fileAttachment",
             "name": attachment.get("file_name"),
             "contentType": mime.from_buffer(attachment.get("content")),
             "contentBytes": base64.b64encode(attachment.get("content")).decode()
             }
            for attachment in attachments
        ]

        email_msg = {'Message': {'Subject': subject,
                                 'Body': {'ContentType': body.get("content_type"), 'Content': body.get("content")},
                                 'ToRecipients': [{'EmailAddress': {'Address': single_address}} for single_address in
                                                  to_addresses],
                                 'ccRecipients': [{'EmailAddress': {'Address': single_address}} for single_address in
                                                  cc_addresses],

                                 'attachments': allegati
                                 },
                     'SaveToSentItems': save_to_sent_item}

        r = self.request_obj.post(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                   email_url_formatted,
                                                   OperationURI.SEND_MAIL.value),
                                  headers=self._init_header_request(token=self._access_token_info["access_token"]),
                                  json=email_msg,
                                  timeout=timeout)

        return r

    @_check_token
    def send_mail_mime(self,
                       email_msg: Message,
                       addressed_to: List[str] = None,
                       address_from: str = None,
                       content_type: str = "text/plain",
                       email: str = None,
                       timeout: int = 120
                       ):

        """
        It takes a email_message and send mail to the specified address.
        :param email_msg: the email message
        :param addressed_to: The list of receivers
        :param address_from: the sender of the email, default value is the username
        :param content_type: The content type of the data in body
        :param timeout: request timeout
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :return: The response object is being returned.
        """

        access_token = self._access_token_info["access_token"]

        headers = self._init_header_request(token=access_token)
        headers.update({"Content-Type": content_type})

        email_url_formatted = self.create_email_url(email=email)

        if address_from:
            email_msg["From"] = address_from
        if addressed_to:
            email_msg["To"] = ",".join(addressed_to)

        email_str = base64.encodebytes(email_msg.as_bytes()).decode()
        r = self.request_obj.post(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                   email_url_formatted,
                                                   OperationURI.SEND_MAIL.value),
                                  headers=headers,
                                  data=email_str,
                                  timeout=timeout)

        return r

    @_check_token
    def forward_mail(self,
                     mail_id: str,
                     to_addresses: List[str],
                     comment: str = "",
                     email: str = None,
                     timeout: int = 120) -> Dict:
        """
        It takes a mail_id, comment, address, and address_name as parameters, and then uses the access token to forward the
        mail to the specified address.
        :param mail_id: The ID of the mail you want to forward
        :param comment: The comment to be added to the forwarded mail
        :param address: The email address of the recipient
        :param address_name: The name of the person you're forwarding the email to
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        :return: The response object is being returned.
        """

        mail_forwarding_info = {
            "comment": comment,
            "toRecipients": [{'EmailAddress': {'Address': single_address}} for single_address in to_addresses]
        }

        email_url_formatted = self.create_email_url(email=email)

        r = self.request_obj.post(
            url=os.path.join(BaseURI.GRAPH_URI.value,
                             email_url_formatted,
                             OperationURI.MESSAGES.value,
                             mail_id,
                             OperationURI.FORWARD.value
                             ),
            headers=self._init_header_request(token=self._access_token_info["access_token"]),
            json=mail_forwarding_info,
            timeout=timeout)

        return requester.handle_response_json(response=r)

    @_check_token
    def move_email_by_id(self,
                         email_id: str,
                         folder_id: str,
                         email: str = None,
                         timeout: int = 120) -> Dict:

        """
        Function that moves a mail from a mail folder to another
        :param email_id: email id
        :param folder_id: folder id destination
        :param timeout: request timeout
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :return: email json format with new ID associated
        """

        email_url_formatted = self.create_email_url(email=email)

        url_move = os.path.join(BaseURI.GRAPH_URI.value,
                                email_url_formatted,
                                OperationURI.MESSAGES.value,
                                email_id,
                                OperationURI.MOVE.value)

        resp_move = self.request_obj.post(url=url_move,
                                          json={"destinationId": folder_id},
                                          headers=self._init_header_request(
                                              token=self._access_token_info["access_token"]),
                                          timeout=timeout)

        return requester.handle_response_json(response=resp_move)

    @_check_token
    def move_thread_by_id(self,
                          conversation_id: str,
                          folder_resource: str,
                          folder_destination: str,
                          email: str = None,
                          timeout: int = 120) -> str:

        """
        Function that moves a mail thread from a mail folder to another
        :param conversation_id: thread id
        :param folder_resource: folder id resource
        :param folder_destination: folder id destination
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        :return:
        """

        resp_ids = self.get_mails_metadata_from_folder(folder_id=folder_resource,
                                                       filters={"filter": f"conversationId eq '{conversation_id}'",
                                                                "select": "id"},
                                                       email=email,
                                                       timeout=timeout)

        for value_id in resp_ids:
            self.move_email_by_id(email_id=value_id.get("id"),
                                  email=email,
                                  folder_id=folder_destination,
                                  timeout=timeout)

        return "Done"

    @_check_token
    def delete_mail_by_id(self,
                          email_id: str,
                          email: str = None,
                          folder_id: str = WKEmailNamesForRequest.DELETED_ITEMS.value,
                          timeout: int = 120,
                          ):
        """
        Function that moves a mail from a mail folder to another
        :param email_id: email id
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param folder_id: folder_id or WellKnownName where you want to put the deleted email:
        NB: THIS IS A MOVE ACTION so is raccomended to choice of of the following values WK or their relative ids:
            - deleteditems -> moves the email in the trash folder
            - recoverableitemspurges -> moves the email in the section that allows you to recover the deleted email for a specific period of time
        :param timeout: request timeout
        :return:
        """
        resp = self.move_email_by_id(email_id=email_id,
                                     email=email,
                                     folder_id=folder_id,
                                     timeout=timeout)

        return resp

    @_check_token
    def delete_thread_by_conversation_id(self,
                                         conversation_id: str,
                                         folder_resource: str,
                                         email: str = None,
                                         timeout: int = 120
                                         ) -> str:
        """
        Function that moves a mail from a mail folder to another
        :param conversation_id: thread id
        :param folder_resource: folder id resource
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        :return:
        """
        resp = self.move_thread_by_id(conversation_id=conversation_id,
                                      folder_resource=folder_resource,
                                      folder_destination=WKEmailNamesForRequest.DELETED_ITEMS.value,
                                      email=email,
                                      timeout=timeout)

        return resp

    @_check_token
    def update_email_parameters(self,
                                email_id: str,
                                updates: Dict[str, Any],
                                email: str = None,
                                timeout: int = 120) -> Dict:

        """
        Function that updates an email medatada
        for supported parameters check documentation from this link:
        https://docs.microsoft.com/en-us/graph/api/message-update?view=graph-rest-1.0&tabs=http
        :param updates: Dict that represent the updates
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        :return:
        """

        email_url_formatted = self.create_email_url(email=email)

        resp = self.request_obj.patch(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                       email_url_formatted,
                                                       OperationURI.MESSAGES.value,
                                                       email_id),
                                      json=updates,
                                      headers=self._init_header_request(
                                          token=self._access_token_info["access_token"]),
                                      timeout=timeout
                                      )

        return requester.handle_response_json(response=resp)

    @_check_token
    def add_attachment(self,
                       email_id: str,
                       attach_name: str,
                       attach_content: str,
                       email: str = None,
                       timeout: int = 120) -> Dict:
        """
        This function adds an attachment to a specified email message using the Microsoft Graph API.
        :param email_id: The ID of the email message to which the attachment will be added
        :type email_id: str
        :param attach_name: The name of the attachment that will be added to the email
        :type attach_name: str
        :param attach_content: The "attach" parameter is a str that represents the content of the attachment to be added to
        an email message converted to base64 string
        :type attach_content: str
        :param timeout: The timeout parameter is an optional integer value that specifies the maximum number of seconds to
        wait for a response from the server before raising a timeout exception. The default value is 120 seconds, defaults
        to 120
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :type timeout: int (optional)
        :return: a dictionary containing the response from the API call made to add an attachment to an email message. The
        dictionary may contain information such as the attachment ID, name, and content type.
        for documentation check this link:
        https://learn.microsoft.com/en-us/graph/api/post-post-attachments?view=graph-rest-1.0&tabs=http
        """

        email_url_formatted = self.create_email_url(email=email)

        dict_attachment = {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": attach_name,
            "contentBytes": attach_content
        }
        url = os.path.join(BaseURI.GRAPH_URI.value,
                           email_url_formatted,
                           OperationURI.MESSAGES.value,
                           email_id,
                           "attachments")

        resp = self.request_obj.post(url=url,
                                     json=dict_attachment,
                                     headers=self._init_header_request(
                                         token=self._access_token_info["access_token"]),
                                     timeout=timeout)

        return requester.handle_response_json(response=resp)

    @_check_token
    def draft_and_forward(self,
                          email_id: str,
                          to_addresses: List[str],
                          cc_addresses: List[str] = [],
                          subject_changes: str = None,
                          body_changes: str = None,
                          attachments_to_add: List[Dict[str, str]] = [],
                          email: str = None,
                          timeout: int = 120) -> Dict:
        """
        Function that creates a draft from an existing mail, update the mail and send the mail all at once.
        Required params are the email id and a list of addresses
        :param email_id: The id of the mail already in the box
        :param to_addresses: List of recipients of the new mail forward
        :param cc_addresses: List of cc of the the new mail forward
        :param subject_changes: String that will become the new mail subject
        :param body_changes:Text that will become the new mail body
        :param attachments_to_add: List of attachments to add to the draft, contain {"name":"<filename.ext>", "content": "base64str"}
        :param email: email where you want to gain information, if None, default is "me" for DelegatedApplication
        :param timeout: request timeout
        """
        updates = {"toRecipients": [{'EmailAddress': {'Address': single_address}} for single_address in to_addresses],
                   "ccRecipients": [{'EmailAddress': {'Address': single_address}} for single_address in cc_addresses]}
        if subject_changes:
            updates['subject'] = subject_changes
        if body_changes:
            updates['body'] = {'ContentType': "Text", 'Content': body_changes},

        email_url_formatted = self.create_email_url(email=email)

        resp_create_forward = self.request_obj.post(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                                     email_url_formatted,
                                                                     OperationURI.MESSAGES.value,
                                                                     email_id,
                                                                     OperationURI.CREATE_FORWARD.value),
                                                    headers=self._init_header_request(
                                                        token=self._access_token_info["access_token"]),
                                                    timeout=timeout)

        id_draft = requester.handle_response_json(response=resp_create_forward).get('id')

        if attachments_to_add:
            for attachment in attachments_to_add:
                self.add_attachment(email_id=id_draft,
                                    timeout=timeout,
                                    attach_name=attachment.get("name"),
                                    attach_content=attachment.get("content"))

        resp = self.request_obj.patch(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                       email_url_formatted,
                                                       OperationURI.MESSAGES.value,
                                                       id_draft),
                                      json=updates,
                                      headers=self._init_header_request(
                                          token=self._access_token_info["access_token"]),
                                      timeout=timeout
                                      )
        id_send = requester.handle_response_json(response=resp).get('id')
        resp = self.request_obj.post(url=os.path.join(BaseURI.GRAPH_URI.value,
                                                      email_url_formatted,
                                                      OperationURI.MESSAGES.value,
                                                      id_send,
                                                      OperationURI.SEND.value
                                                      ),
                                     headers=self._init_header_request(token=self._access_token_info["access_token"]),
                                     timeout=timeout)
        return resp
