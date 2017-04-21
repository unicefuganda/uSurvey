Feature: Group features

    Scenario: List Conditions Page
        Given I am logged in as researcher
        And I visit conditions listing page
        And I have 10 conditions
        And I should see the conditions list
        When I click the add button
        Then I should see the new condition form

    Scenario: List Groups Page
        Given I am logged in as researcher
        And I have a condition
        And I have 100 groups with that condition
        And I visit groups listing page
        Then I should see the groups list paginated

    Scenario: Add a group condition
        Given I am logged in as researcher
        And I visit the new condition page
        When I fill in the condition details
        And I click save button
        Then I should see that the condition was saved on the condition list page

    Scenario: Add household member a group
        Given I am logged in as researcher
        And I have a condition
        And I visit the new group page
        When I fill in the group details
        And I select a condition
        And I click save button
        Then I should see that the group was saved successfully

    Scenario: Create a condition on the group form
        Given I am logged in as researcher
        And I visit the new group page
        When I click the add new condition
        Then I should see the modal open
        When I fill in the condition details
        And I click the new condition form save button
        Then I should see the condition saved on create group page
        And I should see the new condition in the groups form

    Scenario: Create a condition with invalid form on the group form
        Given I am logged in as researcher
        And I visit the new group page
        When I click the add new condition
        Then I should see the modal open
        And I click the new condition form save button
        Then I should see the form errors of required fields

    Scenario: Create a group with multiple conditions
        Given I am logged in as researcher
        And I have 2 conditions
        And I visit the new group page
        When I fill name and order
        And I select conditions
        And I click save button
        Then I should see that the group was saved successfully

    Scenario: List group details
        Given I am logged in as researcher
        And I have member group with conditions
        And I visit groups listing page
        And I click view conditions link
        Then I should see a list of conditions
        When I click on add condition button
        Then I should see a new condition form for this group
        And When I fill condition details
        And I submit the form
        And I should see the newly added condition on that page

    Scenario: Add group from group listing page
        Given I am logged in as researcher
        And I visit groups listing page
        When I click the add group button
        Then I should go to add group page

    Scenario: JS validation for add group condition
        Given I am logged in as researcher
        And I visit the new condition page
        When I select gender as attribute
        Then I should see only Equals as available for condition
        And male and female for values
        When I select general as attribute
        Then I should see only Equals as available for condition
        And HEAD for values
        When I select age as attribute
        And If I add in a negative number
        And I click the new condition form save button
        Then I see error age cannot be negative

    Scenario: Edit a member group
        Given I am logged in as researcher
        And I have member group with conditions
        And I visit groups listing page
        And I click edit group link
        Then I should see the groups details in an edit group form
        When I fill in edited group details
        And I select new conditions
        And I submit the form
        Then I should see that the group was edited successfully

    Scenario: Delete a member a group
        Given I am logged in as researcher
        And I have member group with conditions
        And I visit groups listing page
        And I click delete group link
        Then I should see a delete confirmation modal
        When I click yes
        Then I should see that the group was deleted successfully

    Scenario: Delete a group condition
        Given I am logged in as researcher
        And I have member group with conditions
        And I visit conditions listing page
        And I click delete condition link
        Then I should see a delete condition confirmation modal
        When I click yes
        Then I should see that the condition was deleted successfully
