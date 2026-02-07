# Research Collaboration System - Data Modeling

## Overview
This document defines the detailed data models for each NoSQL database in the Research Collaboration System, including schemas, relationships, and sample data structures.

## 1. MongoDB (Document Database)

### Collections Overview
MongoDB stores structured data in collections with flexible schemas:

```
research_collaboration/
├── researchers/          # Researcher profiles
├── projects/             # Research projects
├── publications/         # Publications and papers
└── departments/          # Academic departments
```

### 1.1 Researchers Collection

```json
{
  "_id": "ObjectId('507f1f77bcf86cd799439011')",
  "orcid_id": "0000-0002-1825-0097",
  "personal_info": {
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice.johnson@university.edu",
    "phone": "+1-555-0123",
    "office_location": "Building A, Room 301"
  },
  "academic_profile": {
    "employee_id": "EMP001234",
    "department_id": "dept_cs",
    "position": "Associate Professor",
    "title": "Dr.",
    "hire_date": "2018-08-15",
    "education": [
      {
        "degree": "Ph.D. Computer Science",
        "institution": "Stanford University",
        "year": 2015,
        "thesis": "Machine Learning Applications in Healthcare"
      },
      {
        "degree": "M.S. Computer Science",
        "institution": "MIT",
        "year": 2011,
        "thesis": "Distributed Systems Optimization"
      }
    ]
  },
  "research_interests": [
    "machine_learning",
    "healthcare_analytics",
    "distributed_systems",
    "computer_vision",
    "natural_language_processing"
  ],
  "expertise_areas": [
    {
      "area": "Machine Learning",
      "level": "expert",
      "years_experience": 8
    },
    {
      "area": "Healthcare Technology",
      "level": "advanced",
      "years_experience": 5
    }
  ],
  "collaboration_metrics": {
    "total_publications": 47,
    "h_index": 23,
    "citation_count": 1247,
    "collaboration_score": 8.7
  },
  "links": {
    "personal_website": "https://alicejohnson.research.edu",
    "google_scholar": "https://scholar.google.com/citations?user=abc123",
    "research_gate": "https://researchgate.net/profile/Alice_Johnson",
    "linkedin": "https://linkedin.com/in/alicejohnson"
  },
  "metadata": {
    "created_at": "2024-01-15T10:30:00Z",
    "last_updated": "2024-12-20T14:22:00Z",
    "status": "active",
    "verified": true
  }
}
```

### 1.2 Projects Collection

```json
{
  "_id": "ObjectId('507f1f77bcf86cd799439012')",
  "title": "AI-Driven Drug Discovery Platform",
  "description": "Development of machine learning algorithms for identifying potential drug compounds and predicting their therapeutic effects.",
  "project_code": "PRJ_2024_001",
  "status": "active",
  "priority": "high",
  "classification": {
    "research_area": "bioinformatics",
    "project_type": "research",
    "funding_source": "NSF Grant",
    "confidentiality_level": "public"
  },
  "timeline": {
    "start_date": "2024-01-01",
    "end_date": "2026-12-31",
    "duration_months": 36,
    "milestones": [
      {
        "name": "Data Collection Phase",
        "due_date": "2024-06-30",
        "status": "completed"
      },
      {
        "name": "Model Development",
        "due_date": "2025-03-31",
        "status": "in_progress"
      }
    ]
  },
  "funding": {
    "total_budget": 2500000,
    "currency": "USD",
    "funding_agency": "National Science Foundation",
    "grant_number": "NSF-2024-AI-1234",
    "budget_breakdown": {
      "personnel": 1500000,
      "equipment": 500000,
      "travel": 100000,
      "other": 400000
    }
  },
  "participants": {
    "principal_investigators": [
      {
        "researcher_id": "507f1f77bcf86cd799439011",
        "role": "lead_pi",
        "effort_percentage": 50,
        "start_date": "2024-01-01"
      }
    ],
    "co_investigators": [
      {
        "researcher_id": "507f1f77bcf86cd799439013",
        "role": "co_pi",
        "effort_percentage": 30,
        "start_date": "2024-01-01"
      }
    ],
    "research_assistants": [
      {
        "researcher_id": "507f1f77bcf86cd799439014",
        "role": "research_assistant",
        "effort_percentage": 100,
        "start_date": "2024-02-01"
      }
    ]
  },
  "publications": [
    {
      "publication_id": "507f1f77bcf86cd799439020",
      "relationship": "project_outcome"
    }
  ],
  "tags": [
    "machine_learning",
    "drug_discovery",
    "bioinformatics",
    "ai",
    "healthcare"
  ],
  "metadata": {
    "created_at": "2024-01-01T09:00:00Z",
    "last_updated": "2024-12-20T16:45:00Z",
    "created_by": "507f1f77bcf86cd799439011"
  }
}
```

