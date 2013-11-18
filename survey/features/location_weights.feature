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
    Then I should see location weights upload is in progress

  Scenario: List locations weights
    Given I am logged in as researcher
    And I have a survey
    And I have some locations with weights
    And I have error logs from location weights upload
    And I visit the list location weights page
    Then I should see the locations weights
    When i click the view error logs link
    Then I should see the error logs from previous the month