Feature: Users feature

    Scenario: new user page
      Given I am logged in as a superuser
      And I visit new user page
      Then I see all  new user fields
      And I click submit
      Then I should see the error messages

    Scenario: create user
       Given I am logged in as a superuser
       And I have a group
       And I visit new user page
       Then I fill all necessary new user fields
       And I click submit
       Then I should see user successfully registered
       And I can login that user successfully

    Scenario: create user with already existing mobile
      Given I am logged in as a superuser
      And I have a group
      And I visit new user page
      Then I fill an existing mobile number
      And I click submit
      Then I should see existing mobile number error message

    Scenario: create user with already existing username
      Given I am logged in as a superuser
      And I have a group
      And I visit new user page
      Then I fill an existing username
      And I click submit
      Then I should see existing username error message

    Scenario: create user with already existing email
      Given I am logged in as a superuser
      And I have a group
      And I visit new user page
      Then I fill an existing email
      And I click submit
      Then I should see existing email error message

    Scenario: create user with prohibited username
      Given I am logged in as a superuser
      And I have a group
      And I visit new user page
      Then I fill a not allowed username
      And I click submit
      Then I should see not allowed username error message
      
    Scenario: List users
      Given I am logged in as a superuser
      And I have 100 users
      And I visit the users list page
      Then I should see a list of users
    Scenario: Edit a user
      Given I am logged in as a superuser
      And I have two users
      And I visit the users list page
      And I select edit action
      Then I should see the users information in a form
      When I click the update button
      Then I should see user information saved successfully