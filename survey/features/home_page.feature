Feature: Homepage feature

    Scenario: Home page
        Given I am not logged in
        And I am in the home page
        Then I should see the completion map
