# Database Patterns

A guide covering architectural options for flexible, multi-level attribute systems with conditional logic, pricing, and formulas.

---

## Part 1: Core Architectural Patterns

### 1. Pure EAV (Entity-Attribute-Value)

The classic three-table pattern where everything becomes key-value pairs.

**How it works:** You create three core tables — Entities (your materials), Attributes (definitions like "hardness", "scale"), and Values (the actual data connecting entities to attributes). Every piece of data becomes a row in the Values table with a reference to both the entity and attribute.

**Structure concept:**

- `entities` table holds material records
- `attributes` table defines what properties exist
- `values` table stores triples: (entity_id, attribute_id, value)

**Query behavior:** To reconstruct a material with all its properties, you JOIN the values table multiple times or pivot the results. A material with 20 attributes requires fetching 20 rows from the values table.

| Pros | Cons |
| --- | --- |
| Maximum flexibility — add attributes without schema changes | Query performance degrades with depth ("JOIN hell") |
| Simple conceptual model | No native type safety — everything is typically stored as text |
| Works with any database | Hard to enforce referential integrity on values |
| Easy to add/remove attributes dynamically | Complex reporting and aggregation queries |

**Best for:** Simple attribute systems with few queries, shallow nesting, and when flexibility trumps performance.

---

### 2. JSONB Document Approach

Store the entire attribute tree as a JSON document in a single column.

**How it works:** Each material record contains a JSONB column that holds its complete attribute hierarchy. The structure mirrors your UI — nested objects represent nested attributes. PostgreSQL (or MongoDB) handles the storage and provides operators to query inside the JSON.

**Example structure:**

```json
{"hardness": {"selected": true, "scale": "Brinell", "value": 250}}

```

**Query behavior:** Fetching a material is a single-row read. Searching across materials requires JSON operators like `->`, `->>`, or `@>` in PostgreSQL, which can be indexed but behave differently than relational queries.

| Pros | Cons |
| --- | --- |
| Very fast reads — single row contains everything | Querying across materials requires JSON operators |
| Schema-less — structure can vary per record | No referential integrity within the JSON |
| Natural hierarchy representation | Schema validation must happen in application code |
| Easy versioning — snapshot the whole document | Can't easily JOIN JSON data with other tables |
| Supports deep nesting naturally | Updates to nested values can be verbose |

**Best for:** Read-heavy workloads, document-like data, when each record is relatively independent, and when you don't need to query/filter by deep attributes often.

---

### 3. Graph Database (Neo4j, Amazon Neptune)

Model materials, attributes, and relationships as nodes and edges in a graph.

**How it works:** Instead of tables, you create nodes (Material, Attribute, Value) and connect them with typed edges (HAS_ATTRIBUTE, HAS_OPTION, DEPENDS_ON). Traversing relationships is a first-class operation — you can query "all attributes 3 levels deep" naturally.

**Structure concept:**

```
(Material:Steel) -[:HAS_ATTRIBUTE]-> (Hardness)
(Hardness) -[:HAS_OPTION]-> (Scale:Brinell)
(Scale:Brinell) -[:HAS_DETAILS]-> (TestLoad:3000)

```

**Query behavior:** Graph queries (Cypher in Neo4j) express traversals directly. Finding all descendants or checking relationship chains is natural and fast, regardless of depth.

| Pros | Cons |
| --- | --- |
| Perfect for hierarchical and network relationships | Different technology stack to learn and deploy |
| Traversal is natural and fast at any depth | Team learning curve for Cypher/Gremlin |
| Flexible relationship types with properties | Less mature tooling than SQL ecosystems |
| Visual representation matches mental model | Deployment and operational complexity |
| Can model conditional logic as relationship properties | Overkill if relationships are simple trees |

**Best for:** Complex multi-level relationships, when traversal patterns are core to your application, or when relationships themselves carry significant meaning/data.

---

### 4. Hybrid Relational + JSONB

Use relational tables for structure and metadata, JSONB for flexible instance data.

**How it works:** You maintain relational tables for material types and attribute definitions (the "schema"), but store actual instance values in a JSONB column on the materials table. The relational layer defines what's possible; the JSONB stores what was chosen.

**Structure concept:**

