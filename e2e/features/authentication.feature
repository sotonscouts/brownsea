Feature: Authentication
  People log in with a username and password, and can log out again.

  Scenario: Logging in
    Given the intranet has a site
    And a user "alice" exists
    When I visit "/accounts/login/"
    Then I see the heading "Login to Brownsea Intranet"
    When I log in as "alice" with the password "password"
    Then I am on "/"
    And I see the "Logout" button in the navigation
    And I do not see "Login" in the navigation

  Scenario: A wrong password is rejected
    Given the intranet has a site
    And a user "alice" exists
    When I visit "/accounts/login/"
    And I log in as "alice" with the password "not-her-password"
    Then I am on "/accounts/login/"
    And I see the text "Please enter a correct username and password"
    And I see "Login" in the navigation

  Scenario: An unknown user is rejected
    Given the intranet has a site
    When I visit "/accounts/login/"
    And I log in as "nobody" with the password "password"
    Then I am on "/accounts/login/"
    And I see the text "Please enter a correct username and password"

  Scenario: Logging out
    Given the intranet has a site
    And I am logged in
    When I visit "/"
    And I click the "Logout" button in the navigation
    Then I am on "/accounts/login/"
    And I see "Login" in the navigation
    When I visit "/"
    Then I am on "/accounts/login/?next=/"

  Scenario: People who are already logged in skip the login page
    Given the intranet has a site
    And I am logged in
    When I visit "/accounts/login/"
    Then I am on "/"

  Scenario: Editors log in to the Wagtail admin separately
    Given the intranet has a site
    And an editor "editor" exists
    When I visit "/admin/"
    Then I am on "/admin/login/?next=/admin/"
    When I sign in to the admin as "editor" with the password "password"
    Then I am on "/admin/"
    And I see the heading "Brownsea Intranet"

  Scenario: Ordinary users cannot use the Wagtail admin
    Given the intranet has a site
    And a user "alice" exists
    When I visit "/admin/login/"
    And I sign in to the admin as "alice" with the password "password"
    Then I see the text "You do not have permission to access the admin"

  Scenario: The admin rejects a wrong password
    Given the intranet has a site
    And an editor "editor" exists
    When I visit "/admin/login/"
    And I sign in to the admin as "editor" with the password "wrong"
    Then I see the text "Your username and password didn't match"
