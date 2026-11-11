Feature: Choosing an article's author
  Editors credit an article to someone through one of their roles, such as "Sam Smith, Trustee", picked from a chooser
  they can search by name or role. The role is kept, so the article still shows it after the person moves on.

  Background:
    Given the intranet has a site
    And the site has a news index
    And the news has the articles:
      | title     | published  | type         |
      | Camp tips | 2026-03-05 | Announcement |
    And "Sam Smith" has the past role "Deputy District Commissioner" and the current role "Trustee"
    And I am logged in as an editor

  Scenario: An editor finds an author by name and picks their role
    When I edit the article "Camp tips"
    And I choose the author "Sam Smith, Trustee" by searching for "Sam"
    Then the author field shows "Sam Smith, Trustee"

  Scenario: Past roles can be picked too, and are marked as past
    When I edit the article "Camp tips"
    And I choose the author "Sam Smith, Deputy District Commissioner (past role)" by searching for "Deputy"
    Then the author field shows "Sam Smith, Deputy District Commissioner (past role)"

  Scenario: The chooser does not offer to create a role
    When I edit the article "Camp tips"
    And I open the author chooser
    Then I am not offered to create a new role
