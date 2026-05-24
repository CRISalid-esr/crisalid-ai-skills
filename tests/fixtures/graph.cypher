CREATE (p:Person {uid: 'local-jdurand@univ-domain.edu', display_name: 'Jeannette Durand', display_name_variants: [], external: false})

CREATE (i1:AgentIdentifier {type: 'local', value: 'jdurand@univ-domain.edu'})
CREATE (i2:AgentIdentifier {type: 'idref', value: '012345678'})
CREATE (i3:AgentIdentifier {type: 'orcid', value: '0000-0001-2345-6789'})

MERGE (p)-[:HAS_IDENTIFIER]->(i1)
MERGE (p)-[:HAS_IDENTIFIER]->(i2)
MERGE (p)-[:HAS_IDENTIFIER]->(i3)

CREATE (rs:OrganizationUnit:Unit:ResearchUnit {uid: 'local-ru-123456', generic_type: 'unit', national_type: 'UMR', external: false})
CREATE (rsi1:AgentIdentifier {type: 'local', value: '123456'})
CREATE (rs_ll:Literal {language: 'fr', value: 'Laboratoire de recherche en astrophysique', type: 'organization_long_label'})
CREATE (rs_sl:Literal {language: 'fr', value: 'LRA', type: 'organization_short_label'})

MERGE (rs)-[:HAS_IDENTIFIER]->(rsi1)
MERGE (rs)-[:HAS_LONG_LABEL]->(rs_ll)
MERGE (rs)-[:HAS_SHORT_LABEL]->(rs_sl)

MERGE (p)-[:MEMBER_OF]->(rs)

CREATE (inst:OrganizationUnit:Institution {uid: 'local-inst-234567', generic_type: 'institution', national_type: 'UNIV', external: false})
CREATE (ini1:AgentIdentifier {type: 'UAI', value: '02345'})
CREATE (inst_ll:Literal {language: 'fr', value: 'Université de Paris', type: 'organization_long_label'})

MERGE (inst)-[:HAS_IDENTIFIER]->(ini1)
MERGE (inst)-[:HAS_LONG_LABEL]->(inst_ll)

MERGE (p)-[:EMPLOYED_AT {position_code: 'PR'}]->(inst)
MERGE (rs)-[:MEMBER_OF {position: 'main_supervision'}]->(inst)

CREATE (c1:Concept {uid: 'http://www.idref.fr/02734004x/id', uri: 'http://www.idref.fr/02734004x/id'})
CREATE (c1pl1:Literal {value: 'Analyse des données', language: 'fr', type: 'concept_pref_label'})

MERGE (c1)-[:HAS_PREF_LABEL]->(c1pl1)

CREATE (c2:Concept {uid: 'http://www.idref.fr/027818055/id', uri: 'http://www.idref.fr/027818055/id'})
CREATE (c2pl1:Literal {language: 'fr', value: 'Matière interstellaire', type: 'concept_pref_label'})
CREATE (c2al1:Literal {value: 'Milieu interstellaire', language: 'fr', type: 'concept_alt_label'})

MERGE (c2)-[:HAS_PREF_LABEL]->(c2pl1)
MERGE (c2)-[:HAS_ALT_LABEL]->(c2al1)

CREATE (c3:Concept {uid: 'http://www.wikidata.org/entity/Q210521', uri: 'http://www.wikidata.org/entity/Q210521'})
CREATE (c3pl1:Literal {language: 'fr', value: 'résolution numérique', type: 'concept_pref_label'})
CREATE (c3pl2:Literal {language: 'en', value: 'image resolution', type: 'concept_pref_label'})
CREATE (c3pl3:Literal {language: 'ul', value: 'image resolution (undetermined)', type: 'concept_pref_label'})

CREATE (c3al1:Literal {language: 'en', value: 'pixel count', type: 'concept_alt_label'})
CREATE (c3al2:Literal {language: 'en', value: 'resolution', type: 'concept_alt_label'})

