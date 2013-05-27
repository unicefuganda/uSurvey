Feature: Investigators feature

  Scenario: Create an investigator
    Given I am logged in as researcher
    And I visit new investigator page
    And I fill all necessary fields
    And I submit the form
    # Then I should see that the investigator is created