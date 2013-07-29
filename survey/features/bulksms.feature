Feature: Bulk SMS

  Scenario: Sending Bulk SMS to investigators in selected locations
    Given I am logged in as researcher
    And I have 2 districts with investigators
    And I visit bulk SMS page
    And I compose a SMS to send
    And I select the districts
    And I click send
    Then I should see a message saying SMS has been sent

  Scenario: Bulk SMS validations
    Given I am logged in as researcher
    And I have 2 districts with investigators
    And I visit bulk SMS page
    And I click send
    Then I should see error message for location
    And I select the districts
    And I click send
    Then I should see error message for text
    And I type message the message
    Then I should see the counter has changed