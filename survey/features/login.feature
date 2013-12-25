Feature: Login feature

  Scenario: Login page
    Given I have a user
    And And I visit the login page
    And I login a user
    Then I should see that I am logged in as given username

  Scenario: Login from Home page
    Given I have a user
    And I am in the home page
    And I click the login link
    And I login a user
    Then I should see that I am logged in as given username

  Scenario: Login from new investigator page
    Given I have a user
    And I have locations
    And I visit new investigator page
    And I login a user
    Then I should see new investigator with logout link

  Scenario: Login from list investigator page
    Given I have a user
    And I have locations
    And I visit investigators listing page
    And I login a user
    Then I should see list investigator with logout link

  Scenario: Login from new household page
    Given I have a user
    And I have locations
    And I have an investigator in that location
    And I visit new household page
    And I login a user
    Then I should see new household page with logout link

  Scenario: Login from download excel report page
    Given I have a user
     And I have three surveys
     And I have batches in those surveys
     And I visit download excel page
     And I login a user
     Then I should see download excel page with logout link

  Scenario: Login from users page
     Given I have a user
     And I visit new user page
     And I login a user
     Then I should see new user page with logout link
