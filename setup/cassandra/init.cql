CREATE KEYSPACE research_analytics
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE research_analytics;

CREATE TABLE publication_metrics (
    publication_id uuid,
    metric_date date,
    citation_count int,
    download_count int,
    view_count int,
    h_index_contribution int,
    PRIMARY KEY ((publication_id), metric_date)
) WITH CLUSTERING ORDER BY (metric_date DESC);

CREATE TABLE collaboration_trends (
    researcher_id uuid,
    collaboration_date date,
    new_collaborations int,
    total_collaborations int,
    collaboration_score decimal,
    PRIMARY KEY ((researcher_id), collaboration_date)
) WITH CLUSTERING ORDER BY (collaboration_date DESC);

CREATE TABLE department_analytics (
    department_id text,
    analytics_date date,
    active_researchers int,
    total_publications int,
    total_citations int,
    avg_h_index decimal,
    collaboration_rate decimal,
    project_count int,
    funding_total decimal,
    PRIMARY KEY ((department_id), analytics_date)
) WITH CLUSTERING ORDER BY (analytics_date DESC);
