Feature: Investigators feature

    Scenario: Investigator new page
      Given I am logged in as researcher
      And I have locations
      And I visit new investigator page
      And I see all the fields are present
      And I submit the form
      Then I should see the error messages
    
    Scenario: Create an investigator
       Given I am logged in as researcher
       And I have locations
       And I visit new investigator page
       And I fill all necessary fields
       And I submit the form
       Then I should see that the investigator is created
    
    Scenario: List investigators
      Given I have 100 investigators
      Given I am logged in as researcher
      And I have locations
      And I visit investigators listing page
      And I should see the investigators list paginated

    Scenario: No investigators list
      Given I have no investigators
      Given I am logged in as researcher
      And I have locations
      And I visit investigators listing page
      And I should see no investigators registered message
    
    Scenario: No investigators filter list
      Given I am logged in as researcher
      And I have locations
      And I request filter list of a County with no associated investigator
      Then I should see no investigator for this County
    
    Scenario: Create an investigator - validation
      Given I am logged in as researcher
      And I have locations
      And I visit new investigator page
      And I fill in already registered mobile number
      And I submit the form
      Then I should see that mobile number is already taken

    Scenario: View investigator details
      Given I am logged in as researcher
      And I have one investigator
      And I visit investigators page
      And I click on the investigators name
      Then I should see his details displayed
      And I should see navigation links
      Then back button should take back to Investigator Listing page

    Scenario: Edit investigator details
      Given I am logged in as researcher
      And I have one investigator
      And I visit investigators page
      And I click on the edit button
      Then it should be able to take me to edit form page
      And I change Name of investigator
      And I click on save
      Then I should go back to investigator details page
      And I should see name of investigator updated

    Scenario: Block investigators
      Given I am logged in as researcher
      And I have one investigator
      And I visit investigators listing page
      And I click block the investigator
      Then I should see block investigator confirmation modal
      When I confirm block the investigator
      Then I should see the investigator blocked successfully
      And I should see unblock investigator
      And I click unblock the investigator
      Then I should see unblock investigator confirmation modal
      When I confirm unblock the investigator
      Then I should see the investigator unblocked successfully