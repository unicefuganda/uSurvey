Feature: Simple indicator results

    Background:
        Given I am logged in as researcher
        And I have a survey
        And I have three batches
        And I have two modules

    Scenario: Simple Indicator - Transition from List to analysis
        And I have regions and districts
        And I have investigators in those districts
        And I have households in in those districts
        And I have a multichoice  question
        And I have an indicator in that survey
        And I have responses for that question
        Given I am on the indicator listing page
        And I click the analysis link of the indicator
        Then I should see indicator result page
        And I should see indicator graph for the country
        And I should see indicator data table for the country