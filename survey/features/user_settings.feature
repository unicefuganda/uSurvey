Feature: User Settings feature

    Scenario: user settings links    
      Given I have a user
      And I visit the login page
      And I login a user
      And I am in the home page
      And I click user settings link
      Then I see edit profile, change password and logout link
    
    Scenario: Change use password 
      Given I have a user
      And I visit the login page
      And I login a user
      And I am in the home page
      And I click user settings link
      Then I see edit profile, change password and logout link
      Then I click change password link
      Then I should see a form asking me to add old password and new password
      Then I fill in the old password and new password
      And I click the change my password button
      Then I should see password reset successfully
      
    Scenario: Change user password with errors 
      Given I have a user
      And I visit the login page
      And I login a user
      And I am in the home page
      And I click user settings link
      Then I see edit profile, change password and logout link
      Then I click change password link
      Then I should see a form asking me to add old password and new password
      Then I fill in the wrong old password and correct new password
      And I click the change my password button
      Then I should error that my old password is incorrect and password mismatch