MERGE (c3)-[:HAS_PREF_LABEL]->(c3pl1)
MERGE (c3)-[:HAS_PREF_LABEL]->(c3pl2)
MERGE (c3)-[:HAS_PREF_LABEL]->(c3pl3)
MERGE (c3)-[:HAS_ALT_LABEL]->(c3al1)
MERGE (c3)-[:HAS_ALT_LABEL]->(c3al2)


CREATE (pi1:PublicationIdentifier {type: 'doi', value: '10.3847/1538-4357/ad0cc0'})
CREATE (pi2:PublicationIdentifier {type: 'uri', value: null})

CREATE (pn1:PersonName)
CREATE (pn1fn:Literal {language: 'fr', value: 'Jeannette'})
CREATE (pn1ln:Literal {language: 'fr', value: 'Durand'})

MERGE (pn1)-[:HAS_FIRST_NAME]->(pn1fn)
MERGE (pn1)-[:HAS_LAST_NAME]->(pn1ln)

CREATE (pn2:PersonName)
CREATE (pn2fn:Literal {language: 'fr', value: 'Jeannette'})
CREATE (pn2ln:Literal {language: 'fr', value: 'Dupont'})

MERGE (pn2)-[:HAS_FIRST_NAME]->(pn2fn)
MERGE (pn2)-[:HAS_LAST_NAME]->(pn2ln)

MERGE (p)-[:HAS_NAME]->(pn1)
MERGE (p)-[:HAS_NAME]->(pn2)

CREATE(t1:Literal {language: 'en',
                   value:    'All We Are Is Dust in the WIM: Constraints on Dust Properties in the Milky Way’s Warm Ionized Medium'})
CREATE(t2:Literal {language: 'fr',
                   value:    'Nous ne sommes que de la poussière dans le WIM : contraintes sur les propriétés de la poussière dans le milieu ionisé chaud de la Voie Lactée'})


CREATE (j1:SourceJournal {
  uid:               'scanr-0004-637X-1538-4357-the_astrophysical_journal-american_astronomical_society-ScanR',
  publisher:         'American Astronomical Society',
  titles:            ['The Astrophysical Journal'],
  source:            'ScanR',
  source_identifier: '0004-637X-1538-4357-the_astrophysical_journal-american_astronomical_society-ScanR'
})


CREATE (ji1:JournalIdentifier {type: 'issn', value: '0004-637X', format: 'Print'})
CREATE (ji2:JournalIdentifier {type: 'issn', value: '1538-4357', format: 'Online'})
CREATE (ji3:JournalIdentifier {type: 'issn', value: '3478-4357'})

MERGE (j1)-[:HAS_IDENTIFIER]->(ji1)
MERGE (j1)-[:HAS_IDENTIFIER]->(ji2)
MERGE (j1)-[:HAS_IDENTIFIER]->(ji3)

CREATE (si:SourceIssue {
  number:            [],
  source:            'ScanR',
  titles:            [],
  source_identifier: 'the_astrophysical_journal-ScanR'
})

MERGE (si)-[:ISSUED_BY]->(j1)

CREATE (sp1:SourcePerson {
  uid:               'hal-123456',
  name:              'Marie Dupuis',
  source:            'hal',
  source_identifier: '123456'
})

CREATE (sc1:SourceContribution {
  role: 'AUTHOR'
})

CREATE (sp2:SourcePerson {
  uid:               'hal-987654',
  name:              'Laurent Dupond',
  source:            'hal',
  source_identifier: '987654'
})

CREATE (sc2:SourceContribution {
  role: 'THESIS-DIRECTOR'
})

MERGE (sc1)-[:CONTRIBUTOR]->(sp1)
MERGE (sc2)-[:CONTRIBUTOR]->(sp2)

