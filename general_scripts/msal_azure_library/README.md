This library has the scope to interact with the new authentication provided by microsoft, using msal(Microsoft Authentication Library).

* Components implemented:

  * Token acquisition methods:
    * Application Validator: Get the access token using the Client Credentials Flow (Application Flow)
    * Delegaded Validator: Validates user credentials and retrieves an access token from the tenant via Client Application method.

* Tests executed:
  * Application Validator
  * Delegaded Validator