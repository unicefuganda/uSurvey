Feature: About page

    Scenario: Create about us content
        Given I am logged in as admin
        And I have about us content
        And I visit the about us page
        Then I should see the sample about us information
        When I click the edit link
        Then I should see the existing content in a text area
        When I modify about us content
        And I submit the form
        Then I should see the content was updated successfully

    Scenario: About us anonymous user
        Given I  am an anonymous user
        And I have about us content
        And I visit the about us page
        Then I should see the sample about us information
        And I should not see the edit about us button
