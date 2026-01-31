#!/usr/bin/env python3
"""
Sample Data Generator for Research Collaboration System
Generates realistic sample data for all databases
"""

import os
import json
import random
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging
import pandas as pd
import numpy as np
from faker import Faker
from database_manager import ResearchDatabaseManager, load_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker for realistic data generation
fake = Faker()
Faker.seed(42)  # For reproducible results
np.random.seed(42)


class ResearchDataGenerator:
    """Generate realistic research collaboration data"""
    
    def __init__(self, db_manager: ResearchDatabaseManager):
        self.db_manager = db_manager
        self.researcher_ids = []
        self.department_ids = ["dept_cs", "dept_bio", "dept_chem", "dept_math", "dept_physics"]
        self.research_interests = [
            "machine_learning", "artificial_intelligence", "bioinformatics", "quantum_computing",
            "natural_language_processing", "computer_vision", "robotics", "neuroscience",
            "genetics", "molecular_biology", "organic_chemistry", "inorganic_chemistry",
            "statistics", "pure_mathematics", "applied_mathematics", "astrophysics",
            "condensed_matter", "particle_physics", "optics", "materials_science",
            "الذكاء_الاصطناعي", "الأمن_السيبراني", "تحليل_البيانات", "الرؤية_الحاسوبية", "معالجة_اللغات_الطبيعية"
        ]
        self.project_titles = [
            "AI-Driven Drug Discovery Platform",
            "Quantum Computing Applications in Cryptography",
            "Machine Learning for Climate Prediction",
            "Blockchain Security Analysis Framework",
            "Neural Networks for Medical Imaging",
            "Distributed Systems Optimization",
            "Robotics for Healthcare Assistance",
            "Natural Language Processing for Legal Documents",
            "Computer Vision in Autonomous Vehicles",
            "Bioinformatics Tools for Genomics",
            "Quantum Machine Learning Algorithms",
            "Sustainable Energy Systems Modeling",
            "Cybersecurity Framework Development",
            "Real-time Data Analytics Platform",
            "Virtual Reality for Education",
            "منصة اكتشاف الأدوية بالذكاء الاصطناعي",
            "تطبيقات الحوسبة الكمومية في التشفير",
            "تعلم الآلة للتنبؤ بالمناخ",
            "إطار تحليل أمن البلوكتشين",
            "الشبكات العصبية للتصوير الطبي",
            "نظام مراقبة جودة الهواء الذكي",
            "تحليل المشاعر في وسائل التواصل الاجتماعي باللغة العربية",
            "تحسين كفاءة الألواح الشمسية باستخدام النانو",
            "معالجة الصور الطبية للكشف المبكر عن الأورام",
            "تطوير تقنيات الري الذكي للزراعة المستدامة",
            "نظام إدارة الطاقة في المدن الذكية",
            "الأمن السيبراني في منصات التجارة الإلكترونية",
            "تحليل البيانات الضخمة في القطاع الصحي",
            "نظام التنبؤ بالأخطار الطبيعية باستخدام الذكاء الاصطناعي",
            "محرك بحث متطور للمصادر العربية القديمة",
            "تطوير تقنيات التعليم الذكي لذوي الاحتياجات الخاصة",
            "المحاكاة الرقمية لعمليات الإنتاج الصناعي",
            "تحليل الشبكات الاجتماعية للكشف عن الأخبار الزائفة"
        ]
        self.journal_names = [
            "Nature", "Science", "IEEE Transactions on Pattern Analysis and Machine Intelligence",
            "Nature Machine Intelligence", "Journal of Machine Learning Research",
            "Bioinformatics", "Physical Review Letters", "Journal of Chemical Physics",
            "Mathematics of Computation", "Artificial Intelligence", "Neural Networks",
            "Computer Vision and Image Understanding", "Pattern Recognition", "Data Mining and Knowledge Discovery",
            "مجلة العلوم الحاسوبية", "المجلة العربية للذكاء الاصطناعي", "التقنية الحديثة", "نظم المعلومات العالمية", "الأبحاث المتقدمة"
        ]
        
    def _convert_dates_to_strings(self, data: Dict) -> Dict:
        """Recursively convert all date objects to ISO strings in a dictionary"""
        if isinstance(data, dict):
            return {key: self._convert_dates_to_strings(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_dates_to_strings(item) for item in data]
        elif isinstance(data, date) and not isinstance(data, datetime):
            # Convert date to datetime at midnight and then to ISO string
            return datetime.combine(data, datetime.min.time()).isoformat()
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    def _ensure_cassandra_tables(self):
        """Ensure that required Cassandra tables exist"""
        if not hasattr(self.db_manager, 'cassandra') or not self.db_manager.cassandra or not self.db_manager.cassandra.session:
            logger.warning("Cassandra session not available, cannot ensure tables")
            return False
            
        logger.info("Checking and creating Cassandra tables if needed...")
        try:
            # Create publication_metrics table if it doesn't exist
            create_pub_metrics_query = """
            CREATE TABLE IF NOT EXISTS publication_metrics (
                publication_id UUID,
                analytics_date DATE,
                citation_count INT,
                download_count INT,
                view_count INT,
                h_index_contribution INT,
                PRIMARY KEY (publication_id, analytics_date)
            ) WITH CLUSTERING ORDER BY (analytics_date DESC);
            """
            self.db_manager.cassandra.session.execute(create_pub_metrics_query)
            logger.info("publication_metrics table ensured")
            
            # Create department_analytics table if it doesn't exist
            create_dept_analytics_query = """
            CREATE TABLE IF NOT EXISTS department_analytics (
                department_id TEXT,
                analytics_date DATE,
                active_researchers INT,
                total_publications INT,
                total_citations INT,
                avg_h_index FLOAT,
                collaboration_rate FLOAT,
                project_count INT,
                funding_total BIGINT,
                PRIMARY KEY (department_id, analytics_date)
            ) WITH CLUSTERING ORDER BY (analytics_date DESC);
            """
            self.db_manager.cassandra.session.execute(create_dept_analytics_query)
            logger.info("department_analytics table ensured")
            
            return True
        except Exception as e:
            logger.error(f"Failed to ensure Cassandra tables: {e}")
            return False
    
    def generate_researcher_data(self, count: int = 50) -> List[Dict]:
        """Generate researcher data"""
        logger.info(f"Generating {count} researcher records...")
        
        researchers = []
        for i in range(count):
            # Basic information
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
            
            # Department assignment
            department_id = random.choice(self.department_ids)
            
            # Generate realistic academic profile
            years_experience = random.randint(2, 25)
            position = random.choice([
                "Assistant Professor", "Associate Professor", "Professor", 
                "Research Scientist", "Postdoctoral Fellow", "Senior Researcher"
            ])
            
            # Realistic metrics following academic distributions
            h_index = max(1, int(np.random.lognormal(2.5, 1.2)))
            total_publications = max(1, int(np.random.lognormal(3.0, 1.0)))
            citation_count = int(total_publications * np.random.lognormal(2.0, 1.5))
            collaboration_score = round(random.uniform(3.0, 10.0), 1)
            
            # Research interests
            interests = random.sample(self.research_interests, random.randint(3, 8))
            
            researcher = {
                "_id": str(uuid.uuid4()),
                "orcid_id": f"0000-000{random.randint(10000000, 99999999)}",
                "personal_info": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": fake.phone_number(),
                    "office_location": f"Building {random.choice(['A', 'B', 'C'])}, Room {random.randint(100, 999)}"
                },
                "academic_profile": {
                    "employee_id": f"EMP{random.randint(100000, 999999)}",
                    "department_id": department_id,
                    "position": position,
                    "title": "Dr." if position != "Postdoctoral Fellow" else "",
                    "hire_date": fake.date_between(start_date='-25y', end_date='today'),
                    "education": self._generate_education(first_name, last_name)
                },
                "research_interests": interests,
                "expertise_areas": self._generate_expertise_areas(interests, years_experience),
                "collaboration_metrics": {
                    "total_publications": total_publications,
                    "h_index": h_index,
                    "citation_count": citation_count,
                    "collaboration_score": collaboration_score
                },
                "links": {
                    "personal_website": f"https://{first_name.lower()}{last_name.lower()}.research.edu",
                    "google_scholar": f"https://scholar.google.com/citations?user={fake.uuid4()[:10]}",
                    "research_gate": f"https://researchgate.net/profile/{first_name}_{last_name}",
                    "linkedin": f"https://linkedin.com/in/{first_name.lower()}{last_name.lower()}"
                },
                "metadata": {
                    "created_at": fake.date_time_between(start_date='-5y', end_date='now'),
                    "last_updated": fake.date_time_between(start_date='-30d', end_date='now'),
                    "status": "active",
                    "verified": random.choice([True, True, True, False])  # Mostly verified
                }
            }
            
            # Convert all dates to strings before appending
            researchers.append(self._convert_dates_to_strings(researcher))
        
        logger.info(f"Generated {len(researchers)} researcher records")
        return researchers
    
    def _generate_education(self, first_name: str, last_name: str) -> List[Dict]:
        """Generate realistic education background"""
        education = []
        
        # Always PhD
        education.append({
            "degree": "Ph.D. " + random.choice([
                "Computer Science", "Biology", "Chemistry", "Mathematics", "Physics",
                "Bioinformatics", "Statistics", "Computational Science"
            ]),
            "institution": f"{fake.company()} University",
            "year": random.randint(1995, 2020),
            "thesis": f"Thesis on {fake.sentence(nb_words=6)}"
        })
        
        # Sometimes Master's
        if random.random() < 0.8:
            education.append({
                "degree": "M.S. " + random.choice([
                    "Computer Science", "Biology", "Chemistry", "Mathematics", "Physics"
                ]),
                "institution": f"{fake.company()} University",
                "year": random.randint(1990, 2018),
                "thesis": f"Master's thesis on {fake.sentence(nb_words=6)}"
            })
        
        # Sometimes Bachelor's
        if random.random() < 0.9:
            education.append({
                "degree": "B.S. " + random.choice([
                    "Computer Science", "Biology", "Chemistry", "Mathematics", "Physics",
                    "Engineering", "Biochemistry"
                ]),
                "institution": f"{fake.company()} University",
                "year": random.randint(1985, 2016),
                "thesis": ""
            })
        
        return sorted(education, key=lambda x: x["year"])
    
    def _generate_expertise_areas(self, interests: List[str], years_experience: int) -> List[Dict]:
        """Generate expertise areas with realistic experience"""
        expertise = []
        for interest in random.sample(interests, min(len(interests), 5)):
            level = random.choices(
                ["beginner", "intermediate", "advanced", "expert"],
                weights=[0.1, 0.2, 0.4, 0.3]
            )[0]
            
            # Experience should be reasonable based on career length
            max_exp = min(years_experience, 30)
            years_exp = random.randint(max(1, max_exp - 10), max_exp)
            
            expertise.append({
                "area": interest,
                "level": level,
                "years_experience": years_exp
            })
        
        return expertise
    
    def generate_project_data(self, researcher_ids: List[str], count: int = 30) -> List[Dict]:
        """Generate project data"""
        logger.info(f"Generating {count} project records...")
        
        projects = []
        
        # Check if we have researcher IDs to assign
        has_researchers = len(researcher_ids) > 0
        
        for i in range(count):
            # Only select principal investigators if we have researcher IDs
            pi_ids = []
            if has_researchers:
                pi_count = min(random.randint(1, 3), len(researcher_ids))
                pi_ids = random.sample(researcher_ids, pi_count)
            
            # Generate timeline
            start_date = fake.date_between(start_date='-5y', end_date='today')
            duration_months = random.choice([6, 12, 18, 24, 36, 48])
            end_date = start_date + timedelta(days=duration_months * 30)
            
            # Project details
            title = random.choice(self.project_titles)
            if title == "AI-Driven Drug Discovery Platform":
                research_area = "bioinformatics"
            elif "Quantum" in title:
                research_area = "quantum_computing"
            elif "Machine Learning" in title or "Neural" in title:
                research_area = "machine_learning"
            elif "Blockchain" in title:
                research_area = "cybersecurity"
            elif "Computer Vision" in title:
                research_area = "computer_vision"
            else:
                research_area = random.choice([
                    "artificial_intelligence", "distributed_systems", "robotics",
                    "natural_language_processing", "bioinformatics"
                ])
            
            # Create project with placeholder for created_by if no researchers available yet
            created_by = pi_ids[0] if pi_ids else f"temp_{uuid.uuid4()}"
            
            project = {
                "_id": str(uuid.uuid4()),
                "title": title,
                "description": fake.text(max_nb_chars=300),
                "project_code": f"PRJ_{random.randint(2020, 2024)}_{random.randint(1, 999):03d}",
                "status": random.choices(
                    ["active", "completed", "planned", "on_hold"],
                    weights=[0.4, 0.3, 0.2, 0.1]
                )[0],
                "priority": random.choice(["low", "medium", "high"]),
                "classification": {
                    "research_area": research_area,
                    "project_type": random.choice(["research", "development", "collaboration"]),
                    "funding_source": random.choice([
                        "NSF Grant", "NIH Grant", "Industry Partnership", 
                        "University Funding", "International Collaboration"
                    ]),
                    "confidentiality_level": random.choice(["public", "restricted", "confidential"])
                },
                "timeline": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_months": duration_months,
                    "milestones": self._generate_milestones(start_date, end_date)
                },
                "funding": {
                    "total_budget": random.randint(100000, 5000000),
                    "amount": random.randint(100000, 5000000), # Redundant for project_detail.html
                    "currency": "USD",
                    "funding_agency": random.choice([
                        "National Science Foundation", "National Institutes of Health",
                        "Department of Energy", "Industry Partners", "University Research Office"
                    ]),
                    "source": random.choice([ # Redundant for project_detail.html
                        "NSF Grant", "NIH Grant", "Industry Partnership", 
                        "University Funding", "International Collaboration"
                    ]),
                    "grant_number": f"{random.choice(['NSF', 'NIH', 'DOE'])}-{random.randint(2020, 2024)}-{random.randint(1000, 9999)}",
                    "budget_breakdown": {
                        "personnel": random.randint(50000, 2000000),
                        "equipment": random.randint(10000, 500000),
                        "travel": random.randint(5000, 100000),
                        "other": random.randint(10000, 200000)
                    }
                },
                "participants": {
                    "principal_investigators": [
                        {
                            "researcher_id": pi_id,
                            "role": "lead_pi" if i == 0 else "pi",
                            "effort_percentage": random.randint(20, 50),
                            "start_date": start_date
                        } for i, pi_id in enumerate(pi_ids)
                    ],
                    "co_investigators": [],
                    "research_assistants": []
                },
                "publications": [],
                "tags": random.sample(self.research_interests, random.randint(3, 7)),
                "metadata": {
                    "created_at": fake.date_time_between(start_date='-5y', end_date='now'),
                    "creation_date": fake.date_time_between(start_date='-5y', end_date='now'), # Fixed for projects list
                    "last_updated": fake.date_time_between(start_date='-30d', end_date='now'),
                    "created_by": created_by
                }
            }
            
            # Add co-investigators only if we have researchers
            if has_researchers:
                available_researchers = [r for r in researcher_ids if r not in pi_ids]
                if available_researchers and random.random() < 0.7:
                    co_pi_count = random.randint(1, min(3, len(available_researchers)))
                    co_pi_ids = random.sample(available_researchers, co_pi_count)
                    project["participants"]["co_investigators"] = [
                        {
                            "researcher_id": co_pi_id,
                            "role": "co_pi",
                            "effort_percentage": random.randint(10, 40),
                            "start_date": start_date
                        } for co_pi_id in co_pi_ids
                    ]
            
            # Convert all dates to strings before appending
            projects.append(self._convert_dates_to_strings(project))
        
        logger.info(f"Generated {len(projects)} project records")
        return projects
    
    def _generate_milestones(self, start_date: date, end_date: date) -> List[Dict]:
        """Generate project milestones"""
        milestones = []
        total_days = (end_date - start_date).days
        
        milestone_count = random.randint(3, 8)
        for i in range(milestone_count):
            milestone_date = start_date + timedelta(days=int(total_days * (i + 1) / (milestone_count + 1)))
            status = random.choices(
                ["completed", "in_progress", "planned"],
                weights=[0.3, 0.4, 0.3] if milestone_date < date.today() else [0.0, 0.2, 0.8]
            )[0]
            
            milestones.append({
                "name": f"Milestone {i + 1}: {fake.sentence(nb_words=4)}",
                "due_date": milestone_date,
                "status": status
            })
        
        return milestones
    
    def generate_publication_data(self, researcher_ids: List[str], project_ids: List[str], count: int = 100) -> List[Dict]:
        """Generate publication data"""
        logger.info(f"Generating {count} publication records...")
        
        publications = []
        
        # Check if we have researcher IDs to assign
        has_researchers = len(researcher_ids) > 0
        has_projects = len(project_ids) > 0
        
        for i in range(count):
            # Generate publication metadata
            title = fake.sentence(nb_words=8)
            publication_date = fake.date_between(start_date='-10y', end_date='today')
            
            # Select authors (realistic number: 1-8 authors)
            authors = []
            if has_researchers:
                author_count = min(random.randint(1, 8), len(researcher_ids))
                author_ids = random.sample(researcher_ids, author_count)
                authors = [
                    {
                        "researcher_id": author_id,
                        "author_order": j + 1,
                        "contribution": "lead_author" if j == 0 else "co_author",
                        "affiliation": fake.company() if random.random() < 0.3 else "University Research Center",
                        "email": fake.email()
                    } for j, author_id in enumerate(author_ids)
                ]
            
            # Citation count based on age and journal
            days_old = (date.today() - publication_date).days
            base_citations = max(0, int(days_old * random.uniform(0.1, 2.0)))
            citation_count = max(0, int(np.random.lognormal(np.log(base_citations + 1), 1.5)))
            
            # Related projects
            related_projects = []
            if has_projects and random.random() < 0.6:
                related_projects = random.sample(project_ids, random.randint(1, min(3, len(project_ids))))
            
            publication = {
                "_id": str(uuid.uuid4()),
                "title": title,
                "abstract": fake.text(max_nb_chars=500),
                "publication_type": random.choice([
                    "journal_article", "conference_paper", "book_chapter", 
                    "preprint", "technical_report"
                ]),
                "status": random.choices(
                    ["published", "accepted", "under_review", "submitted"],
                    weights=[0.7, 0.15, 0.10, 0.05]
                )[0],
                "bibliographic_info": {
                    "journal": random.choice(self.journal_names),
                    "volume": random.randint(1, 50) if random.random() < 0.8 else None,
                    "issue": random.randint(1, 12) if random.random() < 0.6 else None,
                    "pages": f"{random.randint(1, 500)}-{random.randint(501, 600)}" if random.random() < 0.7 else None,
                    "publication_date": publication_date,
                    "doi": f"10.1000/{fake.uuid4()[:8]}",
                    "issn": fake.bothify(text="####-####") if random.random() < 0.5 else None
                },
                "authors": authors,
                "keywords": random.sample(self.research_interests, random.randint(3, 6)),
                "research_areas": random.sample(self.research_interests, random.randint(2, 4)),
                "metrics": {
                    "citation_count": citation_count,
                    "download_count": random.randint(10, 1000),
                    "view_count": random.randint(50, 5000),
                    "h_index_contribution": 1 if citation_count > 10 else 0
                },
                "related_projects": related_projects,
                "related_publications": [],
                "file_info": {
                    "pdf_url": f"https://journals.example.com/articles/{fake.uuid4()[:8]}.pdf",
                    "supplementary_materials": [fake.url()] if random.random() < 0.3 else [],
                    "dataset_url": fake.url() if random.random() < 0.2 else None,
                    "code_repository": fake.url() if random.random() < 0.4 else None
                },
                "funding_acknowledgment": f"This research was supported by {fake.company()} grant." if random.random() < 0.7 else "",
                "metadata": {
                    "created_at": fake.date_time_between(start_date='-10y', end_date='now'),
                    "last_updated": fake.date_time_between(start_date='-30d', end_date='now'),
                    "submitted_date": fake.date_between(start_date=publication_date - timedelta(days=365), end_date=publication_date),
                    "accepted_date": fake.date_between(start_date=publication_date - timedelta(days=90), end_date=publication_date) if publication_date > date(2020, 1, 1) else None,
                    "published_date": publication_date if random.random() < 0.8 else None
                }
            }
            
            # Convert all dates to strings before appending
            publications.append(self._convert_dates_to_strings(publication))
        
        logger.info(f"Generated {len(publications)} publication records")
        return publications
    
    def load_all_data(self, researcher_count: int = 5, project_count: int = 5, publication_count: int = 5):
        """Generate and load all sample data"""
        logger.info("Starting comprehensive data generation and loading...")
        
        try:
            # Step 1: Generate researchers first
            logger.info("Step 1: Generating researchers...")
            researchers = self.generate_researcher_data(researcher_count)
            # Create a map of ID to name for easy lookup during project generation
            researcher_map = {
                r["_id"]: f"{r['personal_info']['first_name']} {r['personal_info']['last_name']}"
                for r in researchers
            }
            researcher_ids = list(researcher_map.keys())
            
            # Step 2: Generate projects with researcher IDs and Names (denormalized)
            logger.info("Step 2: Generating projects...")
            projects = self.generate_project_data(researcher_ids, project_count)
            
            # Additional step: Enrich projects with researcher names during generation
            for project in projects:
                for pi in project["participants"]["principal_investigators"]:
                    rid = pi["researcher_id"]
                    if rid in researcher_map:
                        pi["name"] = researcher_map[rid]
                for copi in project["participants"]["co_investigators"]:
                    rid = copi["researcher_id"]
                    if rid in researcher_map:
                        copi["name"] = researcher_map[rid]
            
            project_ids = [p["_id"] for p in projects]
            
            # Step 3: Generate publications with researcher and project IDs
            logger.info("Step 3: Generating publications...")
            publications = self.generate_publication_data(researcher_ids, project_ids, publication_count)
            publication_ids = [p["_id"] for p in publications]
            
            # Step 4: Link publications to projects
            logger.info("Step 4: Linking publications to projects...")
            for publication in publications:
                if publication["related_projects"]:
                    for project_id in publication["related_projects"]:
                        project = next((p for p in projects if p["_id"] == project_id), None)
                        if project:
                            project["publications"].append({
                                "publication_id": publication["_id"],
                                "relationship": "project_outcome"
                            })
            
            # Step 5: Load data into databases
            logger.info("Step 5: Loading researchers into MongoDB...")
            for researcher in researchers:
                self.db_manager.create_researcher_comprehensive(researcher)
            
            logger.info("Step 6: Loading projects into MongoDB...")
            for project in projects:
                # Use the appropriate method to insert projects
                # Try different possible method names
                try:
                    if hasattr(self.db_manager.mongodb, 'insert'):
                        self.db_manager.mongodb.insert("projects", project)
                    elif hasattr(self.db_manager.mongodb, 'insert_one'):
                        self.db_manager.mongodb.db.projects.insert_one(project)
                    elif hasattr(self.db_manager.mongodb, 'create'):
                        self.db_manager.mongodb.create("projects", project)
                    else:
                        # Fallback to direct MongoDB access
                        self.db_manager.mongodb.db.projects.insert_one(project)
                except Exception as e:
                    logger.error(f"Failed to insert project: {e}")
                    # Try direct access as last resort
                    self.db_manager.mongodb.db.projects.insert_one(project)
            
            logger.info("Step 7: Loading publications into MongoDB...")
            for publication in publications:
                # Use the appropriate method to insert publications
                try:
                    if hasattr(self.db_manager.mongodb, 'insert'):
                        self.db_manager.mongodb.insert("publications", publication)
                    elif hasattr(self.db_manager.mongodb, 'insert_one'):
                        self.db_manager.mongodb.db.publications.insert_one(publication)
                    elif hasattr(self.db_manager.mongodb, 'create'):
                        self.db_manager.mongodb.create("publications", publication)
                    else:
                        # Fallback to direct MongoDB access
                        self.db_manager.mongodb.db.publications.insert_one(publication)
                except Exception as e:
                    logger.error(f"Failed to insert publication: {e}")
                    # Try direct access as last resort
                    self.db_manager.mongodb.db.publications.insert_one(publication)
            
            # Step 8: Create collaboration relationships in Neo4j
            logger.info("Step 8: Creating collaboration relationships in Neo4j...")
            self._create_collaboration_relationships(researcher_ids)
            
            # Step 8.5: Ensure Cassandra tables exist
            if not self._ensure_cassandra_tables():
                logger.warning("Failed to create Cassandra tables, skipping analytics data insertion")
                return {
                    "researchers": len(researchers),
                    "projects": len(projects),
                    "publications": len(publications),
                    "researcher_ids": researcher_ids,
                    "project_ids": project_ids,
                    "publication_ids": publication_ids,
                    "warning": "Cassandra analytics data not inserted due to table creation failure"
                }
            
            # Step 9: Insert analytics data into Cassandra
            if hasattr(self.db_manager, 'cassandra') and self.db_manager.cassandra and self.db_manager.cassandra.session:
                logger.info("Step 9: Inserting analytics data into Cassandra...")
                self._generate_and_insert_analytics(researcher_ids, project_ids, publication_ids)
            else:
                logger.warning("Step 9: Cassandra not connected, skipping analytics data insertion")
            
            logger.info("Data generation and loading completed successfully!")
            return {
                "researchers": len(researchers),
                "projects": len(projects),
                "publications": len(publications),
                "researcher_ids": researcher_ids,
                "project_ids": project_ids,
                "publication_ids": publication_ids
            }
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def _create_collaboration_relationships(self, researcher_ids: List[str]):
        """Create realistic collaboration relationships"""
        # Create co-authorship relationships
        collaboration_probability = 0.3  # 30% chance of collaboration
        num_collaborations = int(len(researcher_ids) * collaboration_probability)
        
        for _ in range(num_collaborations):
            researcher1_id, researcher2_id = random.sample(researcher_ids, 2)
            
            # Create collaboration properties
            collaboration_props = {
                "publication_count": random.randint(1, 10),
                "first_collaboration": fake.date_between(start_date='-5y', end_date='today').isoformat(),
                "last_collaboration": fake.date_between(start_date='-1y', end_date='today').isoformat(),
                "collaboration_strength": round(random.uniform(0.3, 1.0), 2)
            }
            
            self.db_manager.neo4j.create_collaboration_relationship(
                researcher1_id, researcher2_id, "CO_AUTHORED_WITH", collaboration_props
            )
    
    def _generate_and_insert_analytics(self, researcher_ids: List[str], project_ids: List[str], publication_ids: List[str]):
        """Generate and insert analytics data into Cassandra"""
        # Generate last 30 days of analytics data
        for i in range(30):
            analytics_date = date.today() - timedelta(days=i)
            
            # Publication metrics
            for pub_id in random.sample(publication_ids, min(10, len(publication_ids))):
                metrics = {
                    "citation_count": random.randint(0, 100),
                    "download_count": random.randint(0, 500),
                    "view_count": random.randint(10, 1000),
                    "h_index_contribution": random.randint(0, 2)
                }
                
                try:
                    # Try to use the method from db_manager first
                    if hasattr(self.db_manager.cassandra, 'insert_publication_metrics'):
                        self.db_manager.cassandra.insert_publication_metrics(pub_id, metrics, analytics_date)
                    else:
                        # Fallback to direct query
                        query = """
                        INSERT INTO publication_metrics 
                        (publication_id, analytics_date, citation_count, download_count, view_count, h_index_contribution)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        self.db_manager.cassandra.session.execute(query, (
                            pub_id, analytics_date, metrics["citation_count"], 
                            metrics["download_count"], metrics["view_count"], metrics["h_index_contribution"]
                        ))
                except Exception as e:
                    logger.error(f"Failed to insert publication metrics: {e}")
            
            # Department analytics
            for dept_id in self.department_ids:
                analytics = {
                    "department_id": dept_id,
                    "analytics_date": analytics_date,
                    "active_researchers": random.randint(20, 50),
                    "total_publications": random.randint(100, 500),
                    "total_citations": random.randint(1000, 10000),
                    "avg_h_index": round(random.uniform(15, 35), 1),
                    "collaboration_rate": round(random.uniform(0.4, 0.8), 2),
                    "project_count": random.randint(10, 30),
                    "funding_total": random.randint(5000000, 25000000)
                }
                
                try:
                    # Direct query for department analytics
                    query = """
                    INSERT INTO department_analytics 
                    (department_id, analytics_date, active_researchers, total_publications,
                     total_citations, avg_h_index, collaboration_rate, project_count, funding_total)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.db_manager.cassandra.session.execute(query, (
                        analytics["department_id"], analytics["analytics_date"],
                        analytics["active_researchers"], analytics["total_publications"],
                        analytics["total_citations"], analytics["avg_h_index"],
                        analytics["collaboration_rate"], analytics["project_count"],
                        analytics["funding_total"]
                    ))
                except Exception as e:
                    logger.error(f"Failed to insert department analytics: {e}")


def main():
    """Main function to generate and load sample data"""
    # Load configuration
    config = load_database_config()
    
    # Initialize database manager
    db_manager = ResearchDatabaseManager(config)
    
    try:
        # Connect to all databases
        if db_manager.connect_all():
            logger.info("Connected to all databases successfully")
            
            # Initialize data generator
            data_generator = ResearchDataGenerator(db_manager)
            
            # Generate and load sample data
            results = data_generator.load_all_data(
                researcher_count=5,
                project_count=5,
                publication_count=5
            )
            
            logger.info(f"Data generation completed: {results}")
            
            # Save sample data to files for reference
            logger.info("Saving sample data files...")
            
            # This would save JSON files with sample data
            # (Implementation details omitted for brevity)
            
        else:
            logger.error("Failed to connect to databases")
            
    except Exception as e:
        logger.error(f"Data generation failed: {e}")
        raise
        
    finally:
        db_manager.disconnect_all()


if __name__ == "__main__":
    main()