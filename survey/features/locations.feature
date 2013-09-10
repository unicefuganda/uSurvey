Feature: Geographical location feature

    Scenario: add location type page
      Given I am logged in as researcher
      And I visit new location type page
      And I see all location type fields are present
      And I submit the form
      Then I should see the error messages

  Scenario: Create a location_type
     Given I am logged in as researcher
     And I visit new location type page
     And I fill all necessary location type fields
     And I submit the form
     Then I should see that the location type is created

 Scenario: Create location
    Given I am logged in as researcher
    And I have a location type
    And I visit new location page
    And I fill all necessary location fields
    And I submit the form
    Then I should see that the location is created
