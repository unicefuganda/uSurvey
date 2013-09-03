Feature: Households feature

    Scenario: Household new page
      Given I am logged in as researcher
      And I have locations
      And I visit new household page
      And I see all households fields are present
      And I submit the form
      Then I should see the error messages

    Scenario: Create a household
       Given I am logged in as researcher
       And I have locations
       And I have an investigator in that location
       And I visit new household page
       And I fill all necessary fields
       And I submit the form
       Then I should see that the household is created

    Scenario: Create a household with other-specify occupation
        Given I am logged in as researcher
        And I have locations
        And I visit new household page
        And Now If I choose Other as occupation
        Then I have to specify one
        And If I choose a different occupation
        Then Specify disappears

    Scenario: List all households
      Given I have an investigator
      Given I have 100 households
      Given I am logged in as researcher
      And I have locations
      And I am in the home page
      And I click households option
      And I select list households
      And I should see the households list paginated

    Scenario: No households list
      Given I have no households
      Given I am logged in as researcher
      And I have locations
      And I visit households listing page
      And I should see no household message


