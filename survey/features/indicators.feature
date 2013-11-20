Feature: Indicators feature

    Scenario: Add indicators
      Given I am logged in as researcher
      And I have a survey
      And I have a batch
      And I have two question modules
      And I visit new indicator page
      And I visit new indicator page
      And I fill in the indicator details
      And I submit the form
      Then I should see that the indicator was successfully added

    Scenario: List indicators
      Given I am logged in as researcher
      And I have a survey
      And I have three batches
      And I have two modules
      And I have an indicator not in that survey
      And I have indicator in each batch
      When I visit indicator listing page
      Then I should see all indicators listed
      And I should see action buttons
      When I select a survey
      And I click on get list
      Then I should see indicators in that survey
      When I select a batch
      And I click on get list
      Then I should see indicators in that batch
      When I select a module
      And I click on get list
      Then I should see indicators in that module
      When I click on add indicator button
      Then I should see add indicator page

  Scenario: Delete Indicator
    Given I am logged in as researcher
    And I have two indicators
    When I visit indicator listing page
    And I click the delete indicator link
    Then I should see confirm indicator batch
    And if I click yes
    Then I should go back to indicator listing page
    And I should see the indicator successfully deleted
