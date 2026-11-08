Feature: Search
  Logged in users can find pages from any page on the site.

  Scenario: Searching from the header
    Given the intranet has a site
    And the site has an info page "Camping guide" with the introduction "Everything about tents"
    And the site has an info page "Kayaking guide"
    And I am logged in
    When I visit "/"
    And I search for "camping"
    Then I am on "/search/?query=camping"
    And I see the search results:
      | Camping guide |
    And I see the text "Everything about tents"

  Scenario: A search result takes you to the page
    Given the intranet has a site
    And the site has an info page "Camping guide"
    And I am logged in
    When I visit "/search/?query=camping"
    And I open the search result "Camping guide"
    Then I am on "/camping-guide/"
    And I see the heading "Camping guide"

  Scenario: Nothing matches
    Given the intranet has a site
    And the site has an info page "Camping guide"
    And I am logged in
    When I visit "/"
    And I search for "zeppelin"
    Then I see the text "No results found for"

  Scenario: Anonymous visitors are asked to log in
    Given the intranet has a site
    When I visit "/search/?query=camping"
    Then I am on "/accounts/login/?next=/search/%3Fquery%3Dcamping"
