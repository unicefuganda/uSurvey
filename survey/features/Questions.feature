Feature: Questions related features

  Scenario: List Questions Under a batch
    Given I am logged in as researcher
    And I have a survey
    And I have a batch
    And I have 100 questions under the batch
    And I visit questions listing page of the batch
    Then I should see the questions list paginated

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
    And I visit create new question page
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
    And If I click create new question link
    Then I should see create new question page

  Scenario: View multichoice question options
    Given I am logged in as researcher
    And I have a member group
    And I have a multichoice question
    And I visit questions list page
    And I click on view options link
    Then I should see the question options in a modal
    And when I click the close button
    Then I should be back to questions list page

  Scenario: Add Subquestion
    Given I am logged in as researcher
    And I have a member group
    And I have a multichoice question
    And I visit questions list page
    And I click on view add subquestion link
    Then I should go to add subquestion page
    When I fill in subquestion details
    And I submit the form
    And I should see subquestion successfully added message

 Scenario: Invalid MultiChoice question
    Given I am logged in as researcher
    And I have a member group
    And I visit create new question page
    And I fill the invalid details details for question
    When I select multichoice for answer type
    And I fill an option question
    And I submit the form
    And I should see question was not added
    And I should see that option in the form

  Scenario: Edit question
    Given I am logged in as researcher
    And I have a member group
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
    And I have a multichoice question
    And I visit questions list page
    And I click on delete question link
    Then I should see a delete question confirmation modal 
    When I click yes 
    Then I should see that the question was deleted successfully

  Scenario: View sub question
    Given I am logged in as researcher
    And I have a member group
    And I have a multichoice question
    And I have a sub question for that question
    And I visit questions list page
    Then I should not see the sub question
    When I click on the question
    Then I should see the sub question below the question 