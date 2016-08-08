
Feature: Question feature
  Scenario: List Questions Under a batch
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have 100 questions under the batch
    And I visit questions listing page of the batch
    Then I should see the questions list paginated
    When I change to 100 questions per page
    Then I should not see pagination
    And I should be able to export questions


  Scenario: List Questions Under an open-batch
    Given I am logged in as researcher
    And I have a survey
    And I have a location
    And I have an open batch in that location
    And I have a multichoice and numeric questions with logics
    And I visit questions listing page of the batch
    Then I should see question list with only view options action
    And I should be able to export questions

  Scenario: Error Message on no question
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have no questions under the batch
    And I visit questions listing page of the batch
    Then I should see error message on the page

  Scenario: Add new question to batch
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I visit questions listing page of the batch
    And I have a member group
    And I click add question button
    Then I should see the assign question page of that batch

  Scenario: MultiChoice question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I visit create new question page
    Then I should see special characters message
    And I fill the details for question
    When I select multichoice for answer type
    Then I should see one option field
    When I click add-option icon
    Then I should see two options field
    When I click remove-option icon
    Then I should see only one option field
    And I fill an option question
    And I submit the form
    And I should see question successfully added message

  Scenario: List All Questions
    Given I am logged in as researcher
    And I have more than 50 questions
    And I visit questions list page
    Then I should see the questions list paginated
    And I should be able to export questions
    And If I click create new question link
    Then I should see create new question page


  Scenario: View multichoice question options
    Given I am logged in as researcher
    And I have a member group
    And I have a survey
    And I have a module
    And I have a multichoice question
    And I select multichoice question in batch
    And I have a sub question for that question
    And I have a rule linking one option with that subquestion
    And I visit questions list page
    And I click on view options link
    Then I should see the question options in a modal
    And when I click the close button
    Then I should be back to questions list page
    And I visit questions listing page of the batch
    And I click on view options link again
    And I click delete question rule
    And I click confirm delete
    Then I should go back to questions listing page
    And I should see that the logic was deleted successfully

  Scenario: Add Subquestion
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I visit questions list page
    And I click on view add subquestion link
    Then I should go to add subquestion page
    And I submit the form
    Then I should see field required error message
    When I fill in subquestion details
    And I submit the form
    And I should see subquestion successfully added message

  Scenario: Edit question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I visit question listing page
    And I click the edit question link
    Then I should see the edit question page
    And I see the question form with values
    When I fill in edited question details
    And I submit the form
    Then I should see the question successfully edited

  Scenario: Delete question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I visit questions list page
    And I click on delete question link
    Then I should see a delete question confirmation modal 
    When I click yes 
    Then I should see that the question was deleted successfully

  Scenario: View sub question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I have a sub question for that question
    And I visit questions list page
    Then I should not see the sub question
    When I click on the question
    Then I should see the sub question below the question

  Scenario: Duplicate sub question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I have a subquestion under that question
    And I visit questions list page
    And I click on view add subquestion link
    Then I should go to add subquestion page
    When I fill in duplicate subquestion details
    And I submit the form
    And I should see subquestion not added message

  Scenario: View question logic
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a non multichoice question
    And I have a sub question for that question
    And I have a rule on value with that subquestion
    And I visit batches question list page
    And I click on view logic link
    Then I should see the logic in a modal
    Then I should see the sub question below the question
    And when I click the close button
    Then I should be back to questions list page

  Scenario: Delete question logic
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have a member group
    And I have a module
    And I have a non multichoice question
    And I have a sub question for that question
    And I have a rule on value with that subquestion
    And I visit batches question list page
    And I click on view logic link
    Then I should see the logic in a modal
    Then I should see delete logic icon
    When I click delete logic icon
    And I click confirm delete
    Then I should redirected to batch question page

  Scenario: Delete sub question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I have a sub question for that question
    And I visit questions list page
    When I click on the question
    And I click delete sub question link
    Then I should see a confirm delete subqestion modal
    When I click confirm delete
    Then I should see the sub question deleted successfully

  Scenario: Edit sub question
    Given I am logged in as researcher
    And I have a member group
    And I have a module
    And I have a multichoice question
    And I have a sub question for that question
    And I visit questions list page
    When I click on the question
    And I click edit sub question link
    Then I see the sub question form with values
    When I fill in edited sub question details
    And I submit the form
    Then I should see the sub question successfully edited