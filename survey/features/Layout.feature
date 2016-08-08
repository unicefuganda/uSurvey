Feature: Layout Page feature
  Scenario: Survey Administration Tab
    Given I am logged in as researcher
    And I click Survey Administration tab
    Then I should see survey administration dropdown list

  Scenario: Downloads Tab
    Given I am logged in as researcher
    And I click Downloads tab
    Then I should see downloads dropdown list

  Scenario: Analysis Tab
    Given I am logged in as researcher
    And I click Analysis tab
    Then I should see analysis dropdown list

  Scenario: Settings Tab
    Given I am logged in as admin
    And I click Settings tab
    Then I should see Settings dropdown list