CREATE (s1:SourceRecord {
  issued:            '2012-09-19T00:00:00Z',
  document_types:    ['Book', 'Document'],
  harvester:         'ScanR',
  url:               'https://scanr.enseignementsup-recherche.gouv.fr/publications/10.3847/1538-4357/ad0cc0',
  uid:               'scanr-doi10.3847/1538-4357/ad0cc0',
  source_identifier: 'doi10.3847/1538-4357/ad0cc0'
})

MERGE (s1)-[:HAS_TITLE]->(t1)
MERGE (s1)-[:HAS_TITLE]->(t2)
MERGE (s1)-[:HAS_SUBJECT]->(c1)
MERGE (s1)-[:HAS_SUBJECT]->(c2)
MERGE (s1)-[:HAS_SUBJECT]->(c3)
MERGE (s1)-[:HAS_IDENTIFIER]->(pi1)
MERGE (s1)-[:HAS_IDENTIFIER]->(pi2)
MERGE (s1)-[:PUBLISHED_IN]->(si)
MERGE (s1)-[:HARVESTED_FOR]->(p)
MERGE (s1)-[:HAS_CONTRIBUTION]->(sc1)
MERGE (s1)-[:HAS_CONTRIBUTION]->(sc2)


CREATE (s2:SourceRecord {
  harvester:            'HAL',
  url:                  'https://hal.science/hal-04234567',
  uid:                  'hal-hal-04234567',
  source_identifier:    'hal-04234567',
  hal_collection_codes: ['astronomy', 'cosmology'],
  hal_submit_type:      'file'
})
MERGE (s2)-[:HARVESTED_FOR]->(p)

CREATE (doc:Document {uid:                    'doc1',
                      document_type:          'JournalArticle',
                      publication_date:       '2012-09-19',
                      publication_date_start: '2012-09-19T00:00:00Z',
                      publication_date_end:   '2012-09-19T23:59:59Z',
                      upw_oa_status:          'gold',
                      oa_status:              'green'})
CREATE(title1:Literal {language: 'en',
                       value:    'All We Are Is Dust in the WIM: Constraints on Dust Properties in the Milky Way’s Warm Ionized Medium'})
CREATE(title2:Literal {language: 'fr',
                       value:    'Nous ne sommes que de la poussière dans le WIM : contraintes sur les propriétés de la poussière dans le milieu ionisé chaud de la Voie Lactée'})
CREATE(abstract1:TextLiteral {language: 'en',
                              value:    'A detailed abstract of the document in English.'})
CREATE(abstract2:TextLiteral {language: 'ul',
                              value:    'A detailed abstract of the document in an undetermined language.'})
CREATE (doc)-[:HAS_TITLE]->(title1)
CREATE (doc)-[:HAS_TITLE]->(title2)
CREATE (doc)-[:HAS_ABSTRACT]->(abstract1)
CREATE (doc)-[:HAS_ABSTRACT]->(abstract2)
CREATE (doc)-[:HAS_SUBJECT]->(c1)
CREATE (doc)-[:HAS_SUBJECT]->(c2)
CREATE (doc)-[:HAS_SUBJECT]->(c3)
CREATE (doc)-[:RECORDED_BY]->(s1)
CREATE (doc)-[:RECORDED_BY]->(s2)

CREATE(j:Journal {uid: 'journal-0004-637X', issn_l: '0004-637X', publisher: 'American Astronomical Society', titles: [
  'The Astrophysical Journal']})

MERGE (j)-[:HAS_IDENTIFIER]->(ji1)
MERGE (j)-[:HAS_IDENTIFIER]->(ji2)
MERGE (j)-[:HAS_IDENTIFIER]->(ji3)

CREATE (doc)-[:PUBLISHED_IN {volume: '823', issue: '1', pages: '1–20'}]->(j)

// --- Authority organizations (Root + States) ---

