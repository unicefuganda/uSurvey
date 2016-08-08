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
    When I click the view error logs link
    Then I should see the error logs from previous the month

  Scenario: List locations weights -- pagination and upload link
    Given I am logged in as researcher
    And I have a survey
    And I have some 100 locations with weights
    And I visit the list location weights page
    Then I see locations weights paginated
    When I click the upload weights link
    Then I should see upload weights page


  Scenario: Filter list locations weights
    Given I am logged in as researcher
    And I have two surveys
    And I have a number of locations and weights in each survey
    And I visit the list location weights page
    And I select one survey
    And I click get list
    Then I should see the location weights in that survey
    When I select a location
    And I click get list
    Then I should see the weights for that location and survey

  Scenario: List and filter upload weights error logs
    Given I am logged in as researcher
    And I have some error logs for upload weights
    And I visit the weights error logs page
    Then I should see all error logs
    When I select from and to dates
    And I click the filter link
    Then I should see only error logs between those dates