Feature: Login feature

  Scenario: Login page
    Given I have a user
    And And I visit the login page
    And I login a user
    Then I should see home page and logout link

    # Scenario: Login page
    #   Given I have a user
    #   And I am in the homepage
    #   And I click the login page
    #   And I login a user
    #   Then I should see home page and logout link
