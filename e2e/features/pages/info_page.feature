Feature: Information page
  An information page presents guidance as an introduction followed by a body of content blocks.

  Background:
    Given the intranet has a site
    And I am logged in

  Scenario: An information page shows its title and introduction
    Given the site has an info page "Trip guide" with the introduction "Everything for the weekend away"
    When I visit "/trip-guide/"
    Then I see the heading "Trip guide"
    And I see the text "Everything for the weekend away"
    And the browser tab is titled "Trip guide"

  Scenario: The body shows its blocks in the order they were written
    Given the site has an info page "Trip guide" with the body:
      | block   | value               |
      | heading | Before you go       |
      | text    | Check the weather   |
      | quote   | Always be prepared  |
      | heading | When you get there  |
      | text    | Find the campsite   |
    When I visit "/trip-guide/"
    Then the page body reads:
      | Before you go      |
      | Check the weather  |
      | Always be prepared |
      | When you get there |
      | Find the campsite  |

  Scenario: A page with no body is just a title and introduction
    Given the site has an info page "Coming soon"
    When I visit "/coming-soon/"
    Then I see the heading "Coming soon"
    And the page body reads:
      |  |

  Scenario: Unpublished pages cannot be seen
    Given the site has an info page "Draft guide"
    And the page "Draft guide" is unpublished
    When I visit "/draft-guide/"
    Then the response status is 404
    And I see the heading "Page not found"

  Scenario: Pages can be found by searching for their content
    Given the site has an info page "Trip guide" with the body:
      | block | value             |
      | text  | Check the weather |
    And the site has an info page "Kit list" with the body:
      | block | value        |
      | text  | Bring a tent |
    When I visit "/"
    And I search for "weather"
    Then I see the search results:
      | Trip guide |
