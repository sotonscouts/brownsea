# Brownsea information architecture plan

The plan for how content on Brownsea is organised, labelled, found and governed. Status: **draft**. Companion documents:

- [page-types.md](page-types.md): the page types, their placement rules and status
- [example-structure.md](example-structure.md): worked examples of the page tree and of how listings work

Contents: [1. Goals](#1-goals) · [2. Principles](#2-principles) · [3. Site structure](#3-site-structure) ·
[4. Content areas](#4-content-areas) · [5. Navigation](#5-navigation) · [6. Classification](#6-classification) ·
[7. Search](#7-search) · [8. Access](#8-access) · [9. Editing and governance](#9-editing-and-governance) ·
[10. Roadmap](#10-roadmap) · [11. Scope and assumptions](#11-scope-and-assumptions)

---

## 1. Goals

1. People find the right guidance, event or contact quickly, from the navigation or from search.
2. Content is consistent. Each kind of content has one obvious page type with the fields it needs.
3. Editors, who are volunteers, can choose where a page goes and what type it is without training.
4. Everything is private unless someone decides otherwise, and sharing a page outside the team is easy and safe.
5. The structure works for a district today and for groups and county teams later, without being rebuilt.

## 2. Principles

1. **Structure and curation are separate.** The page tree gives stable URLs and breadcrumbs. The primary navigation
   and landing pages are curated by editors and organised around tasks, not around the tree.
2. **Collections are an index plus items.** News, Events and (later) Policies and Roles each have one index page
   that lists, filters and paginates, and item pages that may only live beneath it.
3. **Items live in one place and are listed elsewhere by filter.** A Cub event lives under Events and appears on the
   Cubs page through a filter, never as a copy.
4. **Placement is enforced in code**, with allowed parents and children for every page type, so structure does not
   depend on editor discipline.
5. **A new page type only when content has a recurring shape and its own fields.** Everything else is an Info page,
   a block or a snippet.
6. **Hubs curate, collections list.** Landing pages are hand-built entry points; indexes list automatically.
7. **Secure by default.** New pages inherit access from their parent, and the fallback is logged-in only.

## 3. Site structure

```
Home
├── News                   ArticlePages
├── Events                 EventPages (every event lives here)
├── Programme              Programme home → one page per section → guidance
├── Policies               (planned)
├── Volunteer roles        (planned)
├── Meet the team          People listing
├── Map                    Woodmill map
└── Hubs                   Landing pages for teams, venues and topics
    └── Guidance           Info, Process and Index pages, including wikis
```

Page types, parents and children are in [page-types.md](page-types.md). A worked example is in
[example-structure.md](example-structure.md).

**URLs** mirror the tree. These top-level paths are reserved and cannot be used as page slugs: `admin`,
`django-admin`, `accounts`, `documents`, `gis`, `search`, `magic-links`.

## 4. Content areas

The areas the site is organised around, with the page types that carry them. "Examples" are drawn from a district
intranet; groups and the county will populate the same types differently.

| Area | Examples | Page types |
| --- | --- | --- |
| News and communications | Monthly updates, announcements, project reports, urgent notices | News index, Article |
| Events | Camps, training, AGM, socials, venue sessions | Events index, Event |
| Programme and sections | Section pages, nights away permits, awards, programme ideas | Programme home, Programme section, Info, Process |
| Venue operations | Keys, utilities, bookings, pricing, invoicing, customer notes | Landing, Info, Process, Directory |
| Digital and IT | Accounts, email, domains, runbooks | Landing, Index, Info, Process |
| Governance and policy | Structure, policies, AGM papers, annual reports | Info, Index, Policies (planned) |
| Volunteering | Role descriptions, vacancies, onboarding | Roles (planned), Info |
| People and contacts | Team, role holders, who to ask | People listing |
| Directories | Suppliers, partners, venues | Directory |
| Resources | Templates, letters, forms, posters, reports, minutes | Info, with documents attached to the page they belong to |
| Support and requests | Hardship assistance, account requests, media services | Info, Process |
| Projects and campaigns | Woodmill redevelopment, Jamboree | Landing, plus filtered news and events |
| Help | About the hub, contact support, accessibility | Info |

Areas that may follow, once there is content for them: training catalogue, group profiles and a groups directory,
glossary, request forms. They are in the "Later" list in [page-types.md](page-types.md).

## 5. Navigation

| Element | Plan |
| --- | --- |
| **Primary navigation** | Curated, task-oriented, two levels (top link, then up to three columns in a mega menu). Maintained separately from the tree. |
| **Section navigation** | A local tree and previous/next links inside deep sections such as wikis, so people can move sideways without going back up. |
| **Breadcrumbs** | Derived from the tree. Show only ancestors the visitor can open. |
| **In-page navigation** | Automatic from headings on long pages. |
| **Filtered listings** | Home, hub and section pages list upcoming events and recent news by classification, with a "see all" link to the pre-filtered index. |
| **Landing pages** | Task tiles, featured sections, link sections and child lists for curated entry points. |
| **Footer** | Help, contact, about this site, accessibility. |
| **Alert banner** | Site-wide notices, paired with an urgent news type so they leave an archive. |
| **Search** | Always visible to signed-in users. See section 7. |

## 6. Classification

Content is classified once, where it lives, and listed elsewhere by filter. The taxonomies are being defined next.
The working set, each of which can apply to several page types:

| Dimension | Purpose | Applies to |
| --- | --- | --- |
| Audience or section | Who it is for (age section, adults, role) | Events, news, programme content, documents, and other guidance |
| Topic | What it is about | News, events, guidance |
| Type | What kind of item it is (news type, event type) | Per collection |

Rules: one shared set of values per dimension, managed in one place; every filter on a page uses the same vocabulary
as the classification on the items; filters carry through to the "see all" link.

## 7. Search

One site search, aimed at finding the right page rather than listing everything:

- Each result shows its type and where it lives (breadcrumb path).
- Filter by type, audience or section, and area.
- Results never list pages the visitor is not allowed to open.
- Documents and snippets are searchable alongside pages.
- Zero-result queries are logged so gaps in content and vocabulary show up.

## 8. Access

- Four levels per page: inherit, logged in only, public, magic link. Pages inherit from their parent; the fallback
  is logged-in only.
- Magic links give time-limited, revocable access to a single page for people outside the team.
- Visitors without an account see a coherent, minimal site: the pages they can open, breadcrumbs limited to
  ancestors they can open, and no dead ends.
- Special permissions (such as the restricted map data) are per feature and documented with it.

## 9. Editing and governance

- **Placement rules** on every page type, as in [page-types.md](page-types.md), so the add-page menu only offers
  sensible choices.
- **Page types guide** in the admin, grouped to match the page-type families, with a "choosing quickly" table.
- **One meaning for listing flags.** A single "show in listings" field decides whether a page appears in automatic
  lists, applied the same way by indexes, child-page lists and news.
- **One child-listing rule** shared by indexes and landing pages.
- **Slug validation** that rejects the reserved top-level paths.
- **Ownership and review.** Guidance pages get an owner and a review date, and a "due for review" report.
- **Integrity reports.** Pages not reachable from the navigation or a hub, and navigation links to unpublished
  pages.

## 10. Roadmap

A proposed order. Each step makes the next cheaper.

| Phase | Work | Result |
| --- | --- | --- |
| 1. Foundations | Placement rules for existing types; single listing rule and field; reserved-slug validation | The structure is safe to grow |
| 2. Classification | Define the taxonomies; apply them across page types | Items can be listed anywhere by filter |
| 3. Collections | Events index and Event pages; Programme home and section pages; Directory | The main content areas have a home |
| 4. Reworks | Process page; People listing with contact details; section navigation for wikis | Deep and procedural content is easier to use |
| 5. Search | Result context, facets, permission filtering, document search | Search finds the right thing |
| 6. Planned types | Policies; Volunteer roles and vacancies, once designed | Governance and volunteering content get dedicated layouts |
| 7. Governance | Ownership and review fields, review and integrity reports | The site stays accurate |

## 11. Scope and assumptions

- **Events** live only under the Events index and are listed elsewhere by classification.
- **Programme sections** start with a single section page type.
- **Index pages** stay, for wikis and sections that are simply a list.
- **Documents** are attached to the pages they belong to. A document library is added when volume justifies it.
- **Policies and Volunteer roles** are designed later and added as collections.
- **Scope:** built for the district first, with page types and classification kept general enough for groups and the
  county to adopt.
- **Access:** everything stays behind login to begin with. Public and magic-link content is introduced area by area.
- **External calendars** (such as Bookwhen) can be embedded on any page, and the Events index lists the district's
  own events.
- **Review cycle:** each guidance area has a named owner and an agreed review period, set when the ownership fields
  are introduced (phase 7).
