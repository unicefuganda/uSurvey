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
    
  Scenario: Create a condition on the group form
    Given I am logged in as researcher
    And I visit the new group page
    When I click the add new condition
    Then I should see the modal open
    When I fill in the condition details
    And I click the save button
    Then I should see the condition was saved successfully
    And I should see the new condition in the groups form

  Scenario: Create a condition with invalid form on the group form 
    Given I am logged in as researcher
    And I visit the new group page
    When I click the add new condition
    Then I should see the modal open
    And I click the save button
    Then I should see the form errors of required fields
    
  Scenario: Create a group with multiple conditions
    Given I am logged in as researcher
    And I have 2 conditions
    And I visit the new group page
    When I fill name and order
    And I select conditions
    And I click save button
    Then I should see that the group was saved successfully
    
  Scenario: List group details
    Given I am logged in as researcher
    And I have a groups
    And I have 2 conditions
    And I visit groups listing page
    And I click the actions button
    And I click view conditions link
    Then I should see a list of conditions
