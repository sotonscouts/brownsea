# Target page types

The page types for Brownsea, their purpose and where each can live. Part of the plan in
[information-architecture.md](information-architecture.md). Taxonomies (audience, section, topic, and so on) are
defined separately, so the "filters" mentioned below are placeholders for them.

**Status key:** **Exists** = on `main` as is · **Rework** = exists but needs changes · **New** = to build, design
agreed · **Planned** = wanted, but not yet designed (the fields and purpose shown are indicative only) ·
**Later** = wanted, not yet.

## Design rules

1. **Collections are an index plus items.** News already works this way: one singleton index page (listing, filters,
   pagination) with item pages that may only live beneath it. Events, Policies and Roles/Vacancies follow the same
   pattern, so editors and visitors learn one shape.
2. **Items live in one place and are shown elsewhere through filtered listings.** An event for Cubs lives under the
   Events index and appears on the Cubs section page through a filtered "upcoming events" block, exactly as recent
   news does today. That keeps the tree shallow and URLs stable, and is why taxonomies matter next.
3. **Hubs curate, collections list.** Landing pages stay hand-curated entry points. Collection indexes list
   automatically.
4. **Placement is constrained in code** (`parent_page_types` / `subpage_types`), so structure does not depend on
   editor discipline.
5. **A new page type only when the content has a recurring shape and its own fields.** Everything else is an Info
   page, a block or a snippet.

## Target tree

```
Root (hidden)
└── HomePage                                   Exists
    ├── NewsIndexPage                          Exists, singleton
    │   └── ArticlePage
    ├── EventsIndexPage                        New, singleton
    │   └── EventPage
    │       └── InfoPage / ProcessPage         (event sub-pages: code of conduct, arrivals, costs)
    ├── ProgrammeHomePage                      New, singleton
    │   ├── ProgrammeSectionPage               New (Squirrels, Beavers, Cubs, Scouts, Explorers, Network)
    │   │   └── InfoPage / ProcessPage / IndexPage
    │   └── InfoPage / ProcessPage / LandingPage   (programme-wide: nights away permits, top awards)
    ├── Roles / vacancies                      Planned (to be designed)
    ├── Policies                               Planned (to be designed)
    ├── PersonListingPage                      Rework, singleton ("Meet the team")
    ├── GISPage                                Exists, singleton
    └── LandingPage                            Exists: Support, Woodmill, Digital Services, project hubs
        └── LandingPage / InfoPage / IndexPage / ProcessPage / DirectoryPage
            └── InfoPage / ProcessPage / IndexPage ... (wikis)
```

## Catalogue

### Site and structure

| Page type | Status | Purpose | Parents | Children |
| --- | --- | --- | --- | --- |
| `HomePage` | Exists | The front door: introduction, search, featured sections, recent news, and (new) upcoming events. | Root only | News index, Events index, Programme home, Person listing, GIS, Landing (plus the planned policy and role types) |
| `LandingPage` | Exists | A curated hub that sends people elsewhere: a team, a topic, a sub-site (Woodmill, Digital Services). Hand-built from tiles, sections and a child-pages block. | Home, Landing, Programme home | Landing, Info, Index, Process, Directory |
| `IndexPage` | Exists | An introduction plus an automatic list of child pages. Use it for wikis and sections that are simply a list, where nothing needs curating. Use a Landing page when the links should be chosen and ordered. | Info, Landing | Info, Process, Index |

### Everyday content

| Page type | Status | Purpose | Parents | Children |
| --- | --- | --- | --- | --- |
| `InfoPage` | Exists | The general content page: guidance, how-to, reference. Stays deliberately generic; anything with its own fields should move to a specific type. | Landing, Info, Index, Programme home, Programme section, Event | Info, Process, Index |
| `ProcessPage` | **Rework** | A step-by-step procedure that must be followed in order ("Invoice a booking", "Request an account"). Rework to add prerequisites and outcome, allow a link back to the parent, and be allowed under Info and Event pages. | Landing, Info, Index, Programme section, Event | None |
| `DirectoryPage` | **New** | A filterable list of similar records held as snippets: suppliers (recommended or avoid), partners, venues. Replaces prose lists such as the Supplier Directory. Records are snippets, not pages, so it does not multiply page types. | Landing, Info | None |

### Collections (index plus items)

