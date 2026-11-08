Feature: Index page
  An index page introduces a section and lists the pages in it.

  Background:
    Given the intranet has a site
    And the site has an index page "Camping"
    And I am logged in

  Scenario: An index page shows its title and introduction
    Given the page "Camping" has the introduction "Everything you need for a night under canvas"
    When I visit "/camping/"
    Then I see the heading "Camping"
    And I see the text "Everything you need for a night under canvas"

  Scenario: An index page lists the pages in its section
    Given the page "Camping" has the info pages:
      | title        | introduction                  |
      | Packing list | What to bring                 |
      | Tent pitching | How to put up a patrol tent |
    When I visit "/camping/"
    Then I see the child page cards:
      | Packing list  | What to bring                |
      | Tent pitching | How to put up a patrol tent  |

  Scenario: Each card opens its page
    Given the page "Camping" has the info pages:
      | title        | introduction  |
      | Packing list | What to bring |
    When I visit "/camping/"
    And I open the card "Packing list"
    Then I am on "/camping/packing-list/"
    And I see the heading "Packing list"

  Scenario: Pages are listed in the order they sit in the section
    Given the page "Camping" has the info pages:
      | title    | introduction |
      | Zebra    | Z            |
      | Aardvark | A            |
      | Mongoose | M            |
    When I visit "/camping/"
    Then I see the child page cards:
      | Zebra    | Z |
      | Aardvark | A |
      | Mongoose | M |

  Scenario: Pages hidden from menus are not listed
    Given the page "Camping" has the info pages:
      | title        | introduction |
      | Packing list | What to bring |
      | Secret plans | Not for you   |
    And the page "Secret plans" is hidden from menus
    When I visit "/camping/"
    Then I see the child page cards:
      | Packing list | What to bring |

  Scenario: Unpublished pages are not listed
    Given the page "Camping" has the info pages:
      | title        | introduction  |
      | Packing list | What to bring |
      | Draft        | Not ready     |
    And the page "Draft" is unpublished
    When I visit "/camping/"
    Then I see the child page cards:
      | Packing list | What to bring |

  Scenario: Only the pages directly in the section are listed
    Given the page "Camping" has an info page "Packing list"
    And the page "Packing list" has an info page "Sleeping bags"
    When I visit "/camping/"
    Then I see the child page cards:
      | Packing list | Introduction |

  Scenario: An empty section lists nothing
    When I visit "/camping/"
    Then I see the heading "Camping"
    And I see no child page cards

  Scenario: Long sections are split across pages
    Given index pages show 2 pages at a time
    And the page "Camping" has the info pages:
      | title | introduction |
      | One   | 1            |
      | Two   | 2            |
      | Three | 3            |
    When I visit "/camping/"
    Then I see the child page cards:
      | One | 1 |
      | Two | 2 |
    And I am on page 1 of the results
    When I click "Next" in the pagination
    Then I am on "/camping/?page=2"
    And I see the child page cards:
      | Three | 3 |
    And I am on page 2 of the results
    When I click "Previous" in the pagination
    Then I see the child page cards:
      | One | 1 |
      | Two | 2 |

  Scenario: A page number can be picked directly
    Given index pages show 1 pages at a time
    And the page "Camping" has the info pages:
      | title | introduction |
      | One   | 1            |
      | Two   | 2            |
      | Three | 3            |
    When I visit "/camping/"
    And I click "3" in the pagination
    Then I see the child page cards:
      | Three | 3 |
