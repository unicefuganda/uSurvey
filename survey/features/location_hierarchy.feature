Feature: Location hierarchy

  Scenario: Add location hierarchy
    Given I am logged in as researcher
    And I have a country
    And I visit add location hierarchy page
    Then I should see text message
    And I should see country dropdown
    And I should see country present in dropdown
    And I should see a row for level details field
    And I should see a link to add another row
    And I should see a link to remove a row
    When I click add row link
    Then I should see anther row for levels details field
    When I click remove row link
    Then I should see row for levels details field removed
