Feature: Breadcrumbs
  Pages show where they sit in the site, with a way back up.

  Scenario: The home page has no breadcrumbs
    Given the intranet has a site
    And I am logged in
    When I visit "/"
    Then there are no breadcrumbs

  Scenario: A nested page shows its ancestors
    Given the intranet has a site
    And the site has an index page "Section"
    And the page "Section" has an info page "Details"
    And I am logged in
    When I visit "/section/details/"
    Then the breadcrumbs are "Home > Section"

  Scenario: Breadcrumbs link back up the tree
    Given the intranet has a site
    And the site has an index page "Section"
    And the page "Section" has an info page "Details"
    And I am logged in
    When I visit "/section/details/"
    And I click "Section" in the breadcrumbs
    Then I am on "/section/"
    And I see the heading "Section"
