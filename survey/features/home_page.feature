Feature: Homepage feature

  Scenario: Home page
    Given I am not logged in
    And And I am in the home page
    Then I should see the about text provided by panwar
