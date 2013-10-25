Feature: Location upload

  Scenario: Upload locations
    Given I am logged in as admin
    And I have a country
    And I have location type and location details objects
    When I visit upload locations page
    Then I should see the text message
    And I should see name of the country for which details were added
    And I should see link for input file format
    When I click on the link for input file format
    Then I should see table of all location types
    And Type code should be in front of any type that has code
    When I click on the link for input file format
    Then Table should collapse

  Scenario: Upload locations- when no details object present
    Given I am logged in as admin
    And I have a country
    When I visit upload locations page
    Then I should see no hierarchy message
    And I should see the button to add hierarchy
    When I click on add hierarchy button
    And I should go to add hierarchy page
