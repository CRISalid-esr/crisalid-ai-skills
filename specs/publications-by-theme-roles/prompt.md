# `publications-by-theme` — contribution role allow-list — specification

## 1. Problem

`publications-by-theme` returns, for each matching document, every person linked to it through a `Contribution`
node, whatever `Contribution.roles` holds. A thesis therefore comes back with its advisor, its committee members,
its rapporteurs and its jury president next to its author, and callers that read "contributor" as "author" (the TRM
batch of `crisalid-agents`, an LLM answering "who wrote on this theme?") credit all of them with the document.

Roles are stored on the contribution as full LoC relator URIs (`http://id.loc.gov/vocabulary/relators/ths`),
several per contribution. Three groups matter for this tool, plus a fallback:

| Group | Codes |
|---|---|
| Authorship | `aut` (author, thesis authors included) |
| Editorial | `edt` (editor), `pbd` (publisher director), `sad` (scientific advisor), `aui` (author of introduction), `trl` (translator) |
| Thesis supervision and jury | `ths` (thesis advisor), `dgc` (degree committee member), `rap` (rapporteur), `opn` (opponent), `pra` (praeses, jury president) |
| Unspecified | `ctb` (LoC "contributor"): not a role in itself, the fallback the IKG writes when a source gives no role or an unrecognised one |

In an institution that harvests its theses, the third group is a large share of the contributions.

## 2. Change

One optional parameter on `publications-by-theme`, in `tools.yaml` and `tools-auth.yaml`:

```yaml
  - name: roles
    type: string
    description: <see §3>
    default: ""
```

- Comma-separated relator codes (the last segment of the URI: `aut`, `ths`…), the convention already used by
  `sources` and `uids` in this file and by the `roles` output of `list-person-top-documents`. A full URI is accepted
  and reduced to its last segment; values are trimmed and lower-cased; empty items are ignored.
- Empty (default): no role filter, the tool behaves exactly as today.
- Non-empty: an allow-list. A contribution matches when at least one of its roles is in the list.

Effects, mirroring `internal_only`:

1. **Document filter** — a document is kept only if it has at least one matching contribution. Combined with
   `internal_only = true`, the same contribution must satisfy both conditions (an internal person holding an allowed
   role): a thesis whose only internal contributor is its advisor is dropped with `roles = "aut"`.
2. **Returned contributors** — only the persons of matching contributions are returned.

The filter runs before `LIMIT`, so `limit` still counts kept documents. The output shape does not change:
`contributors[].roles` stays the full list of URIs of the contribution, including roles outside the allow-list.

### 2.1 Cypher

```cypher
CALL db.index.vector.queryNodes('embeddable_embedding', toInteger($limit) * 100, $semantic_theme_vector)
YIELD node AS literal, score
WHERE literal.embedding_status = 'success'
  AND literal.type IN (CASE WHEN $use_abstract
    THEN ['document_title', 'document_abstract']
    ELSE ['document_title'] END)
MATCH (doc:Document)-[:HAS_TITLE|HAS_ABSTRACT]->(literal)
WITH doc, max(score) AS best_score,
     [r IN split($roles, ',') WHERE trim(r) <> '' | toLower(split(trim(r), '/')[-1])] AS allowed_roles
WHERE ($internal_only = false AND size(allowed_roles) = 0)
  OR EXISTS {
    MATCH (doc)-[:HAS_CONTRIBUTION]->(c:Contribution)<-[:HAS_CONTRIBUTION]-(p:Person)
    WHERE ($internal_only = false OR p.external = false)
      AND (size(allowed_roles) = 0
           OR ANY(role IN c.roles WHERE split(role, '/')[-1] IN allowed_roles))
  }
ORDER BY best_score DESC
LIMIT $limit
```

`allowed_roles` is carried through the following `CALL` blocks and the contributors sub-query gets the same
predicate:

