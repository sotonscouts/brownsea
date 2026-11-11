Feature: People listing page
  The people page lists everyone marked Show in listing, under the teams of their current roles.

  Background:
    Given the intranet has a site
    And the site has a people page
    And I am logged in

  Scenario: Only people marked to show in the listing are listed
    Given the people are:
      | name          | in listing | roles                        |
      | Sam Smith     | yes        | District Commissioner @ Team |
      | Kayaker Jones | no         | Treasurer @ Team             |
    When I visit "/people/"
    Then I see the heading "People"
    And I see the "Team" section lists:
      | name      | roles                 |
      | Sam Smith | District Commissioner |
    And I do not see the text "Kayaker Jones"

  Scenario: Teams are shown in their set order, each with its people
    Given the people are:
      | name       | in listing | roles                           |
      | Zed Young  | yes        | Chair @ Trustees                |
      | Alex Jones | yes        | Treasurer @ Trustees            |
      | Sam Smith  | yes        | District Commissioner @ District team |
    When I visit "/people/"
    Then the people page has the team sections "Trustees, District team"
    And I see the "Trustees" section lists:
      | name       | roles     |
      | Alex Jones | Treasurer |
      | Zed Young  | Chair     |

  Scenario: People with a higher priority are listed first in their team
    Given the people are:
      | name       | in listing | roles                          |
      | Alex Jones | yes        | Treasurer @ Team               |
      | Zed Young  | yes        | Chair @ Team [priority 10]     |
      | Bea Brown  | yes        | Member @ Team                  |
    When I visit "/people/"
    Then I see the "Team" section lists:
      | name       | roles     |
      | Zed Young  | Chair     |
      | Alex Jones | Treasurer |
      | Bea Brown  | Member    |

  Scenario: Someone with roles in two teams is in both
    Given the people are:
      | name      | in listing | roles                                              |
      | Sam Smith | yes        | District Commissioner @ District team; Trustee @ Trustees |
    When I visit "/people/"
    Then I see the "District team" section lists:
      | name      | roles                 |
      | Sam Smith | District Commissioner |
    And I see the "Trustees" section lists:
      | name      | roles   |
      | Sam Smith | Trustee |

  Scenario: Past roles are not shown
    Given the people are:
      | name      | in listing | roles                                              |
      | Sam Smith | yes        | Deputy Commissioner @ Team [past]; Trustee @ Team |
    When I visit "/people/"
    Then I see the "Team" section lists:
      | name      | roles   |
      | Sam Smith | Trustee |
    And I do not see the text "Deputy Commissioner"

  Scenario: Roles with no team come last under Other roles
    Given the people are:
      | name         | in listing | roles                        |
      | Sam Smith    | yes        | District Commissioner @ Team |
      | Taylor Brown | yes        | Website editor               |
    When I visit "/people/"
    Then the people page has the team sections "Team, Other roles"
    And I see the "Other roles" section lists:
      | name         | roles          |
      | Taylor Brown | Website editor |
