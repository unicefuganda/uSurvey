Feature: Permissions feature

  Scenario: Anonymous user tabs
      Given I  am an anonymous user
      And I visit the login page
      Then I should see anonymous user allowed tabs
      And I should not be seeing above anonymous user level tabs

  Scenario: Data entry Tabs
      Given I have a data entry user
      And And I visit the login page
      And I login that user
      Then I should see data entry allowed tabs
      And I should not be seeing above data entry level tabs

  Scenario: Researcher Tabs
      Given I have a researcher user
      And And I visit the login page
      And I login that user
      Then I should see researcher allowed tabs
      And I should not be seeing above researcher level tabs

  Scenario: Admin Tabs
      Given I have a admin user
      And And I visit the login page
      And I login that user
      Then I should all tabs

  Scenario: Notify investigators
      Given I have a data entry user
      And And I visit the login page
      And I login that user
      Then I should not see notify investigators drop-down