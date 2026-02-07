// Neo4j Constraints and Indexes Creation
// This script creates constraints and indexes for optimal performance

// Drop existing constraints if they exist
DROP CONSTRAINT researcher_id IF EXISTS;
DROP CONSTRAINT department_id IF EXISTS;
DROP CONSTRAINT publication_id IF EXISTS;
DROP CONSTRAINT project_id IF EXISTS;
DROP CONSTRAINT orcid_id IF EXISTS;

// Create constraints for unique identifiers
CREATE CONSTRAINT researcher_id FOR (r:Researcher) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT department_id FOR (d:Department) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT publication_id FOR (p:Publication) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT project_id FOR (pr:Project) REQUIRE pr.id IS UNIQUE;
CREATE CONSTRAINT orcid_id FOR (r:Researcher) REQUIRE r.orcid_id IS UNIQUE;

// Create indexes for frequently queried properties
CREATE INDEX researcher_department IF NOT EXISTS FOR (r:Researcher) ON (r.department);
CREATE INDEX researcher_h_index IF NOT EXISTS FOR (r:Researcher) ON (r.h_index);
CREATE INDEX researcher_publication_count IF NOT EXISTS FOR (r:Researcher) ON (r.publication_count);
CREATE INDEX publication_date IF NOT EXISTS FOR (p:Publication) ON (p.publication_date);
CREATE INDEX publication_citation_count IF NOT EXISTS FOR (p:Publication) ON (p.citation_count);
CREATE INDEX project_status IF NOT EXISTS FOR (pr:Project) ON (pr.status);
CREATE INDEX project_dates IF NOT EXISTS FOR (pr:Project) ON (pr.start_date, pr.end_date);

// Create relationship indexes
CREATE INDEX co_authored_with IF NOT EXISTS FOR ()-[r:CO_AUTHORED_WITH]-() ON (r.collaboration_strength);
CREATE INDEX supervised IF NOT EXISTS FOR ()-[r:SUPERVISED]-() ON (r.supervision_type);
CREATE INDEX authored IF NOT EXISTS FOR ()-[r:AUTHORED]-() ON (r.author_order);

// Clear any existing sample data
MATCH (n) DETACH DELETE n;

RETURN "Constraints and indexes created successfully" as status;
