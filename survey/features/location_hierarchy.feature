Feature: Location hierarchy

  Scenario: Add location hierarchy
    Given I am logged in as researcher
    And I visit add location hierarchy page
    Then I should see text message
    And I should see country dropdown