// Shared identifiers
CREATE (ao_ror:AgentIdentifier {type: 'ror', value: 'https://ror.org/000000000'})
CREATE (ao_idref:AgentIdentifier {type: 'idref', value: '123456789'})
CREATE (ao_hal_1:AgentIdentifier {type: 'hal', value: '2001'})
CREATE (ao_hal_2:AgentIdentifier {type: 'hal', value: '2002'})

// Root
CREATE (ao_root:AuthorityOrganization:AuthorityOrganizationRoot {
  uid:                      'ao-root-1',
  display_names:            ['Université Anonyme'],
  source_organization_uids: ['hal-2001', 'hal-2002']
})

// Two states attached to root
CREATE (ao_state_1:AuthorityOrganization:AuthorityOrganizationState {
  uid:                      'ao-state-1',
  display_names:            ['Université Anonyme'],
  source_organization_uids: ['hal-2001']
})

CREATE (ao_state_2:AuthorityOrganization:AuthorityOrganizationState {
  uid:                      'ao-state-2',
  display_names:            ['Université Anonyme'],
  source_organization_uids: ['hal-2002']
})

// Attach states to root
MERGE (ao_root)-[:HAS_STATES]->(ao_state_1)
MERGE (ao_root)-[:HAS_STATES]->(ao_state_2)

// Identifiers:
// - states each have their own hal + common idref
// - root has only the common identifier(s) you want (here: ror)
MERGE (ao_state_1)-[:HAS_IDENTIFIER]->(ao_hal_1)
MERGE (ao_state_1)-[:HAS_IDENTIFIER]->(ao_idref)

MERGE (ao_state_2)-[:HAS_IDENTIFIER]->(ao_hal_2)
MERGE (ao_state_2)-[:HAS_IDENTIFIER]->(ao_idref)

MERGE (ao_root)-[:HAS_IDENTIFIER]->(ao_ror)

// --- Contributions (Document-side) ---
CREATE (c_doc_1:Contribution {uid: 'contrib-1', roles: ['AUTHOR']})
CREATE (c_doc_2:Contribution {uid: 'contrib-2', roles: ['AUTHOR']})

// Link doc -> contributions
MERGE (doc)-[:HAS_CONTRIBUTION]->(c_doc_1)
MERGE (doc)-[:HAS_CONTRIBUTION]->(c_doc_2)

// Link person -> contributions
MERGE (p)-[:HAS_CONTRIBUTION]->(c_doc_1)
MERGE (p)-[:HAS_CONTRIBUTION]->(c_doc_2)

// Affiliations:
// - contribution 1 attached to a STATE
// - contribution 2 attached to a ROOT
MERGE (c_doc_1)-[:HAS_AFFILIATION_STATEMENT]->(ao_state_1)
MERGE (c_doc_2)-[:HAS_AFFILIATION_STATEMENT]->(ao_root)

// --- Legacy pseudo-concept (free-form keyword, no URI, single pref label, no alt label) ---
CREATE (c4:Concept {uid: 'keyword:open-access'})
CREATE (c4pl1:Literal {value: 'Open access', language: 'en', type: 'concept_pref_label'})
MERGE (c4)-[:HAS_PREF_LABEL]->(c4pl1)
WITH c4
MATCH (doc:Document {uid: 'doc1'})
CREATE (doc)-[:HAS_SUBJECT]->(c4)

// --- Co-author for doc1 ---
WITH doc
MATCH (ao_s1:AuthorityOrganizationState {uid: 'ao-state-1'})
CREATE (p2:Person {uid: 'local-jmartin@univ-domain.edu', display_name: 'Jean Martin', external: false, display_name_variants: []})
CREATE (pn3:PersonName)
CREATE (pn3fn:Literal {language: 'fr', value: 'Jean'})
CREATE (pn3ln:Literal {language: 'fr', value: 'Martin'})
MERGE (pn3)-[:HAS_FIRST_NAME]->(pn3fn)
MERGE (pn3)-[:HAS_LAST_NAME]->(pn3ln)
MERGE (p2)-[:HAS_NAME]->(pn3)
CREATE (c_doc_3:Contribution {uid: 'contrib-3', roles: ['AUTHOR']})
MERGE (doc)-[:HAS_CONTRIBUTION]->(c_doc_3)
MERGE (p2)-[:HAS_CONTRIBUTION]->(c_doc_3)
MERGE (c_doc_3)-[:HAS_AFFILIATION_STATEMENT]->(ao_s1)