| Page type | Status | Purpose | Parents | Children |
| --- | --- | --- | --- | --- |
| `NewsIndexPage` | Exists | Faceted, paginated list of news. Singleton. | Home | Article |
| `ArticlePage` | Exists | A news item: update, announcement, project report, urgent notice. | News index | None |
| `EventsIndexPage` | **New** | Upcoming and past events as a list with a calendar view, filterable. Singleton. May also show external calendar feeds (see below). | Home | Event |
| `EventPage` | **New** | One event: dates, venue, who it is for, cost, sign-up link, status (open, full, cancelled). **Every event lives under the Events index**, and other pages list events by taxonomy. Can act as a hub for a multi-page event such as District Camp 2027, whose code of conduct, arrivals and costs pages become its children. | Events index only | Info, Process |
| Policies | **Planned** | A place for formal documents with governance metadata (owner, version, status, review date). To be designed: whether this is an index plus item type, one type, or an extension of the Info page. Indicative placement: under Home, following the collection pattern. | Home (indicative) | To be designed |
| Roles and vacancies | **Planned** | Volunteer roles and the openings for them. To be designed: whether role descriptions and vacancies are one type or two, and how they relate to the people listing. Indicative placement: under Home, following the collection pattern. | Home (indicative) | To be designed |

### Programme

| Page type | Status | Purpose | Parents | Children |
| --- | --- | --- | --- | --- |
| `ProgrammeHomePage` | **New** | The home of everything programme-related: introduction, the sections laid out as tiles by age, programme-wide tools (nights away permits, top awards, activity approval), and filtered news and events for programme. Singleton. | Home | Programme section, Info, Process, Landing |
| `ProgrammeSectionPage` | **New** | One age section (Squirrels, Beavers, Cubs, Scouts, Explorers, Network). Standard sections: who it is for (age range), the programme and badges, forms and resources, local contacts, and filtered news and events for that section. Replaces hand-built Info pages per section. A fixed, consistent layout is the point. **Start with this one type for every section**; add more only if a section proves to need a different shape. | Programme home | Info, Process, Index |

### People and places

| Page type | Status | Purpose | Parents | Children |
| --- | --- | --- | --- | --- |
| `PersonListingPage` | **Rework** | "Meet the team": people in groups. Rework to add contact details and responsibilities, and let a person link to the role they hold. Today it holds name, role and photo only. Singleton. | Home, Landing | None |
| `GISPage` | Exists | The Woodmill map (Woodmap viewer, permission-scoped token). Singleton. | Home, Landing | None |

## Content with no page type, and why

| Content | Handled by |
| --- | --- |
| Urgent notices (storm, cancellation) | News article with an urgent news type, plus the existing alert banner. No new type |
| Project or campaign hubs (Woodmill redevelopment, Jamboree) | Landing page + filtered news and events + documents. Revisit if two or more projects want a status or timeline |
| FAQs | Accordion blocks in an Info page |
| External calendars (Fishing at Woodmill) | A block or snippet that embeds a feed on any page, so it does not need its own page type. This, plus the Events index, replaces the old `CalendarPage` |
| Forms and requests | Embed block inside an Info or Process page for now |
| Section pages for other audiences (Groups, Network, Adults) | Same `ProgrammeSectionPage` if they have the same shape, otherwise Landing |

## Later (wanted, not yet)

| Page type | Purpose | Why later |
| --- | --- | --- |
| `GroupPage` + Groups index | A Scout Group profile: meeting times, location, section list, contact, waiting list status | Depends on data ownership and whether groups share this site |
| `TrainingIndexPage` + `CoursePage` | Training catalogue with dates and links | Content not on the site yet |
| `FormPage` | Wagtail form-builder request forms with consistent "who can use this / what happens next" | Only if embedded Google Forms become a problem |
| `GlossaryPage` | Scouting jargon (GSL, DC, ADC) | Low cost and low urgency; could be an Info page first |
| `DocumentLibraryPage` | A browsable, filterable list of documents (type, year, audience): reports, minutes, templates | Documents are attached to the pages they belong to until volume justifies a library |
| `MeetingPage` | Agenda and minutes per meeting | Documents on an Info page are enough for now |

## Summary counts

| | Count |
| --- | --- |
| Exists, unchanged | `HomePage`, `LandingPage`, `IndexPage`, `InfoPage`, `NewsIndexPage`, `ArticlePage`, `GISPage` (7) |
| Rework | `ProcessPage`, `PersonListingPage` (2) |
| New | `EventsIndexPage`, `EventPage`, `ProgrammeHomePage`, `ProgrammeSectionPage`, `DirectoryPage` (5) |
| Planned (to be designed) | Policies, roles and vacancies |

The collection pattern keeps new types looking alike, and the "Page types" help screen in the admin is grouped to
match.

## Approach

- **Events:** every event lives under the Events index. Other pages (programme sections, the home page, landing
  pages) list events by classification, the same way recent news works.
- **Programme sections:** one `ProgrammeSectionPage` type for every section. More types are added only if a section
  needs a different shape.
- **Index pages:** `IndexPage` stays for wikis and plain section lists.
- **Documents:** attached to the pages they belong to. A document library is added when there are enough documents
  to need browsing.
- **Policies and roles:** designed later and added as collections, following the same pattern as news and events.
