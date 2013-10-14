Feature: Batch related features

  Scenario: Add new answer rule to batch question
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a question
    And I assign batch to these questions
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    And I should see already existing logic for the question
    When I fill in skip rule details
    And I submit the form
    Then I should see the logic was successfully added to the question

  Scenario: Add answer rule to multichoice question - Javascript
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a module
    And I have a member group
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
    And I have a member group
    And I have a module
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
    When I select greater than value from the drop down
    Then I should see attribute field defaulted to value
    And I should not see question in the attribute
    When I select less than value from the drop down
    Then I should see attribute field defaulted to value
    And I should not see question in the attribute
    When I select greater than question from the drop down
    Then I should see attribute field defaulted to question
    And I should not see value in the attribute
    When I select less than question from the drop down
    Then I should see attribute field defaulted to question
    And I should not see value in the attribute
    When I select equals from drop down
    And I should see attribute field defaulted to value
    And I should see question in the attribute
    And I should not see option dropdown box and questions dropdown
    When I select question option from dropdown
    Then I should see questions dropdown
    And I should not see option dropdown box and value text box
    And I should see all the action dropdown options

   Scenario: Add Between condition- Javascript
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a question
    And I assign batch to these questions
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    When I select between from the drop down
    Then I should see attribute field defaulted to value
    And I should not see question in the attribute
    And I should see two text fields for min and max value
    And I should not see option dropdown box and value text box


  Scenario: add rule ask subquestion to a question
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a question
    And I assign batch to these questions
    And I have two subquestions for this question
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    And I should not see the add subquestion button
    When I select ask subquestion from then field
    Then I should see next question populated with subquestions
    And I should not the add subquestion button

  Scenario: Add subquestion modal
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a question
    And I assign batch to these questions
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    When I select ask subquestion from then field
    Then I should see add subquestion button
    When I click add subquestion button
    Then I should see a modal for add subquestion
    When I fill the subquestion details
    And I click save question button on the form
    Then I should see the recent subquestion in next question dropdown

  Scenario: Add duplicate subquestion on modal
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a question
    And I assign batch to these questions
    And I have a subquestion under this question
    And I visit batches question list page
    And I click on add logic link
    Then I should see the add logic page
    When I select ask subquestion from then field
    Then I should see add subquestion button
    When I click add subquestion button
    Then I should see a modal for add subquestion
    When I fill the  duplicate subquestion details
    And I click save question button on the form
    And I should see error on the form text field
    When I refill the form with valid values
    And I click save question button on the form
    Then I should see the recent subquestion in next question dropdown