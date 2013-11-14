Feature: Location Weights upload

  Scenario: Upload locations weights
    Given I am logged in as researcher
    And I have some locations to add weights
    And I have a survey
    When I visit upload locations weights page
    Then I should see upload weights form fields
    When I click on the link for input file format
    Then I should see table of location weights layout
    When I click on the link for input file format
    Then said weight layout should collapse
    When I have a locations weights csv file
    And I input that file
    And I select a survey
    And I click the save button
    Then I should see location weights successfully added
