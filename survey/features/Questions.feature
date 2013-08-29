Feature: Questions related features

Scenario: List Questions
  Given I am logged in as researcher
  And I have a batch
  And I have 100 questions under the batch
  And I visit questions listing page of the batch
  Then I should see the questions list paginated

Scenario: Error Message on no question
  Given I am logged in as researcher
  And I have a batch
  And I have no questions under the batch
  And I visit questions listing page of the batch
  Then I should see error message on the page

Scenario: Add new question to batch
  Given I am logged in as researcher
  And I have a batch
  And I visit questions listing page of the batch
  And I click add question button
  Then I should see a add question page
  When I fill the details for add question form
  And I submit the form
  Then I should go back to questions listing page
  And I should see question successfully added message
