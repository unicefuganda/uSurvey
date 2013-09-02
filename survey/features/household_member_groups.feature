Feature: Group features

  Scenario: List Conditions Page
    Given I am logged in as researcher
    And I visit conditions listing page
    And I have 10 conditions
    And I should see the conditions list
    When I click the add button
    Then I should see the new condition form
    
  Scenario: List Groups Page
    Given I am logged in as researcher
    And I have a condition
    And I have 100 groups with that condition
    And I visit groups listing page
    Then I should see the groups list paginated

  Scenario: Add a group condition
    Given I am logged in as researcher
    And I visit the new condition page
    When I fill in the condition details
    And I click save button
    Then I should see that the condition was saved successfully

  Scenario: Add a group
    Given I am logged in as researcher
    And I have a condition
    And I visit the new group page
    When I fill in the group details
    And I click save button
    Then I should see that the group was saved successfully