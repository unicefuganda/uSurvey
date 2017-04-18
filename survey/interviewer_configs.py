LEVEL_OF_EDUCATION = (("Did not attend school", "Did not attend school"),
                      ("Nursery", "Nursery"),
                      ("Primary", "Primary"),
                      ("'O' Level", "'O' Level"),
                      ("'A' Level", "'A' Level"),
                      ("Tertiary", "Tertiary"),
                      ("University", "University"),)

LANGUAGES = (("English", "English"),
             ("Luganda", "Luganda"),
             ("Runyankore-Rukiga", "Runyankore-Rukiga"),
             ("Runyoro-Rutoro", "Runyoro-Rutoro"),
             ("Swahili", "Swahili"),
             ("Ateso-Karimojong", "Ateso-Karimojong"),
             ("Luo", "Luo"),
             ("Lugbara", "Lugbara"),)

MONTHS = ((1, 'January'),
          (2, 'February'),
          (3, 'March'),
          (4, 'April'),
          (5, 'May'),
          (6, 'June'),
          (7, 'July'),
          (8, 'August'),
          (9, 'September'),
          (10, 'October'),
          (11, 'November'),
          (12, 'December'),)


OCCUPATION = (("Agricultural labor", "Agricultural labor"),
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
              ("Other: ", "Other"),)


USSD_PROVIDER = "YO"
NUMBER_OF_HOUSEHOLD_PER_INTERVIEWER = 10
PRIME_LOCATION_TYPE = 'District'
HAS_APPLICATION_CODE = True
APPLICATION_CODE = '10'
# all upload error logs older than this (in days) will be automatically cleared
UPLOAD_ERROR_LOG_EXPIRY = 30
INTERVIEWER_MIN_AGE = 18
INTERVIEWER_MAX_AGE = 60
