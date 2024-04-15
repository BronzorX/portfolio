from enum import Enum

QUERY_OPTIONS = ['count', 'expand', 'filter', 'format', 'orderby', 'search', 'select', 'skip', 'top']


class BaseURI(Enum):
    LOGIN_URI = 'https://login.microsoftonline.com/'
    GRAPH_URI = 'https://graph.microsoft.com/v1.0/'
    BATCH_URI = 'https://graph.microsoft.com/v1.0/$batch/'


class OperationURI(Enum):
    MESSAGES = 'messages'
    MAIL_FOLDERS = 'mailfolders'
    SEND_MAIL = 'sendMail'
    FORWARD = 'forward'
    MOVE = 'move'
    ATTACHMENTS = 'attachments'
    ME = 'me'
    BATCH = '$batch'
    VALUE = '$value'
    CREATE_FORWARD = 'createForward'
    SEND = 'send'
    USERS = "users"


class WKEmailNamesForResponse(Enum):
    IN_ARRIVO = 'Posta in arrivo'
    INVIATA = 'Posta inviata'
    ELIMINATA = 'Posta eliminata'
    INDESIDERATA = 'Posta indesiderata'
    ARCHIVIO = 'Archivio'
    NOTE = 'Note'
    BOZZE = 'Bozze'


class WKEmailNamesForRequest(Enum):
    ARCHIVE = 'archive'
    CLUTTER = 'clutter'
    CONFLICTS = 'conflicts'
    CONVERSATION_HISTORY = 'conversationhistory'
    DELETED_ITEMS = 'deleteditems'
    DRAFTS = 'drafts'
    INBOX = 'inbox'
    JUNK_EMAIL = 'junkemail'
    LOCAL_FAILURES = 'localfailures'
    MSG_FOLDER_ROOT = 'msgfolderroot'
    OUTBOX = 'outbox'
    RECOVERABLE_ITEMS_DELETIONS = 'recoverableitemsdeletions'
    SCHEDULED = 'scheduled'
    SEARCH_FOLDERS = 'searchfolders'
    SENT_ITEMS = 'sentitems'
    SERVER_FAILURES = 'serverfailures'
    SYNCISSUES = 'syncissues'


class ErrorsToHandle(Enum):
    ERROR_ITEM_NOT_FOUND = "ErrorItemNotFound"
