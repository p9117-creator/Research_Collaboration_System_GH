-- Cassandra Initialization for Research Collaboration System
-- Creates keyspace and tables for time-series analytics

-- Create keyspace with replication strategy
CREATE KEYSPACE IF NOT EXISTS research_analytics
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE research_analytics;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS publication_metrics;
DROP TABLE IF EXISTS collaboration_trends;
DROP TABLE IF EXISTS department_analytics;
DROP TABLE IF EXISTS system_performance;

-- publication_metrics: Track publication metrics over time
CREATE TABLE publication_metrics (
    publication_id uuid,
    metric_date date,
    citation_count int,
    download_count int,
    view_count int,
    h_index_contribution int,
    PRIMARY KEY ((publication_id), metric_date)
) WITH CLUSTERING ORDER BY (metric_date DESC)
AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 7
};

-- collaboration_trends: Track collaboration metrics over time
CREATE TABLE collaboration_trends (
    researcher_id uuid,
    collaboration_date date,
    new_collaborations int,
    total_collaborations int,
    collaboration_score decimal,
    active_projects int,
    PRIMARY KEY ((researcher_id), collaboration_date)
) WITH CLUSTERING ORDER BY (collaboration_date DESC)
AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 7
};

-- department_analytics: Track department-level metrics
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
) WITH CLUSTERING ORDER BY (analytics_date DESC)
AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 30
};

-- system_performance: Track system metrics
CREATE TABLE system_performance (
    metric_name text,
    timestamp timestamp,
    value double,
    unit text,
    tags map<text, text>,
    PRIMARY KEY ((metric_name), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'HOURS',
    'compaction_window_size': 24
};

-- Create indexes for query optimization
CREATE INDEX IF NOT EXISTS idx_pub_metrics_date ON publication_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_collab_date ON collaboration_trends(collaboration_date);
CREATE INDEX IF NOT EXISTS idx_dept_date ON department_analytics(analytics_date);
CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON system_performance(timestamp);

-- Insert sample data
INSERT INTO publication_metrics (
    publication_id, metric_date, citation_count, 
    download_count, view_count, h_index_contribution
) VALUES (
    507f1f77bcf86cd799439020, 
    '2024-12-20', 
    23, 156, 342, 1
);

INSERT INTO collaboration_trends (
    researcher_id, collaboration_date, new_collaborations,
    total_collaborations, collaboration_score, active_projects
) VALUES (
    507f1f77bcf86cd799439011,
    '2024-12-20',
    2,
    15,
    8.7,
    3
);

INSERT INTO department_analytics (
    department_id, analytics_date, active_researchers,
    total_publications, total_citations, avg_h_index,
    collaboration_rate, project_count, funding_total
) VALUES (
    'dept_cs',
    '2024-12-20',
    45,
    342,
    8920,
    23.5,
    0.67,
    28,
    15000000.00
);

-- Verify table creation
SELECT table_name FROM system_schema.tables 
WHERE keyspace_name = 'research_analytics';

SELECT "Cassandra keyspace and tables created successfully" as status;
