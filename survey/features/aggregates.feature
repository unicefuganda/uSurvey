Feature: Aggregates feature

    Scenario: Aggregates status page
      Given I am logged in as researcher
      And I have locations
      And I have 2 batches with one open
      And I visit aggregate status page
      Then I should see an option to select location hierarchically
      And I should see an option to select batch
      And I should see a get status button

    Scenario: Aggregates status page for open batch
      Given I am logged in as researcher
      And I have locations
      And I have 2 batches with one open
      And I have 2 investigators with households
      And I visit aggregate status page
      And I choose a location and an open batch
      And I change my mind to select all districts
      And I click get status button
      Then I should see number of households and clusters completed and pending
      And I should see a list of investigators with corresponding phone numbers and pending households
      And I should see all districts as location selected

    Scenario: Aggregates status page for closed batch
      Given I am logged in as researcher
      And I have locations
      And I have 2 batches with one open
      And I have 2 investigators with households
      And I visit aggregate status page
      And I choose a location and a closed batch
      And I click get status button
      Then I should see number of households and clusters completed and pending
      And I should see a list of investigators with corresponding phone numbers and pending households
      And I click get status button
      Then I should see number of households and clusters completed and pending
      And I should see a list of investigators with corresponding phone numbers and pending households

    Scenario: Download Excel
      Given I am logged in as researcher
      And I have few batches
      And I visit download excel page
      And I select a batch and click export to csv

    Scenario: Region/district completion rates
      Given I am logged in as researcher
      And I have locations
      And I have 2 batches with one open
      And I visit district aggregate page
      Then I should see an option to select location hierarchically
      And I should see an option to select batch
      And I should see a get status button

    Scenario: Survey completion rates - get with params
      Given I am logged in as researcher
      And I have locations
      And I have 2 batches with one open
      And I visit district aggregate page
      And I choose a location and an open batch
      And I click get status button
      Then I should see a table for completion rates
      And I should see descendants in the table
      When I click on descendant name
      Then I should see status page for that location

    Scenario: Survey completion for Lowest level location type
      Given I am logged in as researcher
      And I have locations
      And I have an investigator and households
      And I have 2 batches with one open
      And I visit district aggregate page
      And I choose a village and an open batch
      And I click get status button
      Then I should see a table for household completion rates
      And I should see household details text
      And I should see investigator details text
      And I should see percent completion

    Scenario: Survey Completion - Javascript
      Given I am logged in as researcher
      And I have 2 surveys with one batch each
      And I have locations
      And I have an investigator and households
      And I visit district aggregate page
      When I select survey 2 from survey list
      Then I should see batch2 in batch list
      And I should not see batch1 in batch list
      When I select survey 1 from survey list
      Then I should see batch1 in batch list
      And I should not see batch2 in batch list
