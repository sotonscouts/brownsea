Feature: Landing page
  A landing page introduces a section of the intranet: an introduction, a body of blocks, and an optional narrow
  sidebar. Which pages the child pages list leaves out is covered by unit tests; this checks what a visitor sees.

  Background:
    Given the intranet has a site
    And I am logged in

  Scenario: A landing page shows its title and introduction
    Given the site has a landing page "Camping" with the introduction "Everything for life under canvas"
    When I visit "/camping/"
    Then I see the heading "Camping"
    And I see the text "Everything for life under canvas"
    And the browser tab is titled "Camping"

  Scenario: The body shows its blocks in the order they were written
    Given the site has an info page "Policies" with the introduction "Our rules"
    And the site has a landing page "Camping"
    And the landing page "Camping" has the body:
      | section   | title            | page     | url                         |
      | heading 1 | Before you go    |          |                             |
      | text 1    | Check the weather |         |                             |
      | links 1   | Badges           |          | https://badges.example.com/ |
      | heading 2 | When you arrive  |          |                             |
    When I visit "/camping/"
    Then the landing page sections read:
      | Before you go     |
      | Check the weather |
      | Badges            |
      | When you arrive   |

  Scenario: Without a sidebar the body takes the full width
    Given the site has a landing page "Camping" with the introduction "Everything for life under canvas"
    When I visit "/camping/"
    Then the introduction spans the full width of the page
    And there is no sidebar

  Scenario: A sidebar sits beside the body on a wide screen
    Given the site has a landing page "Camping" with the introduction "Everything for life under canvas"
    And the landing page "Camping" has the sidebar:
      | block       | title  | page | url                         |
      | quick links | Badges |      | https://badges.example.com/ |
    When I visit "/camping/"
    Then the sidebar sits beside the body, which takes about two thirds of the page

  Scenario: On a phone the sidebar drops below the body
    Given I am using a phone
    And the site has a landing page "Camping" with the introduction "Everything for life under canvas"
    And the landing page "Camping" has the sidebar:
      | block       | title  | page | url                         |
      | quick links | Badges |      | https://badges.example.com/ |
    When I visit "/camping/"
    Then the sidebar sits below the body, and both take the full width

  Scenario: Quick links in the sidebar open pages and other sites
    Given the site has an info page "Policies"
    And the site has a landing page "Camping"
    And the landing page "Camping" has the sidebar:
      | block       | title  | page     | url                         |
      | quick links | Policy | Policies |                             |
      | quick links | Badges |          | https://badges.example.com/ |
    When I visit "/camping/"
    Then the sidebar quick links are:
      | Policies |
      | Badges   |
    And the sidebar link "Badges" goes to "https://badges.example.com/"
    When I click the sidebar link "Policies"
    Then I am on "/policies/"

  Scenario: The sidebar shows recent news and links to all of it
    Given the site has a news index
    And the news has the articles:
      | title | published  | type         |
      | One   | 2026-03-01 | Announcement |
      | Two   | 2026-03-02 | Announcement |
      | Three | 2026-03-03 | Announcement |
      | Four  | 2026-03-04 | Announcement |
    And the site has a landing page "Camping"
    And the landing page "Camping" has the sidebar:
      | block       | title | page | url |
      | recent news |       |      |     |
    When I visit "/camping/"
    Then the recent news is:
      | Four  |
      | Three |
      | Two   |
    When I click "View all news"
    Then I am on "/news/"

  Scenario: Child pages are listed, leaving out pages the landing page links to itself
    Given the site has a landing page "Camping"
    And the page "Camping" has the info pages:
      | title      | introduction  |
      | Tents      | Pitch up      |
      | Kit list   | Pack a bag    |
      | Campfires  | Stay safe     |
    And the landing page "Camping" has the body:
      | section    | title      | page     | url |
      | links 1    | Kit        | Kit list |     |
      | children 1 | Also here  |          |     |
    When I visit "/camping/"
    Then I see the cards:
      | Kit list  |
      | Tents     |
      | Campfires |
    When I open the card "Tents"
    Then I am on "/camping/tents/"
    And I see the heading "Tents"

  Scenario: A landing page loads without browser errors
    Given the site has an info page "Policies"
    And the site has a landing page "Camping"
    And the landing page "Camping" has the body:
      | section    | title    | page     | url |
      | links 1    | Policy   | Policies |     |
      | children 1 |          |          |     |
    And the landing page "Camping" has the sidebar:
      | block       | title  | page     | url |
      | quick links | Policy | Policies |     |
    When I visit "/camping/"
    Then the browser reported no errors
