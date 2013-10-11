Feature: Question module

    Scenario: List Question modules
      Given I am logged in as researcher
      And I have two question modules
      When I visit the list questions modules page
      Then I should see the questions modules listed

    Scenario: Create a Question module
      Given I am logged in as researcher
      When I visit the create questions module page
      And I fill in the question module details
      And I submit the form
      Then I should see that the question module on the listing page