- `material_types` — relational, defines types
- `attribute_definitions` — relational, defines the attribute tree structure
- `materials` — has a `data JSONB` column for instance-specific values

**Query behavior:** You can query the schema relationally (fast, indexed, JOINable) and query instance data with JSON operators. Validation compares JSONB data against relational schema definitions.

| Pros | Cons |
| --- | --- |
| Balance of structure and flexibility | More complex than pure approaches |
| Query both ways — SQL for schema, JSON for data | Must maintain consistency between schema and data |
| Schema enforcement without rigidity | Two mental models to manage |
| Good performance for most use cases | JSON queries less intuitive than relational |

**Best for:** Systems needing both flexibility and structure, medium complexity, when you want admin-editable schemas with flexible instance data.

---

### 5. Closure Table

Store all ancestor-descendant relationships in a dedicated table with depth tracking.

**How it works:** In addition to your main attributes table, you maintain a separate table that stores every possible ancestor-descendant pair. If A→B→C→D is your hierarchy, the closure table stores (A,B,1), (A,C,2), (A,D,3), (B,C,1), (B,D,2), (C,D,1) plus self-references.

**Structure concept:**

- `attributes` — your nodes with their data
- `attribute_closure` — (ancestor_id, descendant_id, depth)

**Query behavior:** Finding all descendants or ancestors is a single indexed query — no recursion needed. "Get entire subtree" becomes `WHERE ancestor_id = X`. "Get all ancestors" becomes `WHERE descendant_id = X`.

| Pros | Cons |
| --- | --- |
| O(1) subtree and ancestor queries | Storage overhead — stores all path combinations |
| No recursive CTEs needed | Insert/delete requires updating closure table |
| Can query any level efficiently | Moving nodes is complex (rebuild paths) |
| Well-understood, documented pattern | Doesn't naturally represent conditional logic |

**Best for:** Deep hierarchies with frequent subtree queries, when read performance is critical and structure changes are infrequent.

---

### 6. PostgreSQL LTREE

Use PostgreSQL's native hierarchical data type for path-based storage.

**How it works:** LTREE is a PostgreSQL extension that stores hierarchical labels as dot-separated paths (like `metal.hardness.scale.brinell`). It provides specialized operators and GiST indexes for hierarchical queries.

**Structure concept:**

- Each node has a `path LTREE` column
- Paths look like: `'root.category.subcategory.item'`

**Query behavior:** Use operators like `@>` (ancestor of), `<@` (descendant of), `~` (regex match), `?` (contains label). Queries like "all descendants of hardness" become `WHERE path <@ 'metal.hardness'`.

| Pros | Cons |
| --- | --- |
| Built into PostgreSQL — no extra infrastructure | PostgreSQL-specific (vendor lock-in) |
| Very fast hierarchical queries with GiST index | Path updates cascade to all descendants |
| Pattern matching on paths | Less flexible for conditional/dynamic logic |
| Supports label-based queries | Path strings can become unwieldy at depth |

**Best for:** PostgreSQL-only environments, when paths are relatively stable, and when you need fast hierarchical queries without closure table overhead.

---

### 7. Nested Sets

Store left/right boundaries for efficient tree traversal.

**How it works:** Each node gets `lft` and `rgt` integer values representing a pre-order traversal of the tree. A node's descendants all have `lft` and `rgt` values between the parent's values. The root might be (1, 20), its first child (2, 9), and so on.

**Structure concept:**

- Each node has `lft INTEGER` and `rgt INTEGER`
- Descendants: `WHERE lft > parent.lft AND rgt < parent.rgt`

**Query behavior:** Finding all descendants is a single range query — extremely fast. Finding ancestors requires `WHERE lft < node.lft AND rgt > node.rgt`. No recursion needed.

| Pros | Cons |
| --- | --- |
| Lightning-fast subtree reads | Insert/delete requires renumbering many nodes |
| Single query for entire subtrees | Not suitable for frequently changing trees |
| Efficient ancestor queries | Move operations are expensive |
| Low storage overhead | Counter-intuitive to reason about |

**Best for:** Read-heavy hierarchies that rarely change structure, category trees, menu systems.

---

### 8. Materialized Path

Store the full path to each node as a string or array.

**How it works:** Each node stores its complete ancestry as a path string (`"1/4/7/12"` or `"metal.hardness.scale"`) or an array. You can query paths using string operations (LIKE, prefix matching) or array operators.

