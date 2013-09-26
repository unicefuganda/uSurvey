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

  Scenario: Add answer rule to multichoice question - Javascript
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a multichoice question
    And I assign batch to multichoice question
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    And I should see in multichoice if field defaulted to equals option
    And I should see if field is disabled
    And I should see attribute field defaulted to option
    And I should see attribute field is disabled
    And I should see dropdown of all available options
    And I should not see value text box and questions dropdown
    When I select option from dropdown
    And I select skip to from then field
    Then I should see field for next question next to the then field
    When I select end interview from then field
    Then I should not see field for next question next to the then field

  Scenario: Add answer rule to question which is not multichoice - Javascript
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a question
    And I assign batch to these questions
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    And I should see if field defaulted to equals
    And I should see if field is not disabled
    And I should also have all other conditions in the dropdown
    And I should see attribute field defaulted to value
    And I should also have question in the attribute field dropdown
    And I should see attribute field is not disabled
    And I should see value text field
    And I should not see option dropdown box and questions dropdown
    When I select question option from dropdown
    Then I should see questions dropdown
    And I should not see option dropdown box and value text box
    And I should see all the action dropdown options


