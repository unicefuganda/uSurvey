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
       And I have a member for that household
       And I visit households listing page
       And then I click on that household ID
       Then I should see household member title and add household member link
       And I should see that household details, its head and members
       And I should see actions edit and delete member


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
      And I click Survey Administration tab
      And I select list households
      And I should see the households list paginated
      When I click add household button
      Then I should see add household page

    Scenario: No households list
      Given I have no households
      Given I am logged in as researcher
      And I have locations
      And I visit households listing page
      And I should see no household message

    Scenario: Edit households
      Given I am logged in as researcher
      And I have locations
      And I have an investigator in that location
      And I have a household
      And I have two other investigators
      And I visit households listing page
      And then I click on that household ID
      Then I should be on the household details page
      When I click edit household
      Then I should see edit household form
      When I assign a new investigator
      And I submit the form
      Then I should see the investigator was saved successfully