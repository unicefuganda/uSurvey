Feature: Aggregates feature

    Scenario: Download Excel
      Given I am logged in as researcher
      And I have three surveys
      And I have general member group
      And I have batches in those surveys
      And I visit download excel page
      When I select one of the two surveys
      Then I should only see the batches in that survey
      When I choose a batch in that survey
      Then I should be able to export the responses for that batch

    Scenario: Region/district completion rates
      Given I am logged in as researcher
      And I have three surveys
      And I have locations
      And I have 2 batches with one open
      And I visit district aggregate page
      Then I should see an option to select location hierarchically
      And I should see an option to select batch
      And I should see a get status button

    Scenario: Region/district completion rates -- pagination
      Given I am logged in as researcher
      And I have three surveys
      And I have 100 locations
      And I have one batch open in those locations
      And I visit district aggregate page
      And I click get status button
      Then I should see district completion table paginated

    Scenario: Survey completion rates - with filter data
      Given I am logged in as researcher
      And I have three surveys
      And I have locations
      And I have 2 batches with one open
      And I visit district aggregate page
      And I choose a location and an open batch
      And I click get status button
      Then I should see a table for completion rates
      And I should see title message
      And I should see descendants in the table

    Scenario: Survey completion for Lowest level location type
      Given I am logged in as researcher
      And I have three surveys
      And I have locations
      And I have eas in the lowest location
      And I have an investigator and households
      And I have 2 batches with one open
      And one household has completed that open batch
      And I visit district aggregate page
      And I choose ea and an open batch
      And I click get status button
      Then I should see a table for household completion rates
      And I should see household details text
      And I should see investigator details text
      And I should see percent completion

    Scenario: Survey Completion - Javascript
       Given I am logged in as researcher
        And I have locations
        And I have three surveys
        And I have eas in the lowest location
        And I have an investigator and households
        And I have 2 batches with one open
        And I visit district aggregate page
        When I select survey 2 from survey list
        Then I should see batch2 in batch list
        And I should not see batch1 in batch list
        When I select survey 1 from survey list
        Then I should see batch1 in batch list
        And I should not see batch2 in batch list

    Scenario: Download Investigators Report - GET
       Given I am logged in as researcher
       And I have locations
       And I have three surveys
       And I have 2 surveys with one batch each
       When I visit investigator report page
       Then I should see title-text message
       When I select one of the survey
       Then I should batches in that survey
       When I select a batch
       And I click generate report button