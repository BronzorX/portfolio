This library has the scope to interact with the new authentication provided by microsoft, using msal(Microsoft Authentication Library).

* Components implemented:
  * GraphConnector
    * Allows you to interact with the microsoft application via API. 
      At the moment it's possible to interact only with outlook mailboxes 
  
  * Token acquisition methods:
    * Application Validator: Get the access token using the Client Credentials Flow (Application Flow)
    * Delegaded Validator: Validates user credentials and retrieves an access token from the tenant via Client Application method.

  * Request handler:
    * Class that allows you to handle requests and response with some configurations

* Tests executed:
  * Application Validator
  * Delegaded Validator