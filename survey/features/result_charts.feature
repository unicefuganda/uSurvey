Feature: Result Charts

    Background:
        Given I am logged in as researcher
        And I have hierarchical locations with district and village
        And I have investigators completed batches

    Scenario: Numerical answers - top level location hierarchy
        Given I am on the numerical answer computation page
        And I select a district to see results
        Then I should see the computed value
        And I should see the bar graph for all the villages

    Scenario: Numerical answer - village level
        Given I am on the numerical answer computation page
        And I select a village to see results
        Then I should see the computed value
        And I should see the bar graph for all the households

    Scenario: Multi choice answers - top level location hierarchy
        Given I am on the multi choice answer computation page
        And I select a district to see results
        Then I should see the computed bar chart for all the options
        And I should see the stacked bar graph for all the villages

    Scenario: Multi choice answer - village level
        Given I am on the multi choice answer computation page
        And I select a village to see results
        Then I should see the computed bar chart for all the options
        And I should see the tabulated results for all the households