**Structure concept:**

- Each node has `path VARCHAR` or `path TEXT[]`
- Parent is derived from path (all but last segment)

**Query behavior:** Descendants of node X are all nodes whose path starts with X's path. Ancestors are derived by splitting the path. Moving a node requires updating all descendant paths.

| Pros | Cons |
| --- | --- |
| Simple to understand | Path updates cascade to all descendants |
| Fast descendant queries (prefix matching) | String manipulation overhead |
| Easy to get full ancestry | Path length limits (if using VARCHAR) |
| Works with any database | No specialized index support in most DBs |

**Best for:** Moderate hierarchies where nodes rarely move, when you need human-readable paths, and when you don't have PostgreSQL's LTREE.

---

### 9. Configuration as Code + Database

Define attribute schemas in versioned config files (YAML/JSON), store only instance data in DB.

**How it works:** Your attribute tree definitions live in version-controlled files (e.g., `schemas/metal.yaml`). A build/deploy process syncs these to the database. The database stores material instances and their values, but the "shape" of the data comes from code.

**Structure concept:**

- Git repo contains YAML schema definitions
- CI/CD syncs schemas to `attribute_definitions` table
- `materials` table stores instance data referencing schema

**Query behavior:** Standard relational queries. Schema changes go through code review and deployment rather than admin UI edits.

| Pros | Cons |
| --- | --- |
| Version-controlled schema with full history | Schema changes require deployments |
| Easy to review and validate changes | Less dynamic — can't add attributes on the fly |
| Schema evolution is explicit and tracked | Need build process to sync config to DB |
| Good for developer-centric workflows | Non-technical users can't modify schema |

**Best for:** Teams with strong DevOps, when schema changes should be deliberate and reviewed, when you want infrastructure-as-code principles.

---

### 10. Event Sourcing

Store all attribute changes as events, reconstruct current state by replaying.

**How it works:** Instead of storing current state, you store a log of all changes: "attribute added", "value changed", "node moved". Current state is derived by replaying events. You can cache current state in materialized views.

**Structure concept:**

- `attribute_events` table: (entity_id, event_type, attribute_path, data, timestamp)
- Current state reconstructed by replaying or cached in snapshots

**Query behavior:** Queries hit the materialized current state. Historical queries replay events to a point in time. Audit queries scan the event log directly.

| Pros | Cons |
| --- | --- |
| Complete audit history automatically | Query complexity — must replay for current state |
| Can reconstruct any point in time | Storage overhead (events accumulate forever) |
| Great for debugging and compliance | Eventual consistency challenges |
| Natural fit for undo/redo features | Overkill for simple CRUD applications |

**Best for:** When audit trail is critical, temporal queries are needed, regulatory compliance matters, or you need time-travel debugging.

---

### 11. Triple Store / RDF

Store everything as subject-predicate-object triples.

**How it works:** Every fact becomes a triple: `(Steel, hasHardness, 250)`, `(Steel, rdf:type, Metal)`, `(Hardness, hasScale, Brinell)`. You query using SPARQL, a graph pattern matching language. Triples can reference other triples, enabling complex relationships.

**Structure concept:**

- Single table: (subject, predicate, object)
- Or dedicated triple store (Virtuoso, Stardog, Amazon Neptune)

**Query behavior:** SPARQL queries express graph patterns. "Find all metals with hardness > 200" becomes a pattern match across connected triples.

| Pros | Cons |
| --- | --- |
| Maximum flexibility — can represent anything | Very niche technology |
| Standards-based (RDF, SPARQL, OWL) | Complex query language |
| Can represent any relationship type | Steep learning curve |
| Semantic reasoning capabilities | Limited tooling compared to SQL |

**Best for:** Semantic web applications, knowledge graphs, academic/research settings, when you need inference and ontology support.

---

### 12. Multi-Table Type-Specific (Traditional)

Separate tables for each material type with fixed columns.

**How it works:** Each material type gets its own table with typed columns: `metals(id, name, hardness, conductivity)`, `woods(id, name, grain, moisture)`. Properties are columns, not rows.

**Structure concept:**

- `metals` table with metal-specific columns
- `woods` table with wood-specific columns
- Possibly a `materials` parent table for shared fields