### 1.3 Publications Collection

```json
{
  "_id": "ObjectId('507f1f77bcf86cd799439020')",
  "title": "Deep Learning Approaches for Molecular Property Prediction",
  "abstract": "This paper presents novel deep learning architectures for predicting molecular properties relevant to drug discovery...",
  "publication_type": "journal_article",
  "status": "published",
  "bibliographic_info": {
    "journal": "Nature Machine Intelligence",
    "volume": 6,
    "issue": 2,
    "pages": "123-135",
    "publication_date": "2024-03-15",
    "doi": "10.1038/s42256-024-00123",
    "isbn": null,
    "issn": "2522-5839"
  },
  "authors": [
    {
      "researcher_id": "507f1f77bcf86cd799439011",
      "author_order": 1,
      "contribution": "lead_author",
      "affiliation": "University Research Lab",
      "email": "alice.johnson@university.edu"
    },
    {
      "researcher_id": "507f1f77bcf86cd799439013",
      "author_order": 2,
      "contribution": "co_author",
      "affiliation": "Bioinformatics Institute",
      "email": "bob.smith@bioinst.edu"
    }
  ],
  "keywords": [
    "deep_learning",
    "molecular_properties",
    "drug_discovery",
    "neural_networks",
    "cheminformatics"
  ],
  "research_areas": [
    "machine_learning",
    "bioinformatics",
    "computational_chemistry"
  ],
  "metrics": {
    "citation_count": 23,
    "download_count": 156,
    "view_count": 342,
    "h_index_contribution": 1
  },
  "related_projects": [
    "507f1f77bcf86cd799439012"
  ],
  "related_publications": [
    {
      "publication_id": "507f1f77bcf86cd799439021",
      "relationship_type": "cites"
    }
  ],
  "file_info": {
    "pdf_url": "https://journals.nature.com/articles/s42256-024-00123.pdf",
    "supplementary_materials": [
      "https://journals.nature.com/articles/s42256-024-00123-supplementary.pdf"
    ],
    "dataset_url": "https://github.com/research/molecular-properties-dataset",
    "code_repository": "https://github.com/research/ml-molecular-prediction"
  },
  "funding_acknowledgment": "This research was supported by NSF Grant NSF-2024-AI-1234",
  "metadata": {
    "created_at": "2024-03-15T12:00:00Z",
    "last_updated": "2024-12-20T10:30:00Z",
    "submitted_date": "2023-12-01",
    "accepted_date": "2024-02-28",
    "published_date": "2024-03-15"
  }
}
```

### 1.4 Departments Collection

```json
{
  "_id": "dept_cs",
  "name": "Computer Science",
  "full_name": "Department of Computer Science",
  "code": "CS",
  "institution": "University Research Center",
  "description": "Leading research in computer science with focus on AI, systems, and theory.",
  "contact_info": {
    "building": "Technology Center",
    "address": "123 University Ave, Campus City, State 12345",
    "phone": "+1-555-0199",
    "email": "cs-dept@university.edu",
    "website": "https://cs.university.edu"
  },
  "faculty_count": 45,
  "research_areas": [
    "artificial_intelligence",
    "machine_learning",
    "computer_vision",
    "natural_language_processing",
    "distributed_systems",
    "cybersecurity",
    "software_engineering"
  ],
  "established_date": "1985-09-01",
  "head_of_department": {
    "researcher_id": "507f1f77bcf86cd799439015",
    "title": "Department Chair",
    "start_date": "2022-07-01"
  },
  "metadata": {
    "created_at": "2024-01-01T08:00:00Z",
    "last_updated": "2024-12-20T11:15:00Z"
  }
}
```

