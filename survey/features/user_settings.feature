Feature: User Settings feature

    Scenario: user settings links    
      Given I have a user
      And I visit the login page
      And I login a user
      And I am in the home page
      Then I see user settings link
      And I click user settings link
      Then I see edit profile and logout link