**Query behavior:** Standard, fast relational queries. Type-specific indexes. JOINs work naturally.

| Pros | Cons |
| --- | --- |
| Fast, indexed queries | Schema changes required for new types/attributes |
| Full type safety | Can't handle dynamic nesting |
| Referential integrity | Rigid — adding attributes means migrations |
| Traditional, well-understood | Polymorphic queries across types are awkward |

**Best for:** Fixed, well-known schemas where types and attributes are stable, when performance and type safety matter more than flexibility.

---

## Part 2: Database vs Application Layer

The fundamental architectural decision: where does the complexity live?

### Approach A: Database-Heavy (Smart DB, Thin ORM)

**Philosophy:** The database enforces structure, relationships, and logic. The application layer (ORM) is just a thin data mapper.

**Implementation characteristics:**

- Complex SQL views that flatten hierarchies
- Database triggers maintain derived data (like LTREE paths)
- Stored procedures encapsulate business logic
- CHECK constraints validate data
- Foreign keys everywhere for integrity
- Materialized views for performance

**How it plays out:** When you insert a node, a trigger automatically updates paths, recalculates depths, and validates conditions. The application just calls INSERT and trusts the database.

| Pros | Cons |
| --- | --- |
| Data integrity at database level | Vendor lock-in to specific DB |
| Same rules apply from any language/app | Hard to unit test (need real DB) |
| Centralized logic — one source of truth | Migrations are complex |
| Database optimizer can work better | Team needs strong SQL expertise |
| Can use DB from Python, Go, JS, etc. | Debugging stored procedures is harder |

---

### Approach B: ORM-Heavy (Smart App, Simple DB)

**Philosophy:** The database is just storage. All logic, validation, and business rules live in Python/application classes.

**Implementation characteristics:**

- Simple tables with basic columns
- Logic in ORM model methods
- Relationships computed in application code
- Business rules in service classes
- Application-level caching
- Pydantic/dataclasses for validation

**How it plays out:** The database has a simple `parent_id` column. Your Python class has a `get_descendants()` method that recursively fetches children. Path computation, validation, and conditional logic all live in Python.

| Pros | Cons |
| --- | --- |
| Easy to unit test (mock the DB) | Performance can suffer (N+1 queries) |
| Database-agnostic (switch to MySQL easily) | No database-level integrity |
| Idiomatic Python/Ruby/JS code | Logic not available to other apps hitting the DB |
| Easier refactoring with IDE support | Must be careful about consistency |
| Business logic in one place (codebase) | Complex queries may need raw SQL anyway |

---

## Part 3: ORM Implementation Patterns

### Pattern 1: Pure ORM Adjacency List

**Approach:** Simple parent-child references using ORM relationships. Each node has `parent_id` and the ORM defines `children` and `parent` relationships.

**How it works:** You define a self-referential foreign key and let SQLAlchemy/Django handle the relationship loading. Tree traversal is done through recursive Python methods or eager loading.

**Complexity:** Medium
**Performance:** Good for shallow trees, degrades with depth
**Flexibility:** High — JSONB columns can add metadata
**Testability:** Excellent — easy to mock and unit test

**Best for:** 3-5 levels of nesting, simple conditional logic, standard ORM-based applications.

---

### Pattern 2: ORM + JSONB Hybrid

**Approach:** Relational tables for structure (types, attribute definitions), JSONB for instance data (actual values).

**How it works:** Your `MaterialType` model has a `schema JSONB` defining the attribute tree. Your `Material` model has a `data JSONB` storing values. Python methods navigate and validate against the schema.

**Complexity:** Medium-High
**Performance:** Excellent for reads (single row)
**Flexibility:** Very high — schema is data, not DDL
**Testability:** Good — can test with in-memory dicts

**Best for:** PostgreSQL environments, when schema is admin-editable, flexible instance data with validated structure.

---

### Pattern 3: Treebeard/MP_Node Style

**Approach:** Use proven tree libraries that implement materialized path or nested sets behind the scenes.

**How it works:** In Django, you inherit from `MP_Node` (materialized path) or `NS_Node` (nested sets). The library handles path computation, tree operations, and provides methods like `get_descendants()`, `get_ancestors()`, `move()`.

