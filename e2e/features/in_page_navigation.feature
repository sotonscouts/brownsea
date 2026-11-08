Feature: In-page navigation
  Long pages with several headings get a contents list that jumps to each section.

  Scenario: Jumping to a section
    Given the intranet has a site
    And the site has an info page "Trip guide" with the headings:
      | First steps    |
      | Packing list   |
      | After the trip |
    And I am logged in
    When I visit "/trip-guide/"
    Then I see the text "On this page"
    When I click "Packing list" in the page navigation
    Then I am on "/trip-guide/#packing-list"
    And the heading "Packing list" is in view

  Scenario: Short pages have no contents list
    Given the intranet has a site
    And the site has an info page "Trip guide" with the headings:
      | First steps  |
      | Packing list |
    And I am logged in
    When I visit "/trip-guide/"
    Then I do not see the text "On this page"
