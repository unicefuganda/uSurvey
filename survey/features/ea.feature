Feature: EA upload

  Scenario: Upload EA
    Given I am logged in as researcher
    And I have some locations to add EA
    And I have a survey
    When I visit upload EA page
    Then I should see EA upload form fields
    When I click on the link for input file format
    Then I should see table of EA layout
    When I click on the link for input file format
    Then said EA layout should collapse
    When I have a EA csv file
    And I input that file
    And I select a survey
    And I click the save button
    Then I should see EA upload is in progress