**Complexity:** Low — library handles complexity
**Performance:** Excellent — optimized implementations
**Flexibility:** Medium — follows library conventions
**Testability:** Good — library is well-tested

**Best for:** Django projects, when you want battle-tested tree operations without building them yourself.

---

### Pattern 4: Pure Python Dataclasses

**Approach:** Define your domain model entirely in Python dataclasses. Database is just a persistence layer that serializes/deserializes these objects.

**How it works:** You create `@dataclass` classes for `AttributeDefinition`, `Condition`, `ValidationRule`, `Material`. These have methods for traversal, validation, conditional logic. A separate repository layer handles DB persistence (often as JSON).

**Complexity:** High — you build everything
**Performance:** Depends on how you persist
**Flexibility:** Maximum — no constraints from DB or ORM
**Testability:** Excellent — pure Python, no DB needed

**Best for:** Complex domain logic, when you want clean separation of concerns, or when the same model must work with multiple storage backends.

---

## Part 4: Comparison Matrices

### Overall Pattern Comparison

| Approach | Complexity | Read Perf | Write Perf | Flexibility | Testability | DB Independence |
| --- | --- | --- | --- | --- | --- | --- |
| Pure EAV | Low | Poor | Good | Maximum | Good | High |
| JSONB Document | Low | Excellent | Good | Very High | Good | Low (Postgres) |
| Graph DB | High | Excellent | Good | Very High | Medium | Low |
| Hybrid Relational+JSONB | Medium | Excellent | Good | High | Good | Low (Postgres) |
| Closure Table | Medium | Excellent | Medium | Medium | Good | High |
| LTREE | Medium | Excellent | Medium | Medium | Good | Low (Postgres) |
| Nested Sets | Medium | Excellent | Poor | Medium | Medium | High |
| Materialized Path | Low | Good | Medium | Medium | Good | High |

### Hierarchy Operation Comparison

| Approach | Insert | Delete | Move Node | Get Descendants | Get Ancestors | Get Depth |
| --- | --- | --- | --- | --- | --- | --- |
| Adjacency Only | ✅ Easy | ✅ Easy | ✅ Easy | ❌ Slow (recursive) | ❌ Slow | ❌ Compute |
| LTREE Only | ⚠️ Build path | ⚠️ Update children | ❌ Complex | ✅ Fast | ✅ Fast | ✅ From path |
| Closure Table | ⚠️ Insert rows | ⚠️ Delete rows | ❌ Rebuild | ✅ Fast | ✅ Fast | ✅ Stored |
| Nested Sets | ❌ Renumber | ❌ Renumber | ❌ Renumber | ✅ Fast | ✅ Fast | ✅ Stored |
| Hybrid (Adj+LTREE) | ✅ Easy | ✅ Easy | ⚠️ Sync both | ✅ Fast | ✅ Fast | ✅ Stored |

---

## Part 5: The Hybrid Approach (Recommended)

Combining **Adjacency List + LTREE + Depth Cache** provides the optimal balance for most hierarchical data systems.

### What You Maintain

| Component | Column | Purpose |
| --- | --- | --- |
| Adjacency List | `parent_node_id` | Easy parent-child operations, intuitive inserts/deletes |
| Materialized Path | `ltree_path` | Fast hierarchical queries without recursion |
| Depth Cache | `depth` | Quick level filtering, no computation needed |

### Why This Works

**Adjacency List gives you:**

- Simple inserts — just set `parent_id`
- Cascade deletes via foreign keys
- Easy re-parenting — update one field
- Intuitive for developers

**LTREE gives you:**

- Fast descendant queries: `WHERE path <@ 'metal.hardness'`
- Fast ancestor queries: `WHERE 'metal.hardness.scale' <@ path`
- Pattern matching: `WHERE path ~ '*.scale.*'`
- No recursive CTEs needed

**Cached depth gives you:**

- Quick "get all level-2 attributes" queries
- No computation at query time

### The Tradeoff

You must keep adjacency and LTREE in sync. When moving a node, you update:

1. `parent_node_id` (the adjacency pointer)
2. `ltree_path` (the materialized path)
3. `depth` (the level cache)
4. All descendants' `ltree_path` values

**Solution:** Database triggers automatically maintain LTREE and depth when `parent_node_id` changes.

