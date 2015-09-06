LEVEL_OF_EDUCATION = (  ("Did not attend school", "Did not attend school"),
                        ("Nursery", "Nursery"),
                        ("Primary", "Primary"),
                        ("'O' Level", "'O' Level"),
                        ("'A' Level", "'A' Level"),
                        ("Tertiary", "Tertiary"),
                        ("University", "University"),
                    )

LANGUAGES = (   ("English", "English"),
                ("Luganda", "Luganda"),
                ("Runyankore-Rukiga", "Runyankore-Rukiga"),
                ("Runyoro-Rutoro", "Runyoro-Rutoro"),
                ("Swahili", "Swahili"),
                ("Ateso-Karimojong", "Ateso-Karimojong"),
                ("Luo", "Luo"),
                ("Lugbara", "Lugbara"),
            )
MONTHS =( (1, 'January'),
                (2, 'February'),
                (3, 'March'),
                (4, 'April'),
                (5, 'May'),
                (6, 'June'),
                (7, 'July'),
                (8, 'August'),
                (9, 'September'),
                (10,'October'),
                (11,'November'),
                (12,'December'),
              )
OCCUPATION = (
                ("Agricultural labor", "Agricultural labor"),
                ("Livestock herding", "Livestock herding"),
                ("Own farm labor", "Own farm labor"),
                ("Employed(salaried)", "Employed(salaried)"),
                ("Waged labor (Casual)", "Waged labor (Casual)"),
                ("Petty trade", "Petty trade"),
                ("Unemployed", "Unemployed"),
                ("Student", "Student"),
                ("Business person", "Business person"),
                ("Retired pensioner", "Retired pensioner"),
                ("Retired (no pension)", "Retired (no pension)"),
                ("Housewife", "Housewife"),
                ("Domestic help", "Domestic help"),
                ("Hunting, gathering", "Hunting, gathering"),
                ("Firewood/charcoal", "Firewood/charcoal"),
                ("Brewing", "Brewing"),
                ("Weaving/basketry", "Weaving/basketry"),
                ("Fishing", "Fishing"),
                ("Other: ", "Other"),
                )

MESSAGES = {
    'UNKNOWN_RESPONSE' : "Pls enter a valid reply",
    'SUCCESS_MESSAGE': "This survey has come to an end. Your responses have been received. Thank you.",
    'BATCH_5_MIN_TIMEDOUT_MESSAGE': "This batch is already completed and 5 minutes have passed. You may no longer retake it.",
    'USER_NOT_REGISTERED': "Sorry, your mobile number is not registered for any surveys.",
    'START': "Welcome {{interviewer}} to the survey. Current Survey is: {{survey}}\n1: Register households\n",
    'START_SURVEY': '2: Start Survey\n',
    'HOUSEHOLD_LIST': "Please enter household from the list or enter the sequence number",
    'MEMBERS_LIST': "Please select a member from the list",
    'SUCCESS_MESSAGE_FOR_COMPLETING_ALL_HOUSEHOLDS': "Survey Completed. Thank you.",
    'RETAKE_SURVEY': "You have already completed this household. Would you like to start again?\n1: Yes\n2: No",
    'NO_HOUSEHOLDS': "Sorry, you have no households registered.",
    'NO_OPEN_BATCH': "Sorry, currently there are no open surveys in your Enumeration Area.",
    'HOUSEHOLDS_COUNT_QUESTION': "How many households have you listed in your Enumeration Area?",
    'HOUSEHOLD_SELECTION_SMS_MESSAGE': "Thank you. You will receive the household numbers selected for your Enumeration Area",
    'HOUSEHOLD_CONFIRMATION_MESSAGE': "Thank you. Houselist for Enumeration Area is available for member registration.",
    'HOUSEHOLDS_COUNT_QUESTION_WITH_VALIDATION_MESSAGE': "Count must be greater than %s. How many households have you listed in your Enumeration Area?", #% NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER,
    'MEMBER_SUCCESS_MESSAGE': "Thank you. Would you like to proceed to the next Household Member?\n1: Yes\n2: No",
    'HOUSEHOLD_COMPLETION_MESSAGE': "Thank you. You have completed this household. Would you like to retake this household?\n1: Yes\n2: No",
    'RESUME_MESSAGE': "Would you like to to resume with member question?\n1: Yes\n2: No",
    'SELECT_HEAD_OR_MEMBER': 'Household {{household}}, please select household member to register:\n1: Respondent\n2: Member',
    'END_REGISTRATION': 'Thank you for registering household member. Would you like to register another member?\n1: Yes\n2: No',
    'INTERVIEWER_BLOCKED_MESSAGE': 'Sorry. You are not registered for any surveys.',
    'HEAD_REGISTERED': "Head already registered for this household. Registering members now:\n",
    'NON_RESPONSE_MENU': "\n3: Report non-response",
    'NON_RESPONSE_COMPLETION': "Thank you. You have completed reporting non-responses. Would you like to start again?\n1: Yes\n2: No",
    'NON_RESPONSE_MSG' : 'Enter reason for non response'
}

COUNTRY_PHONE_CODE = "256"
USSD_PROVIDER = "YO"
NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER = 10
PRIME_LOCATION_TYPE = 'District'
HAS_APPLICATION_CODE = True
APPLICATION_CODE = '10'
UPLOAD_ERROR_LOG_EXPIRY = 30 # all upload error logs older than this (in days) will be automatically cleared
INTERVIEWER_MIN_AGE = 18
INTERVIEWER_MAX_AGE = 60
