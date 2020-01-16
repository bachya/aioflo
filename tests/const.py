"""Define constants for use in tests."""
TEST_ACCOUNT_ID = "aabbccdd"
TEST_DEVICE_ID = "98765"
TEST_EMAIL_ADDRESS = "email@address.com"
TEST_FIRST_NAME = "Tom"
TEST_LAST_NAME = "Jones"
TEST_LOCATION_ID = "mmnnoopp"
TEST_PASSWORD = "password"
TEST_PHONE_NUMBER = "+1 123-456-7890"
TEST_TOKEN = "123abc"
TEST_USER_ID = "12345abcde"

RESPONSE_USER_INFO_BASE = {
    "id": TEST_USER_ID,
    "email": TEST_EMAIL_ADDRESS,
    "isActive": True,
    "firstName": TEST_FIRST_NAME,
    "lastName": TEST_LAST_NAME,
    "unitSystem": "imperial_us",
    "phoneMobile": TEST_PHONE_NUMBER,
    "locale": "en-US",
    "locations": [{"id": TEST_LOCATION_ID}],
    "alarmSettings": [],
    "locationRoles": [{"locationId": TEST_LOCATION_ID, "roles": ["owner"]}],
    "accountRole": {"accountId": TEST_ACCOUNT_ID, "roles": ["owner"]},
    "account": {"id": TEST_ACCOUNT_ID},
    "enabledFeatures": [],
}

RESPONSE_USER_INFO_EXPAND_ALARM_SETTINGS = {
    "id": TEST_USER_ID,
    "email": TEST_EMAIL_ADDRESS,
    "isActive": True,
    "firstName": TEST_FIRST_NAME,
    "lastName": TEST_LAST_NAME,
    "unitSystem": "imperial_us",
    "phoneMobile": TEST_PHONE_NUMBER,
    "locale": "en-US",
    "locations": [{"id": TEST_LOCATION_ID}],
    "alarmSettings": [
        {
            "deviceId": TEST_DEVICE_ID,
            "settings": [
                {"alarmId": 4, "systemMode": "home", "smsEnabled": False},
                {"alarmId": 5, "systemMode": "away", "smsEnabled": False},
                {"alarmId": 4, "systemMode": "away", "smsEnabled": False},
                {"alarmId": 4, "systemMode": "sleep", "smsEnabled": False},
                {"alarmId": 5, "systemMode": "home", "smsEnabled": False},
                {"alarmId": 5, "systemMode": "sleep", "smsEnabled": False},
            ],
            "floSenseLevel": 5,
            "smallDripSensitivity": 4,
        }
    ],
    "locationRoles": [{"locationId": TEST_LOCATION_ID, "roles": ["owner"]}],
    "accountRole": {"accountId": TEST_ACCOUNT_ID, "roles": ["owner"]},
    "account": {"id": TEST_ACCOUNT_ID},
    "enabledFeatures": [],
}

RESPONSE_USER_INFO_EXPAND_LOCATIONS = {
    "id": TEST_USER_ID,
    "email": TEST_EMAIL_ADDRESS,
    "isActive": True,
    "firstName": TEST_FIRST_NAME,
    "lastName": TEST_LAST_NAME,
    "unitSystem": "imperial_us",
    "phoneMobile": TEST_PHONE_NUMBER,
    "locale": "en-US",
    "locations": [
        {
            "id": TEST_LOCATION_ID,
            "users": [{"id": TEST_USER_ID}],
            "devices": [{"id": TEST_DEVICE_ID, "macAddress": "606405c11e10"}],
            "userRoles": [{"userId": TEST_USER_ID, "roles": ["owner"]}],
            "address": "123 Main Stree",
            "city": "Boston",
            "state": "MA",
            "country": "us",
            "postalCode": "12345",
            "timezone": "US/Easter",
            "gallonsPerDayGoal": 240,
            "occupants": 2,
            "stories": 2,
            "isProfileComplete": True,
            "nickname": "Home",
            "irrigationSchedule": {"isEnabled": False},
            "systemMode": {"target": "home"},
            "locationType": "sfh",
            "locationSize": "lte_4000_sq_ft",
            "waterShutoffKnown": "unsure",
            "indoorAmenities": [],
            "outdoorAmenities": [],
            "plumbingAppliances": ["exp_tank"],
            "notifications": {
                "pending": {
                    "infoCount": 0,
                    "warningCount": 1,
                    "criticalCount": 0,
                    "alarmCount": [{"id": 57, "severity": "warning", "count": 1}],
                }
            },
            "areas": {
                "default": [
                    {"id": "212cb17e-0251-4b09-8581-77a5742d8ca6", "name": "Attic"},
                    {"id": "3bd494f1-7008-42d2-939e-064eb47722b6", "name": "Basement"},
                    {"id": "8cbb1152-232d-4200-a4bd-713fd2d56ba0", "name": "Garage"},
                    {
                        "id": "208ad83e-6cde-4c1a-9984-58d97ea80d27",
                        "name": "Main Floor",
                    },
                    {"id": "cf796985-3360-4cbd-a0ca-2d3f69a11880", "name": "Upstairs"},
                ],
                "custom": [],
            },
            "account": {"id": "34a43bcd-989d-453b-84f1-71d7951b5b04"},
        }
    ],
    "alarmSettings": [],
    "locationRoles": [{"locationId": TEST_LOCATION_ID, "roles": ["owner"]}],
    "accountRole": {"accountId": TEST_ACCOUNT_ID, "roles": ["owner"]},
    "account": {"id": TEST_ACCOUNT_ID},
    "enabledFeatures": [],
}