---

## Part 6: Key Design Considerations

### For Deep Hierarchies (10+ levels)

- **Avoid pure adjacency list** — recursive queries become expensive
- **Use LTREE or Closure Table** — both handle depth efficiently
- **Cache depth values** — prevents repeated computation
- **Consider hybrid approaches** — combine adjacency for writes, LTREE for reads
- **Index your path columns** — GiST indexes for LTREE, btree for closure tables

### For Dynamic Pricing & Formulas

- **Store formulas as text** — `"base_price * load_factor * 1.1"`
- **Evaluate in application layer** — use a safe expression parser
- **Use `price_contribution` field** — for simple additive pricing
- **JSONB for complex configurations** — when formulas need parameters
- **Consider caching computed prices** — if calculation is expensive

### For Conditional Display Logic

- **JSONB conditions** — `{"operator": "equals", "field": "parent.scale", "value": "Brinell"}`
- **Evaluate conditions in app layer** — keep logic testable
- **Support multiple condition types** — equals, contains, greater_than, exists, and, or
- **Store conditions on child nodes** — "when should I appear?" rather than "what are my children?"

### For Searchability

- **Typed value columns** — `value_string`, `value_number`, `value_boolean` enable proper indexing
- **Index specific JSON paths** — `CREATE INDEX ON materials ((data->>'hardness'))`
- **Composite indexes** — `(attribute_id, value_number)` for filtered queries
- **Full-text search** — PostgreSQL `tsvector` for text attributes
- **Consider search infrastructure** — Elasticsearch for complex queries at scale

---

## Part 7: Decision Framework

### Choose Adjacency List when:

- Frequent inserts and deletes
- Hierarchy is shallow (< 5 levels)
- Working with ORMs that support self-referential relationships
- Simplicity is more important than query performance

### Choose LTREE when:

- Using PostgreSQL (required)
- Complex hierarchical queries are common
- Path-based access patterns
- Need pattern matching on paths

### Choose Closure Table when:

- Deep hierarchies (10+ levels)
- Frequent "get all descendants" queries
- Database-agnostic solution needed
- Structure changes are infrequent

### Choose JSONB when:

- Schema varies significantly between records
- Read-heavy workload
- Document-like, self-contained data
- You rarely query/filter by deep nested values

### Choose Nested Sets when:

- Read-heavy with rare writes
- Need fastest possible subtree queries
- Structure is essentially static

### Choose Hybrid when:

- Need both flexibility AND performance
- Complex conditional logic requirements
- Long-term maintainability matters
- Different access patterns (fast reads, easy writes)

---

## Note

**"Enhanced EAV with Recursive + LTREE"** and **"Hybrid (Adjacency + LTREE)"** refer to the same architectural pattern:

| Term | What it describes |
| --- | --- |
| **Adjacency List** | The `parent_node_id` foreign key creating parent-child relationships |
| **Recursive** | Same thing — "recursive" refers to the self-referential nature of adjacency list |
| **LTREE** | The materialized path column using PostgreSQL's LTREE extension |
| **Enhanced EAV** | Adding rich metadata (pricing, formulas, conditions) to the attribute nodes |

So the full pattern combines:

- **Adjacency/Recursive** — `parent_node_id INTEGER REFERENCES attribute_nodes(id)`
- **LTREE** — `ltree_path LTREE` for fast hierarchical queries
- **EAV-style flexibility** — attributes defined as data rows, not schema columns
- **Rich node metadata** — JSONB for conditions, validation rules, pricing, formulas

The original document used different terminology in different sections, but they converge on the same recommended approach. I should have made this clearer in the consolidated guide.

---

## Summary

The optimal pattern for flexible hierarchical data typically combines:

1. **Relational structure** — for integrity and relationships
2. **LTREE or Closure Table** — for efficient tree queries
3. **JSONB** — for flexible conditions, formulas, and metadata
4. **Cached depth** — for quick level-based filtering
5. **Database triggers** — for automatic synchronization

This architecture provides the flexibility of document stores with the query power of relational databases, supporting complex pricing, formulas, and hierarchical requirements without schema changes for new attributes or types.

The key insight: **you don't have to choose just one pattern**. The most robust solutions combine patterns strategically — using each where it excels while triggers or application logic keeps them synchronized.