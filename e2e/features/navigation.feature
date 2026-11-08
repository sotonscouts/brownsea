Feature: Primary navigation
  The header gives everyone a way around the site, and a way to log in or out.

  Scenario: Anonymous visitors are offered the login page instead of the menu
    Given the intranet has a site
    And the home page is public
    And the site has an info page "Guides"
    And the navigation has the links:
      | title | page   | url |
      |       | Guides |     |
    When I visit "/"
    Then I do not see "Guides" in the navigation
    And I see "Login" in the navigation
    When I click "Login" in the navigation
    Then I am on "/accounts/login/"
    And I see the heading "Login to Brownsea Intranet"

  Scenario: The menu can be shown to anonymous visitors
    Given the intranet has a site
    And the home page is public
    And anonymous visitors can see the menu
    And the site has an info page "Guides"
    And the navigation has the links:
      | title | page   | url |
      |       | Guides |     |
    When I visit "/"
    Then I see "Guides" in the navigation

  Scenario: Logged in users can follow a link in the menu
    Given the intranet has a site
    And the site has an info page "Guides"
    And the navigation has the links:
      | title | page   | url |
      |       | Guides |     |
    And I am logged in
    When I visit "/"
    And I click "Guides" in the navigation
    Then I am on "/guides/"
    And I see the heading "Guides"

  Scenario: A link can use its own title instead of the page title
    Given the intranet has a site
    And the site has an info page "Guides"
    And the navigation has the links:
      | title        | page   | url |
      | Handy guides | Guides |     |
    And I am logged in
    When I visit "/"
    Then I see "Handy guides" in the navigation
    And I do not see "Guides" in the navigation

  Scenario: Menus open to show grouped links
    Given the intranet has a site
    And the site has an info page "Safeguarding"
    And the navigation has a "Resources" menu with the group "Policies" containing the pages:
      | Safeguarding |
    And I am logged in
    When I visit "/"
    And I click "Resources" in the navigation
    Then I see the text "Policies"
    When I click "Safeguarding" in the menu
    Then I am on "/safeguarding/"
    And I see the heading "Safeguarding"

  Scenario: Logged in users can search and log out from the header
    Given the intranet has a site
    And I am logged in
    When I visit "/"
    Then I do not see "Login" in the navigation
    And I see the "Logout" button in the navigation

  Scenario: The logo takes you back to the home page
    Given the intranet has a site
    And the site has an info page "Guides"
    And I am logged in
    When I visit "/guides/"
    And I click "Brownsea Intranet" in the navigation
    Then I am on "/"
