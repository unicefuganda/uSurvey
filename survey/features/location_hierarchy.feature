Feature: Location hierarchy

  Scenario: Add location hierarchy
    Given I am logged in as admin
    And I have a country
    And I visit add location hierarchy page
    Then I should see text message
    And I should see country dropdown
    And I should see country present in dropdown
    And I should see a row for level details field
    When I click add row icon
    Then I should see anther row for levels details field
    When I click remove row icon
    Then I should see row for levels details field removed
    And the code field is hidden
    When I check has_code field
    Then length of code field is shown
    When I fill details
    And I click the create hierarchy button
    Then I should see location hierarchy successfully created

