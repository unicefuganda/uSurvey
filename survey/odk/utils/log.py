import logging, os
from datetime import datetime

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(APP_DIR, 'mics_odk.log') 
logger = logging.getLogger('audit_logger')
handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Enum(object):
    __name__= "Enum"
    def __init__(self, **enums):
        self.enums = enums

    def __getattr__(self, item):
        return self.enums[item]

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __iter__(self):
        return self.enums.itervalues()

Actions = Enum(
    PROFILE_ACCESSED="profile-accessed",
    PUBLIC_PROFILE_ACCESSED="public-profile-accessed",
    PROFILE_SETTINGS_UPDATED="profile-settings-updated",
    USER_LOGIN="user-login",
    USER_LOGOUT="user-logout",
    USER_BULK_SUBMISSION="bulk-submissions-made",
    USER_FORMLIST_REQUESTED="formlist-requested",
    FORM_ACCESSED="form-accessed",
    FORM_PUBLISHED="form-published",
    FORM_UPDATED="form-updated",
    FORM_XLS_DOWNLOADED="form-xls-downloaded",
    FORM_XLS_UPDATED="form-xls-updated",
    FORM_DELETED="form-deleted",
    FORM_CLONED="form-cloned",
    FORM_XML_DOWNLOADED="form-xml-downloaded",
    FORM_JSON_DOWNLOADED="form-json-downloaded",
    FORM_PERMISSIONS_UPDATED="form-permissions-updated",
    FORM_ENTER_DATA_REQUESTED="form-enter-data-requested",
    FORM_MAP_VIEWED="form-map-viewed",
    FORM_DATA_VIEWED="form-data-viewed",
    EXPORT_CREATED="export-created",
    EXPORT_DOWNLOADED="export-downloaded",
    EXPORT_DELETED="export-deleted",
    EXPORT_LIST_REQUESTED="export-list-requested",
    SUBMISSION_CREATED="submission-created",
    SUBMISSION_UPDATED="submission-updated",
    SUBMISSION_DELETED="submission-deleted",
    SUBMISSION_ACCESSED="submission-accessed",
    SUBMISSION_EDIT_REQUESTED="submission-edit-requested",
    SUBMISSION_REQUESTED="submission-requested",
    BAMBOO_LINK_CREATED="bamboo-link-created",
    BAMBOO_LINK_DELETED="bamboo-link-deleted",
    SMS_SUPPORT_ACTIVATED="sms-support-activated",
    SMS_SUPPORT_DEACTIVATED="sms-support-deactivated",
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def audit_log(action, request_user, investigator, message, audit, request, level=logging.DEBUG):
    """
    Create a log message based on these params

    @param action: Action performed e.g. form-deleted
    @param request_username: User performing the action
    @param account_username: The formhub account the action was performed on
    @param message: The message to be displayed on the log
    @param level: log level
    @param audit: a dict of key/values of other info pertaining to the action e.g. form's id_string, submission uuid
    @return: None
    """
    extra = {
        'formhub_action': action,
        'request_username': str(request_user),
        'account_username': investigator.name if investigator.name
            else str(investigator),
        'client_ip': get_client_ip(request),
        'audit': audit
    }
    logger.log(level, message, extra=extra)
