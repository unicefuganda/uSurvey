Feature: Users feature

    Scenario: new user page
      Given I am logged in as a superuser
      And I visit new user page
      Then I see all  new user fields
      And I click submit
      Then I should see the error messages

