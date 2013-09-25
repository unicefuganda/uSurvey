Feature: Batch related features

  Scenario: Add new answer rule to batch question
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a question
    And I assign batch to these questions
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    When I fill in skip rule details
    And I submit the form
    Then I should see the logic was successfully added to the question


