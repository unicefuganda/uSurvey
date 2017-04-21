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

    Scenario: Household member edit page
        Given I am logged in as researcher
        And I have locations
        And I have an investigator in that location
        And I have a household
        And also I have a household member
        And I visit edit household member page
        And I see all details of household member are present
        And I edit member related fields
        And I submit the form
        Then I should see member successfully edited message

    Scenario: Delete Household Member
        Given I am logged in as researcher
        And I have locations
        And I have an investigator in that location
        And I have a household
        And also I have a household member
        And I visit that household details page
        And I click delete member
        Then I should see a confirmation modal
        And if I click yes
        Then that member is successfully deleted
