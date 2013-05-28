Feature: Investigators feature

  Scenario: Create an investigator
    Given I am logged in as researcher
    And I visit new investigator page
    And I fill all necessary fields
    And I submit the form
    Then I should see that the investigator is created

  Scenario: List investigators
    Given I have 100 investigators
    And I visit investigators listing page
    And I should see the investigators list paginated