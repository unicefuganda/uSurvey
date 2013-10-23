Feature: Location upload

  Scenario: Upload locations
    Given I am logged in as researcher
    And I have a country
    And I have location type and location details objects
    When I visit upload locations page
    Then I should see the text message
    And I should see name of the country for which details were added
    And I should see link for input file format
