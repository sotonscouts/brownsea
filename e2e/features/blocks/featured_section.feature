Feature: Featured section block
  A featured section highlights up to two pages or external sites as image cards. It is tested on the home page, the
  simplest page that takes it.

  Background:
    Given the intranet has a site
    And I am logged in

  Scenario: Two featured items sit side by side, each taking half the width
    Given the site has an info page "Camp guide" with the introduction "Pitch a tent"
    And the site has an info page "Kit list" with the introduction "Pack a bag"
    And the home page has the sections:
      | section    | title      | page       | url |
      | featured 1 | Camp guide | Camp guide |     |
      | featured 1 | Kit list   | Kit list   |     |
    When I visit "/"
    Then I see the cards:
      | Camp guide |
      | Kit list   |
    And the featured cards sit side by side, each half the width of the section
    And the card images have loaded

  Scenario: A lone featured item takes the full width
    Given the site has an info page "Camp guide"
    And the home page has the sections:
      | section    | title      | page       | url |
      | featured 1 | Camp guide | Camp guide |     |
    When I visit "/"
    Then I see the cards:
      | Camp guide |
    And the featured card takes the full width of the section
    And the card images have loaded

  Scenario: A featured page shows its title and introduction and opens the page
    Given the site has an info page "Camp guide" with the introduction "Pitch a tent"
    And the home page has the sections:
      | section    | title      | page       | url |
      | featured 1 | Camp guide | Camp guide |     |
    When I visit "/"
    Then I see the text "Pitch a tent"
    When I open the card "Camp guide"
    Then I am on "/camp-guide/"
    And I see the heading "Camp guide"

  Scenario: A featured external site opens the other site
    Given the home page has the sections:
      | section    | title  | page | url                         |
      | featured 1 | Badges |      | https://badges.example.com/ |
    When I visit "/"
    Then the card "Badges" links to "https://badges.example.com/"
    And the card images have loaded