// --- Location data for authority organizations ---
WITH p2
MATCH (ao_s1:AuthorityOrganizationState {uid: 'ao-state-1'})
MATCH (ao_r1:AuthorityOrganizationRoot {uid: 'ao-root-1'})
CREATE (place1:Place {latitude: 48.8534, longitude: 2.3488})
CREATE (place2:Place {latitude: 48.8566, longitude: 2.3522})
CREATE (addr1:StructuredPhysicalAddress {uid: 'addr-ao-state-1'})
CREATE (addr1_city:Literal {type: 'institution_city_name', value: 'Paris', language: 'fr'})
CREATE (addr1_zip:Literal {type: 'institution_zip_code', value: '75005', language: 'ul'})
CREATE (addr1_country:Literal {type: 'institution_country_name', value: 'France', language: 'fr'})
MERGE (ao_s1)-[:HAS_POS]->(place1)
MERGE (ao_r1)-[:HAS_POS]->(place1)
MERGE (ao_r1)-[:HAS_POS]->(place2)
MERGE (ao_s1)-[:HAS_ADDRESS]->(addr1)
MERGE (addr1)-[:HAS_CITY]->(addr1_city)
MERGE (addr1)-[:HAS_ZIP_CODE]->(addr1_zip)
MERGE (addr1)-[:HAS_COUNTRY]->(addr1_country)

// --- Additional ResearchUnits for short label ranking tests ---
// ru2: short label "LRAD"  — pure substring of "LRA" (tests exact > substring)
// ru3: short label "LRA Bordeaux" — "LRA" as a whole word (tests word-boundary > substring)
WITH addr1
CREATE (ru2:OrganizationUnit:Unit:ResearchUnit {uid: 'local-ru-999999', generic_type: 'unit', national_type: 'UMR', external: false})
CREATE (ru2_sl:Literal {language: 'fr', value: 'LRAD', type: 'organization_short_label'})
MERGE (ru2)-[:HAS_SHORT_LABEL]->(ru2_sl)
WITH ru2
CREATE (ru3:OrganizationUnit:Unit:ResearchUnit {uid: 'local-ru-888888', generic_type: 'unit', national_type: 'UMR', external: false})
CREATE (ru3_sl:Literal {language: 'fr', value: 'LRA Paris', type: 'organization_short_label'})
MERGE (ru3)-[:HAS_SHORT_LABEL]->(ru3_sl);

// --- Embeddings for semantic search tests ---
// title1: unit vector along dim 0. abstract1: unit vector along dim 1.
// Orthogonal vectors let tests distinguish title-hit vs abstract-hit queries.
WITH [i IN range(0, 1023) | CASE WHEN i = 0 THEN 1.0 ELSE 0.0 END] AS title_vec,
     [i IN range(0, 1023) | CASE WHEN i = 1 THEN 1.0 ELSE 0.0 END] AS abstract_vec
MATCH (t:Literal {language: ‘en’, value: "All We Are Is Dust in the WIM: Constraints on Dust Properties in the Milky Way’s Warm Ionized Medium"})
SET t:Embeddable,
    t.type = 'document_title',
    t.embedding_status = 'success',
    t.embedding_model = 'bge-m3',
    t.embedding = title_vec
WITH abstract_vec
MATCH (a:TextLiteral {language: 'en', value: 'A detailed abstract of the document in English.'})
SET a:Embeddable,
    a.type = 'document_abstract',
    a.embedding_status = 'success',
    a.embedding_model = 'bge-m3',
    a.embedding = abstract_vec

