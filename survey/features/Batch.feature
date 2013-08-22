Feature: Batch related features

  Scenario: Open-Close Batch
    Given I am logged in as researcher
    And I have prime locations
    And I have a batch
    And I visit batches listing page
    And I visit the first batch listed
    Then I should see all the prime locations with open close toggles
    When I open batch for a location
    Then I should see it is open for that location in db
    When I close batch for a location
    Then I should see it is closed for that location in db

  Scenario: Add new Batch
    Given I am logged in as researcher
    And I visit batches listing page
    And I click add batch button
    Then I should see a add batch page
    When I fill the details for add batch form
    And I submit the form
    Then I should go back to batches listing page
    And I should see batch successfully added message
