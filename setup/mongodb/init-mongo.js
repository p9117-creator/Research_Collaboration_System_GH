// MongoDB Initialization Script
// Creates database, collections, indexes, and sample data

print('Initializing Research Collaboration MongoDB...');

// Switch to the research_collaboration database
db = db.getSiblingDB('research_collaboration');

// Create collections
db.createCollection('researchers');
db.createCollection('projects');
db.createCollection('publications');
db.createCollection('departments');

// Create indexes for better performance
print('Creating indexes...');

// Researchers indexes
db.researchers.createIndex({ "orcid_id": 1 }, { unique: true });
db.researchers.createIndex({ "personal_info.email": 1 }, { unique: true });
db.researchers.createIndex({ "academic_profile.department_id": 1 });
db.researchers.createIndex({ "research_interests": 1 });
db.researchers.createIndex({ "collaboration_metrics.h_index": -1 });
db.researchers.createIndex({ "personal_info.last_name": 1, "personal_info.first_name": 1 });

// Projects indexes
db.projects.createIndex({ "project_code": 1 }, { unique: true });
db.projects.createIndex({ "status": 1 });
db.projects.createIndex({ "timeline.start_date": 1, "timeline.end_date": 1 });
db.projects.createIndex({ "funding.funding_agency": 1 });
db.projects.createIndex({ "participants.principal_investigators.researcher_id": 1 });
db.projects.createIndex({ "classification.research_area": 1 });

// Publications indexes
db.publications.createIndex({ "bibliographic_info.doi": 1 }, { unique: true });
db.publications.createIndex({ "authors.researcher_id": 1 });
db.publications.createIndex({ "bibliographic_info.publication_date": -1 });
db.publications.createIndex({ "keywords": 1 });
db.publications.createIndex({ "metrics.citation_count": -1 });
db.publications.createIndex({ "research_areas": 1 });

// Departments indexes
db.departments.createIndex({ "code": 1 }, { unique: true });
db.departments.createIndex({ "name": 1 });

print('Indexes created successfully!');

// Insert sample departments
print('Inserting sample departments...');
db.departments.insertMany([
  {
    _id: "dept_cs",
    name: "Computer Science",
    full_name: "Department of Computer Science",
    code: "CS",
    institution: "University Research Center",
    description: "Leading research in computer science with focus on AI, systems, and theory.",
    contact_info: {
      building: "Technology Center",
      address: "123 University Ave, Campus City, State 12345",
      phone: "+1-555-0199",
      email: "cs-dept@university.edu",
      website: "https://cs.university.edu"
    },
    faculty_count: 45,
    research_areas: [
      "artificial_intelligence",
      "machine_learning",
      "computer_vision",
      "natural_language_processing",
      "distributed_systems",
      "cybersecurity",
      "software_engineering"
    ],
    established_date: "1985-09-01",
    head_of_department: {
      researcher_id: "507f1f77bcf86cd799439015",
      title: "Department Chair",
      start_date: "2022-07-01"
    },
    metadata: {
      created_at: new Date(),
      last_updated: new Date()
    }
  },
  {
    _id: "dept_bio",
    name: "Biology",
    full_name: "Department of Biological Sciences",
    code: "BIO",
    institution: "University Research Center",
    description: "Advancing understanding of life sciences through innovative research.",
    contact_info: {
      building: "Life Sciences Building",
      address: "456 Science Dr, Campus City, State 12345",
      phone: "+1-555-0299",
      email: "bio-dept@university.edu",
      website: "https://bio.university.edu"
    },
    faculty_count: 38,
    research_areas: [
      "molecular_biology",
      "genetics",
      "bioinformatics",
      "ecology",
      "neuroscience",
      "cell_biology"
    ],
    established_date: "1978-09-01",
    head_of_department: {
      researcher_id: "507f1f77bcf86cd799439016",
      title: "Department Chair",
      start_date: "2021-07-01"
    },
    metadata: {
      created_at: new Date(),
      last_updated: new Date()
    }
  },
  {
    _id: "dept_chem",
    name: "Chemistry",
    full_name: "Department of Chemistry",
    code: "CHEM",
    institution: "University Research Center",
    description: "Exploring molecular science and chemical processes.",
    contact_info: {
      building: "Chemistry Building",
      address: "789 Lab Way, Campus City, State 12345",
      phone: "+1-555-0399",
      email: "chem-dept@university.edu",
      website: "https://chem.university.edu"
    },
    faculty_count: 32,
    research_areas: [
      "organic_chemistry",
      "inorganic_chemistry",
      "physical_chemistry",
      "analytical_chemistry",
      "biochemistry",
      "materials_science"
    ],
    established_date: "1965-09-01",
    head_of_department: {
      researcher_id: "507f1f77bcf86cd799439017",
      title: "Department Chair",
      start_date: "2020-07-01"
    },
    metadata: {
      created_at: new Date(),
      last_updated: new Date()
    }
  },
  {
    _id: "dept_math",
    name: "Mathematics",
    full_name: "Department of Mathematics",
    code: "MATH",
    institution: "University Research Center",
    description: "Advancing mathematical knowledge and its applications.",
    contact_info: {
      building: "Mathematics Building",
      address: "321 Math Ave, Campus City, State 12345",
      phone: "+1-555-0499",
      email: "math-dept@university.edu",
      website: "https://math.university.edu"
    },
    faculty_count: 28,
    research_areas: [
      "pure_mathematics",
      "applied_mathematics",
      "statistics",
      "numerical_analysis",
      "mathematical_modeling",
      "computational_mathematics"
    ],
    established_date: "1960-09-01",
    head_of_department: {
      researcher_id: "507f1f77bcf86cd799439018",
      title: "Department Chair",
      start_date: "2019-07-01"
    },
    metadata: {
      created_at: new Date(),
      last_updated: new Date()
    }
  },
  {
    _id: "dept_physics",
    name: "Physics",
    full_name: "Department of Physics",
    code: "PHYS",
    institution: "University Research Center",
    description: "Understanding the fundamental laws of nature through research.",
    contact_info: {
      building: "Physics Building",
      address: "654 Quantum Rd, Campus City, State 12345",
      phone: "+1-555-0599",
      email: "phys-dept@university.edu",
      website: "https://phys.university.edu"
    },
    faculty_count: 35,
    research_areas: [
      "quantum_mechanics",
      "condensed_matter",
      "particle_physics",
      "astrophysics",
      "optics",
      "plasma_physics"
    ],
    established_date: "1962-09-01",
    head_of_department: {
      researcher_id: "507f1f77bcf86cd799439019",
      title: "Department Chair",
      start_date: "2023-07-01"
    },
    metadata: {
      created_at: new Date(),
      last_updated: new Date()
    }
  }
]);

print('Sample departments inserted successfully!');

// Create sample researcher data (will be loaded by Python script)
print('Database initialization completed!');
print('Collections: researchers, projects, publications, departments');
print('Sample data will be loaded by the application.');
