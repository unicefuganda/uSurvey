Feature: Location hierarchy

  Scenario: Add location hierarchy
    Given I am logged in as researcher
    And I visit add location hierarchy page
    Then I should see text message
    And I should see country dropdown
    And I should see level1 text field
    And I should see a plus icon
    When I click add-level icon
    Then I should see another level field
    And I should see another plus icon
    And I should see remove icon
    When I click remove level icon
    Then I should see only one level field
    And I should not see remove icon