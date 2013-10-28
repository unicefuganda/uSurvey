Feature: Indicators feature

    Scenario: Add indicators
      Given I am logged in as researcher
      And I have a survey
      And I have a batch
      And I have two question modules
      And I visit new indicator page
      And I visit new indicator page
      And I fill in the indicator details
      And I submit the form
      Then I should see that the indicator was successfully added