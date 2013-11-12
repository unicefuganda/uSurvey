Feature: Homepage feature

  Scenario: Home page
    Given I am not logged in
    And I am in the home page
    Then I should see the completion map

  Scenario: About page
    Given I am not logged in
    Then I should see the about link
    And If I click the about link
    Then I am in the about page
    And I should see the about text provided by panwar
