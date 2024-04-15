from typing import Dict

from general_scripts.msal_azure_library.token_validator import DelegatedValidator


def test_delegated_validator():
    username = ""
    password = ""
    tenant_id = ""
    client_id = ""
    client_secret = ""
    scope = f"https://graph.microsoft.com/.default"
    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = DelegatedValidator()

    result = app(
        username=username,
        password=password,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        scope=[scope],
        authority=authority
    )

    assert isinstance(result, Dict)
