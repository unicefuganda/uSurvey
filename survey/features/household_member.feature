Feature: Household Member feature

    Scenario: Household Member new page
      Given I am logged in as researcher
      And I have locations
      And I have an investigator in that location
      And I have a household
      And I visit new household member page
      And I see all household member fields are present
      And I fill all member related fields
      And I submit the form
      Then I should see member successfully created message