### MongoDB Indexes

```javascript
// Researchers indexes
db.researchers.createIndex({ "orcid_id": 1 }, { unique: true })
db.researchers.createIndex({ "personal_info.email": 1 }, { unique: true })
db.researchers.createIndex({ "academic_profile.department_id": 1 })
db.researchers.createIndex({ "research_interests": 1 })
db.researchers.createIndex({ "collaboration_metrics.h_index": -1 })

// Projects indexes
db.projects.createIndex({ "project_code": 1 }, { unique: true })
db.projects.createIndex({ "status": 1 })
db.projects.createIndex({ "timeline.start_date": 1, "timeline.end_date": 1 })
db.projects.createIndex({ "funding.funding_agency": 1 })
db.projects.createIndex({ "participants.principal_investigators.researcher_id": 1 })

// Publications indexes
db.publications.createIndex({ "bibliographic_info.doi": 1 }, { unique: true })
db.publications.createIndex({ "authors.researcher_id": 1 })
db.publications.createIndex({ "bibliographic_info.publication_date": -1 })
db.publications.createIndex({ "keywords": 1 })
db.publications.createIndex({ "metrics.citation_count": -1 })
```

## 2. Neo4j (Graph Database)

### Graph Model Overview
Neo4j stores relationships as first-class citizens, ideal for collaboration networks.

### 2.1 Node Types

#### Researcher Node
```
(r:Researcher {
  id: "507f1f77bcf86cd799439011",
  name: "Alice Johnson",
  email: "alice.johnson@university.edu",
  department: "Computer Science",
  position: "Associate Professor",
  h_index: 23,
  publication_count: 47,
  orcid_id: "0000-0002-1825-0097"
})
```

#### Department Node
```
(d:Department {
  id: "dept_cs",
  name: "Computer Science",
  institution: "University Research Center",
  faculty_count: 45
})
```

#### Publication Node
```
(p:Publication {
  id: "507f1f77bcf86cd799439020",
  title: "Deep Learning Approaches for Molecular Property Prediction",
  journal: "Nature Machine Intelligence",
  publication_date: "2024-03-15",
  doi: "10.1038/s42256-024-00123",
  citation_count: 23
})
```

#### Project Node
```
(pr:Project {
  id: "507f1f77bcf86cd799439012",
  title: "AI-Driven Drug Discovery Platform",
  status: "active",
  start_date: "2024-01-01",
  end_date: "2026-12-31",
  funding_amount: 2500000
})
```

### 2.2 Relationship Types

#### Researcher-Department Relationships
```
(:Researcher)-[:BELONGS_TO {
  role: "faculty",
  start_date: "2018-08-15",
  status: "active"
}]->(:Department)
```

#### Researcher-Researcher Collaborations
```
(:Researcher)-[:CO_AUTHORED_WITH {
  publication_count: 5,
  first_collaboration: "2019-03-15",
  last_collaboration: "2024-03-15",
  collaboration_strength: 0.8
}]->(:Researcher)

(:Researcher)-[:SUPERVISED {
  supervision_type: "phd_advisor",
  start_date: "2019-09-01",
  status: "ongoing",
  student_count: 3
}]->(:Researcher)

(:Researcher)-[:MENTORED {
  mentorship_type: "research_guidance",
  start_date: "2020-01-15",
  end_date: "2022-12-31"
}]->(:Researcher)
```

