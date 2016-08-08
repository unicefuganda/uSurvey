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

    Scenario: Delete a Question module
      Given I am logged in as researcher
      And I have two question modules
      When I visit the list questions modules page
      And I click delete module
      I should see a delete module confirmation modal
      When I confirm delete
      Then I should see the module was deleted

    Scenario: Edit a Question module
      Given I am logged in as researcher
      And I have two question modules
      When I visit the list questions modules page
      And I click edit module
      I should see a edit module page
      When I fill in valid values
      And I submit the form
      Then I should see the edited question module