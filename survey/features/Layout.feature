Feature: Layout Page feature

  Scenario: Groups Tab
    Given I am logged in as researcher
    And I visit the new group page
    When I click Groups tab
    Then I should see group dropdown list

  Scenario: Survey Tab
    Given I am logged in as admin
    And I click Survey tab
    Then I should see survey dropdown list

  Scenario: Questions Tab
    Given I am logged in as researcher
    And I click Questions tab
    Then I should see Questions dropdown list

  Scenario: Aggregates Tab
    Given I am logged in as researcher
    And I click Aggregates tab
    Then I should see Aggregates dropdown list

  Scenario: Downloads Tab
    Given I am logged in as researcher
    And I click Downloads Tab
    Then I should see Downloads dropdown list