#### Researcher-Publication Relationships
```
(:Researcher)-[:AUTHORED {
  author_order: 1,
  contribution: "lead_author",
  corresponding_author: true
}]->(:Publication)

(:Researcher)-[:CO_AUTHORED {
  author_order: 2,
  contribution: "co_author",
  corresponding_author: false
}]->(:Publication)
```

#### Researcher-Project Relationships
```
(:Researcher)-[:LEADS {
  role: "principal_investigator",
  effort_percentage: 50,
  start_date: "2024-01-01"
}]->(:Project)

(:Researcher)-[:PARTICIPATES_IN {
  role: "co_investigator",
  effort_percentage: 30,
  start_date: "2024-01-01"
}]->(:Project)

(:Researcher)-[:WORKS_ON {
  role: "research_assistant",
  effort_percentage: 100,
  start_date: "2024-02-01"
}]->(:Project)
```

#### Publication-Project Relationships
```
(:Publication)-[:RESULT_OF {
  relationship_type: "project_outcome",
  generation_time_months: 3
}]->(:Project)

(:Publication)-[:CITES {
  citation_type: "direct_reference",
  context: "methodology"
}]->(:Publication)
```

### 2.3 Sample Cypher Queries

#### Find Collaboration Networks
```cypher
// Find all collaborators of Alice Johnson within 2 degrees
MATCH (r:Researcher {name: "Alice Johnson"})-[:CO_AUTHORED_WITH*1..2]-(collaborator)
RETURN collaborator.name, collaborator.department, collaborator.h_index
ORDER BY collaborator.h_index DESC
LIMIT 10
```

#### Find Research Communities
```cypher
// Find research communities based on collaboration patterns
MATCH (r1:Researcher)-[:CO_AUTHORED_WITH]-(r2:Researcher)
WHERE r1.department = "Computer Science" 
  AND r2.department = "Computer Science"
WITH r1, r2, count(*) as collab_strength
WHERE collab_strength >= 3
RETURN r1.name, r2.name, collab_strength
ORDER BY collab_strength DESC
```

## 3. Redis (Key-Value Store)

### 3.1 Data Structures Used

#### Strings - Cache and Sessions
```
Key: "session:user_507f1f77bcf86cd799439011"
Value: JSON string with user session data
TTL: 3600 seconds (1 hour)

Key: "researcher_profile:507f1f77bcf86cd799439011"
Value: JSON string with cached researcher profile
TTL: 1800 seconds (30 minutes)
```

#### Hashes - Researcher Statistics
```
Key: "researcher_stats:507f1f77bcf86cd799439011"
Field-Value pairs:
- "publications_count": "47"
- "h_index": "23"
- "collaboration_score": "8.7"
- "last_updated": "2024-12-20T14:22:00Z"
```

#### Lists - Recent Activities
```
Key: "recent_publications:dept_cs"
Values (most recent first):
- "507f1f77bcf86cd799439020:Deep Learning Approaches..."
- "507f1f77bcf86cd799439021:Quantum Computing Applications..."
- "507f1f77bcf86cd799439022:Blockchain Security Analysis..."
TTL: 86400 seconds (1 day)
```

#### Sets - Researcher Interests
```
Key: "researchers_by_interest:machine_learning"
Members: researcher IDs with ML expertise
- "507f1f77bcf86cd799439011"
- "507f1f77bcf86cd799439013"
- "507f1f77bcf86cd799439015"

Key: "interests_by_researcher:507f1f77bcf86cd799439011"
Members: interest tags
- "machine_learning"
- "healthcare_analytics"
- "distributed_systems"
```

#### Sorted Sets - Rankings
```
Key: "top_researchers:by_h_index"
Member-Score pairs:
- "507f1f77bcf86cd799439011:23"
- "507f1f77bcf86cd799439013:28"
- "507f1f77bcf86cd799439015:31"

Key: "top_researchers:by_citations"
Member-Score pairs:
- "507f1f77bcf86cd799439011:1247"
- "507f1f77bcf86cd799439013:2156"
- "507f1f77bcf86cd799439015:3421"
```

