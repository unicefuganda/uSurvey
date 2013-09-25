Feature: Survey features

  Scenario: List survey page
    Given I am logged in as researcher
    And I have 100 surveys
    And I visit surveys listing page
    Then I should see the survey list paginated
    And when I click on add batch action for first survey
    Then I should go to add batch page

  Scenario: Link to batch list
    Given I am logged in as researcher
    And I have a survey
    And I visit surveys listing page
    And I click on a survey name
    Then I should see a list of the batches under the survey

  Scenario: Add a survey
    Given I am logged in as researcher
    And I visit the new survey page
    When I fill in the survey details
    And I click save button
    Then I should see that the survey was saved successfully

  Scenario: Add survey modal
    Given I am logged in as researcher
    And I visit surveys listing page
    And I click on create new survey button
    Then I should see the create new survey modal
    When I fill in the survey details
    And I click the modal save button
    Then I should see that the survey was saved successfully

  Scenario: Edit a survey
    Given I am logged in as researcher
    And I have a survey
    And I visit surveys listing page
    And I click on edit link for this survey
    Then I should see the edit survey page
    When I fill in the survey details
    And I submit the form
    Then I should see that the survey was edited successfully


