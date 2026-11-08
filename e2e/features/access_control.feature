Feature: Access control
  Pages are only shown to the people they are meant for.

  Scenario: Logged in only pages send visitors to the login page and back again
    Given the intranet has a site
    And the site has an info page "Staff handbook"
    And a user "alice" exists
    When I visit "/staff-handbook/"
    Then I am on "/accounts/login/?next=/staff-handbook/"
    When I log in as "alice" with the password "password"
    Then I am on "/staff-handbook/"
    And I see the heading "Staff handbook"

  Scenario: Pages are logged in only unless they say otherwise
    Given the intranet has a site
    And the site has an info page "Staff handbook"
    When I visit "/"
    Then I am on "/accounts/login/?next=/"

  Scenario: Public pages can be read by anyone
    Given the intranet has a site
    And the site has an info page "Open day"
    And the page "Open day" is public
    When I visit "/open-day/"
    Then I am on "/open-day/"
    And I see the heading "Open day"

  Scenario: Pages inherit access from the section they are in
    Given the intranet has a site
    And the site has an index page "Public notices"
    And the page "Public notices" has an info page "Fireworks night"
    And the page "Public notices" is public
    When I visit "/public-notices/fireworks-night/"
    Then I see the heading "Fireworks night"

  Scenario: A page can be stricter than the section it is in
    Given the intranet has a site
    And the site has an index page "Public notices"
    And the page "Public notices" has an info page "Leader rota"
    And the page "Public notices" is public
    And the page "Leader rota" is logged in only
    When I visit "/public-notices/leader-rota/"
    Then I am on "/accounts/login/?next=/public-notices/leader-rota/"

  Scenario: A password protected page asks for its password
    Given the intranet has a site
    And the site has an info page "Leaders' notes" with the introduction "Where the spare tents are kept"
    And the page "Leaders' notes" is public
    And the page "Leaders' notes" has the password "tent-peg"
    When I visit "/leaders-notes/"
    Then I see the text "You need a password to access this page."
    And I do not see the text "Where the spare tents are kept"
    When I enter the password "tent-peg"
    Then I see the text "Where the spare tents are kept"

  Scenario: A wrong password keeps the page locked
    Given the intranet has a site
    And the site has an info page "Leaders' notes" with the introduction "Where the spare tents are kept"
    And the page "Leaders' notes" is public
    And the page "Leaders' notes" has the password "tent-peg"
    When I visit "/leaders-notes/"
    And I enter the password "guess"
    Then I see the text "You need a password to access this page."
    And I do not see the text "Where the spare tents are kept"