### 3.2 Cache Strategy

#### Cache Keys Naming Convention
```
researcher_profile:{researcher_id}
researcher_stats:{researcher_id}
recent_publications:{department_id}
top_researchers:by_{metric}
session:{user_id}
collaboration_network:{researcher_id}
search_results:{query_hash}
```

#### TTL Strategy
```
- Researcher profiles: 30 minutes
- Statistics: 1 hour  
- Recent publications: 1 day
- Session data: 1 hour
- Search results: 15 minutes
- Collaboration networks: 2 hours
```

## 4. Cassandra (Wide-Column Store)

### 4.1 Tables Overview
Cassandra stores time-series analytics and metrics data.

### 4.2 Table Definitions

#### publication_metrics Table
```sql
CREATE TABLE publication_metrics (
    publication_id uuid,
    metric_date date,
    citation_count int,
    download_count int,
    view_count int,
    h_index_contribution int,
    PRIMARY KEY ((publication_id), metric_date)
) WITH CLUSTERING ORDER BY (metric_date DESC);
```

#### collaboration_trends Table
```sql
CREATE TABLE collaboration_trends (
    researcher_id uuid,
    collaboration_date date,
    new_collaborations int,
    total_collaborations int,
    collaboration_score decimal,
    PRIMARY KEY ((researcher_id), collaboration_date)
) WITH CLUSTERING ORDER BY (collaboration_date DESC);
```

#### department_analytics Table
```sql
CREATE TABLE department_analytics (
    department_id text,
    analytics_date date,
    active_researchers int,
    total_publications int,
    total_citations int,
    avg_h_index decimal,
    collaboration_rate decimal,
    PRIMARY KEY ((department_id), analytics_date)
) WITH CLUSTERING ORDER BY (analytics_date DESC);
```

#### system_performance Table
```sql
CREATE TABLE system_performance (
    metric_name text,
    timestamp timestamp,
    value double,
    unit text,
    PRIMARY KEY ((metric_name), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);
```

### 4.3 Sample Data

#### publication_metrics Sample
```sql
INSERT INTO publication_metrics (
    publication_id, metric_date, citation_count, 
    download_count, view_count, h_index_contribution
) VALUES (
    507f1f77bcf86cd799439020, 
    '2024-12-20', 
    23, 156, 342, 1
);
```

#### collaboration_trends Sample
```sql
INSERT INTO collaboration_trends (
    researcher_id, collaboration_date, new_collaborations,
    total_collaborations, collaboration_score
) VALUES (
    507f1f77bcf86cd799439011,
    '2024-12-20',
    2,
    15,
    8.7
);
```

## 5. Cross-Database Relationships

### 5.1 Data Consistency Strategy

#### MongoDB as Source of Truth
- Primary data stored in MongoDB
- Other databases receive updates through event listeners
- Consistency checked through reconciliation jobs

#### Update Propagation Flow
```
MongoDB Update → Event Queue → Redis Cache Update
                                 → Neo4j Graph Update
                                 → Cassandra Analytics Update
```

### 5.2 Data Synchronization

#### Real-time Updates
- Direct database updates for critical operations
- Event-driven updates for non-critical data
- Batch processing for analytics updates

#### Conflict Resolution
- Last-write-wins for simple fields
- Merge strategies for complex objects
- Manual intervention for critical conflicts

## 6. Sample Dataset Generation

### 6.1 Data Generation Strategy
- 100 researchers across 5 departments
- 200 projects with varying statuses
- 500 publications with realistic metrics
- 1000+ collaboration relationships
- 6 months of analytics data

### 6.2 Realistic Data Characteristics
- Zipf distribution for publication counts
- Small-world network properties for collaborations
- Realistic academic timelines and dates
- Plausible research interests and expertise areas

This comprehensive data modeling provides the foundation for implementing a robust, scalable research collaboration system with multiple NoSQL databases optimized for different data characteristics and access patterns.
