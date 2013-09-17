Feature: Batch related features

  Scenario: Open-Close Batch
    Given I am logged in as researcher
    And I have prime locations
    And I have a survey
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
    And I have a survey
    And I visit add batch page
    When I fill the details for add batch form
    And I submit the form
    Then I should go back to batches listing page
    And I should see batch successfully added message

  Scenario: Add new batch- Js validations
    Given I am logged in as researcher
    And I have a survey
    And I visit add batch page
    And I submit the form
    Then I should see validation error messages

  Scenario: List Batches
    Given I am logged in as researcher
    And I have a survey
    And I have 100 batches
    And I visit batches listing page
    And I should see the batches list paginated

  Scenario: Edit Batch
    Given I am logged in as researcher
    And I have a survey
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
    And I have a survey
    And I have a batch
    And I visit batches listing page
    And I click delete batch link
    Then I should see confirm delete
    And if I click yes
    Then I should go back to batches listing page
    And I should see the batch successfully deleted

  Scenario: Batch Details- Listing questions under batch
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I visit batches listing page
    And I click on batch name
    Then I should be on the list of questions under the batch page

  Scenario: Assign questions to batch
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have 2 questions
    And I visit batches listing page
    And I click on assign question link
    Then I should see the assign question page of that batch
    When I select some questions
    And I submit the form
    Then I should see the questions successfully assigned to that batch

  Scenario: Assign question filter
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have one question belonging to that group
    And another question which does not
    And I visit the assign question to page batch
    When I select the group
    Then I should see the question which belong to that group

  Scenario: Add new Batch modal
    Given I am logged in as researcher
    And I have a survey
    And I visit batches listing page
    And I click add batch modal button
    Then I should see the add batch modal
    When I fill the details for add batch form
    And I click the modal save button
    And I should see batch successfully added message

