Feature: Group features

  Scenario: List Conditions Page
    Given I am logged in as researcher
    And I visit conditions listing page
    And I have 10 conditions
    And I should see the conditions list
    
  Scenario: List Groups Page
    Given I am logged in as researcher
    And I have a condition
    And I have 100 groups with that condition
    And I visit groups listing page
    Then I should see the groups list paginated