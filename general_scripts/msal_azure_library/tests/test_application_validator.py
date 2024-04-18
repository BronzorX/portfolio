from typing import Dict

from general_scripts.msal_azure_library.token_validator import ApplicationValidator


def test_application_validator():
    tenant_id = ""
    client_id = ""
    client_secret = ""
    domain_name = ""
    scope = f"https://{domain_name}.onmicrosoft.com/{client_id}/.default"
    proxy_name = ""
    authority = f"https://{domain_name}.b2clogin.com/{domain_name}.onmicrosoft.com/{proxy_name}"

    app = ApplicationValidator()

    result = app(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        authority=authority,
        scope=[scope]
    )

    assert isinstance(result, Dict)
