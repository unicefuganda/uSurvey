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

  Scenario: Add new batch- Js validations
    Given I am logged in as researcher
    And I visit add batch page
    And I submit the form
    Then I should see validation error messages

  Scenario: List Batches
    Given I am logged in as researcher
    And I have 100 batches
    And I visit batches listing page
    And I should see the batches list paginated

  Scenario: Edit Batch
    Given I am logged in as researcher
    And I have a batch
    And I visit batches listing page
    And I click edit batch link
    Then I should see edit batch page
    When I fill the details for the batch
    And I submit the form
    Then I should go back to batches listing page
    And I should see the batch successfully edited

  Scenario: Delete Batch
    Given I am logged in as researcher
    And I have a batch
    And I visit batches listing page
    And I click delete batch link
    Then I should see confirm delete
    And if I click yes
    Then I should go back to batches listing page
    And I should see the batch successfully deleted
