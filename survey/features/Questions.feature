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