```cypher
CALL {
  WITH doc, allowed_roles
  OPTIONAL MATCH (doc)-[:HAS_CONTRIBUTION]->(contrib:Contribution)<-[:HAS_CONTRIBUTION]-(contributor:Person)
  WHERE ($internal_only = false OR contributor.external = false)
    AND (size(allowed_roles) = 0
         OR ANY(role IN contrib.roles WHERE split(role, '/')[-1] IN allowed_roles))
  RETURN collect(DISTINCT CASE WHEN contributor IS NOT NULL THEN { … } END) AS contributors
}
```

A contribution whose `roles` is null or empty never matches a non-empty allow-list.

## 3. Hints in the tool metadata

The parameter is filled by code (TRM) and by LLMs (the `crisalid-restricted` and `crisalid-unrestricted` toolsets
expose the tool to the generic agent). The LLM only knows the vocabulary through the tool metadata, so the hints
live there, not in an agent prompt. They list the codes of §1, and say which
list answers the usual question; the 300 other LoC relators are not listed.

Tool description, appended:

```
Each document comes with the people attached to it (`contributors`) and the
role(s) each one held, as LoC relator URIs: author, but also thesis advisor,
jury member, editor… Being listed does not make someone an author. Use
`roles` to keep only the roles you need.
```

Parameter description:

```
Comma-separated allow-list of role codes (LoC relators); empty keeps
every role. A document is kept only if at least one person holds one of
these roles on it, and only those people are returned.
Authorship: aut (author).
Editorial: edt (editor), pbd (publication director), sad (scientific
advisor), aui (author of introduction), trl (translator).
Thesis supervision and jury: ths (thesis advisor), dgc (committee
member), rap (rapporteur), opn (opponent), pra (jury president).
Unspecified: ctb is not a role in itself, it is the fallback recorded
when the source does not say which role the person held.
To find who wrote on a theme, use "aut,ctb" (authors, plus people whose
role is unspecified). Add "ths" to also count thesis supervision.
```

The wording keeps two things apart: the people attached to a document (the `contributors` field of the output,
whatever their role) and `ctb`, which the LoC vocabulary calls "contributor" but which is only the fallback for an
unspecified role. The metadata never uses "contributor" for the first meaning without that qualification.

## 4. Out of scope

- No default allow-list in the tool: the policy belongs to the caller (`TRM_CONTRIBUTOR_ROLES` in `crisalid-agents`).
- The Sorbobot tools (`list-concept-experts`, `list-person-research-concepts`, `list-person-top-documents`,
  `list-concept-expert-evidence`, `get-person-publication-counts`) keep their hard-coded `aut` / `ths` / `spk`
  list, which their specification asks for.
- `list-person-publications` and `get-publication` are unchanged.

## 5. Tests (`tests/test_mcp_toolbox_semantic_search_tools.py`)

Fixture (`tests/fixtures/graph.cypher`): the three contributions of `doc1` carry the legacy value `['AUTHOR']`. Give
them relator URIs so that `doc1` has an internal author, an internal thesis advisor and an external author — or add
a dedicated document with an embedded title if another test depends on the current values.

- empty `roles`: same rows and contributors as without the parameter;
- `roles = "aut"`: every returned contributor has the `aut` URI among its roles; the advisor is absent;
- `roles = "ths"`: only the advisor is returned;
- `roles = "aut, THS"` and a full URI: trimming, case and URI reduction;
- `roles = "aut"` with `internal_only = true`: only the internal author; a document whose only internal contributor
  is an advisor is not returned;
- `roles = "xyz"`: no row.

`tools.yaml` and `tools-auth.yaml` stay identical for this tool apart from `authRequired`.

## 6. Branches and commits

`crisalid-ai-skills`, branch `publications-by-theme-roles`:

0. `docs: publications-by-theme roles spec` — this file
1. `feat: roles allow-list on publications-by-theme` — both YAML files, fixture, tests, README tool table if it
   lists parameters

Paired with `crisalid-agents`, branch `trm-contributor-roles`, which passes the allow-list from TRM and filters
client-side when the deployed toolbox does not have the parameter yet.

## 7. Open question

`pbd`: which source role it is mapped from (probably the scientific editor of a collective volume) decides whether
it deserves a place next to `aut` in the callers' default lists.
