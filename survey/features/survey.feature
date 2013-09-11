Feature: Survey features

  Scenario: List survey page
    Given I am logged in as researcher
    And I have 100 surveys
    And I visit surveys listing page
    Then I should see the survey list paginated
    And if I click the add survey button
    Then I should see the new survey form

  Scenario: Add a survey
    Given I am logged in as researcher
    And I have a batch
    And I have a question
    And I visit the new survey page
    When I fill in the survey details
    And I select the questions
    And I click save button
    Then I should see that the survey was saved successfully