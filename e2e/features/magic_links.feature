Feature: Magic links
  Editors can share a page with someone who does not have an account.

  Background:
    Given the intranet has a site
    And the site has an index page "Camp"
    And the page "Camp" has an info page "Kit list"
    And the page "Camp" is magic link only

  Scenario: Without a link the page needs a login
    When I visit "/camp/kit-list/"
    Then I am on "/accounts/login/?next=/camp/kit-list/"

  Scenario: A magic link opens the page
    Given the page "Camp" has a magic link labelled "Parents"
    When I open the magic link "Parents"
    Then I am on "/camp/"
    And I see the heading "Camp"

  Scenario: A magic link keeps working for the rest of the visit
    Given the page "Camp" has a magic link labelled "Parents"
    When I open the magic link "Parents"
    And I visit "/camp/"
    Then I see the heading "Camp"

  Scenario: A magic link also opens the pages below it
    Given the page "Camp" has a magic link labelled "Parents"
    When I open the magic link "Parents"
    And I visit "/camp/kit-list/"
    Then I see the heading "Kit list"

  Scenario: A magic link for one page does not open its parent
    Given the page "Kit list" has a magic link labelled "Kit only"
    When I open the magic link "Kit only"
    Then I see the heading "Kit list"
    When I visit "/camp/"
    Then I am on "/accounts/login/?next=/camp/"

  Scenario: A revoked magic link no longer works
    Given the page "Camp" has a revoked magic link labelled "Old invite"
    When I open the magic link "Old invite"
    Then I am asked to log in

  Scenario: An expired magic link no longer works
    Given the page "Camp" has an expired magic link labelled "Last year"
    When I open the magic link "Last year"
    Then I am asked to log in

  Scenario: Editors can create a magic link from the page
    Given I am logged in as an editor
    When I visit "/camp/kit-list/"
    And I open the share dialog
    Then I see the text "No active magic links yet."
    When I create a magic link labelled "Parents"
    Then I see the magic link "Parents" in the share dialog
    And I do not see the text "No active magic links yet."

  Scenario: Editors can revoke a magic link
    Given the page "Kit list" has a magic link labelled "Parents"
    And I am logged in as an editor
    When I visit "/camp/kit-list/"
    And I open the share dialog
    And I revoke the magic link "Parents"
    Then I do not see the magic link "Parents" in the share dialog

  Scenario: A link created by an editor works for someone who is not logged in
    Given I am logged in as an editor
    When I visit "/camp/kit-list/"
    And I open the share dialog
    And I create a magic link labelled "Parents"
    Then someone who is not logged in can open the link and see the heading "Kit list"

  Scenario: Ordinary users cannot share pages
    Given I am logged in
    When I visit "/camp/kit-list/"
    Then I do not see the "Share" button
