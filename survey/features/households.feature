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

    # Scenario: Create a household - children validation
    #     Given I am logged in as researcher
    #     And I have locations
    #     And I visit new household page
    #     And I click No to has children
    #     Then I should see children number fields disabled
    #     And No below 5 is also checked
    #     And checking below 5 to yes does not work
    #     And Now If I click to Yes to has children
    #     Then all children number fields are enabled back
    #
    # Scenario: Create a household - below 5 validation
    #     Given I am logged in as researcher
    #     And I have locations
    #     And I visit new household page
    #     And I click No to has below 5
    #     Then I should see below 5 number fields disabled
    #     And Now If I click Yes to below 5
    #     Then below 5 number fields are enabled back
    #
    # Scenario: Create a household - has women validation
    #     Given I am logged in as researcher
    #     And I have locations
    #     And I visit new household page
    #     And I click No to has women
    #     Then I should see has women number fields disabled
    #     And Now If I click Yes to has women
    #     Then has women number fields are enabled back
    #
    # Scenario: Create a household - 15_49 women validation
    #     Given I am logged in as researcher
    #     And I have locations
    #     And I visit new household page
    #     And I click Yes to has women
    #     And I fill in 15_19 higher than 15_49
    #     And I submit the form
    #     Then I should see an 15_49 error
