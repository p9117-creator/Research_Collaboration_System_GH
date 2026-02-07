#!/usr/bin/env python3
"""
Command Line Interface for Research Collaboration System
Interactive CLI for demonstrating database operations and queries
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
import argparse
from datetime import datetime
import pandas as pd

# Add code directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_manager import ResearchDatabaseManager, load_database_config
from query_engine import ResearchQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchCLI:
    """Interactive Command Line Interface for Research Collaboration System"""
    
    def __init__(self):
        self.db_manager = None
        self.query_engine = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to all databases"""
        try:
            config = load_database_config()
            self.db_manager = ResearchDatabaseManager(config)
            
            if self.db_manager.connect_all():
                self.query_engine = ResearchQueryEngine(self.db_manager)
                self.connected = True
                print("✅ Successfully connected to all databases!")
                return True
            else:
                print("❌ Failed to connect to one or more databases")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from databases"""
        if self.db_manager and self.connected:
            self.db_manager.disconnect_all()
            self.connected = False
            print("🔌 Disconnected from databases")
    
    def demonstrate_complete_researcher_profile(self, researcher_id: str = None):
        """Demonstrate getting complete researcher profile"""
        print("\n" + "="*60)
        print("📋 COMPLETE RESEARCHER PROFILE DEMONSTRATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
        
        try:
            # If no researcher_id provided, get first available
            if not researcher_id:
                researchers = self.db_manager.mongodb.search_researchers({}, limit=1)
                if researchers:
                    researcher_id = researchers[0]["_id"]
                    researcher_name = f"{researchers[0]['personal_info']['first_name']} {researchers[0]['personal_info']['last_name']}"
                else:
                    print("❌ No researchers found in database")
                    return
            else:
                # Get researcher name for display
                researcher = self.db_manager.mongodb.get_researcher(researcher_id)
                if researcher:
                    researcher_name = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                else:
                    print(f"❌ Researcher not found: {researcher_id}")
                    return
            
            print(f"🔍 Retrieving complete profile for: {researcher_name}")
            print(f"🆔 Researcher ID: {researcher_id}")
            
            # Get complete profile
            profile = self.query_engine.get_researcher_profile_complete(researcher_id)
            
            if "error" in profile:
                print(f"❌ Error: {profile['error']}")
                return
            
            print("\n📊 PROFILE SUMMARY:")
            print(f"   • Cache Status: {profile.get('cache_status', 'unknown')}")
            print(f"   • Basic Info: ✅ Retrieved")
            print(f"   • Academic Profile: ✅ Retrieved")
            print(f"   • Publications: {profile['publications']['count']} found")
            print(f"   • Projects: {profile['projects']['count']} found")
            print(f"   • Collaborators: {profile['collaboration_network']['collaboration_count']} found")
            
            # Show key information
            if 'basic_info' in profile:
                basic = profile['basic_info']
                print(f"\n👤 BASIC INFORMATION:")
                print(f"   • Name: {basic.get('first_name', '')} {basic.get('last_name', '')}")
                print(f"   • Email: {basic.get('email', 'N/A')}")
                print(f"   • Office: {basic.get('office_location', 'N/A')}")
            
            if 'collaboration_metrics' in profile:
                metrics = profile['collaboration_metrics']
                print(f"\n📈 COLLABORATION METRICS:")
                print(f"   • H-Index: {metrics.get('h_index', 0)}")
                print(f"   • Total Publications: {metrics.get('total_publications', 0)}")
                print(f"   • Total Citations: {metrics.get('citation_count', 0)}")
                print(f"   • Collaboration Score: {metrics.get('collaboration_score', 0)}")
            
            # Show sample collaborators
            collaborators = profile['collaboration_network']['collaborators'][:3]
            if collaborators:
                print(f"\n🤝 TOP COLLABORATORS:")
                for i, collab in enumerate(collaborators, 1):
                    print(f"   {i}. {collab.get('name', 'Unknown')} (Distance: {collab.get('distance', 'N/A')})")
            
            # Show recent publications
            publications = profile['publications']['list'][:3]
            if publications:
                print(f"\n📚 RECENT PUBLICATIONS:")
                for i, pub in enumerate(publications, 1):
                    title = pub.get('title', 'No title')[:60] + "..." if len(pub.get('title', '')) > 60 else pub.get('title', 'No title')
                    print(f"   {i}. {title}")
            
            print(f"\n✅ Profile demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error retrieving profile: {e}")
    
    def demonstrate_advanced_search(self):
        """Demonstrate advanced researcher search"""
        print("\n" + "="*60)
        print("🔍 ADVANCED RESEARCHER SEARCH DEMONSTRATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
        
        try:
            # Search 1: Computer Science researchers with high H-index
            print("\n🎯 Search 1: Computer Science researchers with H-index ≥ 15")
            results1 = self.query_engine.search_researchers_advanced({
                "department": "dept_cs",
                "min_h_index": 15,
                "sort_by": "h_index",
                "limit": 5
            })
            
            print(f"   Found {len(results1)} researchers:")
            for i, researcher in enumerate(results1, 1):
                name = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                h_index = researcher['collaboration_metrics']['h_index']
                pubs = researcher['collaboration_metrics']['total_publications']
                print(f"   {i}. {name} (H-index: {h_index}, Publications: {pubs})")
            
            # Search 2: Researchers in specific interest areas
            print("\n🎯 Search 2: Researchers interested in 'machine_learning' and 'bioinformatics'")
            results2 = self.query_engine.search_researchers_advanced({
                "interests": ["machine_learning", "bioinformatics"],
                "min_publications": 5,
                "sort_by": "publication_count",
                "limit": 5
            })
            
            print(f"   Found {len(results2)} researchers:")
            for i, researcher in enumerate(results2, 1):
                name = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                interests = researcher.get('research_interests', [])[:3]
                print(f"   {i}. {name} (Interests: {', '.join(interests)})")
            
            # Search 3: Name-based search
            print("\n🎯 Search 3: Name-based search for 'john'")
            results3 = self.query_engine.search_researchers_advanced({
                "name_search": "john",
                "limit": 5
            })
            
            print(f"   Found {len(results3)} researchers:")
            for i, researcher in enumerate(results3, 1):
                name = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                email = researcher['personal_info']['email']
                print(f"   {i}. {name} ({email})")
            
            print(f"\n✅ Advanced search demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in advanced search: {e}")
    
    def demonstrate_collaboration_analysis(self):
        """Demonstrate collaboration network analysis"""
        print("\n" + "="*60)
        print("🤝 COLLABORATION NETWORK ANALYSIS DEMONSTRATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
        
        try:
            # Find collaboration pairs
            print("\n🔗 Finding top collaboration pairs in Computer Science department")
            pairs = self.query_engine.find_collaboration_pairs("dept_cs", min_collaborations=1)
            
            print(f"   Found {len(pairs)} collaboration pairs:")
            for i, pair in enumerate(pairs[:5], 1):
                print(f"   {i}. {pair['researcher1_name']} ↔ {pair['researcher2_name']}")
                print(f"      Strength: {pair['collaboration_strength']}, Department: {pair['department']}")
            
            # Get collaboration network for a sample researcher
            if pairs:
                sample_researcher_id = pairs[0]['researcher1_id']
                print(f"\n🌐 Collaboration network for {pairs[0]['researcher1_name']}")
                
                network = self.query_engine.db_manager.neo4j.find_collaborators(sample_researcher_id, max_depth=2)
                print(f"   Network size: {len(network)} collaborators")
                
                # Show network details
                for i, collaborator in enumerate(network[:3], 1):
                    print(f"   {i}. {collaborator.get('name', 'Unknown')} (Distance: {collaborator.get('distance', 'N/A')})")
            
            print(f"\n✅ Collaboration analysis demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in collaboration analysis: {e}")
    
    def demonstrate_analytics(self):
        """Demonstrate analytics and reporting"""
        print("\n" + "="*60)
        print("📊 ANALYTICS AND REPORTING DEMONSTRATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
        
        try:
            # Department analytics
            print("\n🏛️  Computer Science Department Analytics (Last 30 days)")
            analytics = self.query_engine.get_department_analytics("dept_cs", days=30)
            
            if "error" not in analytics:
                basic = analytics['basic_metrics']
                print(f"   • Total Researchers: {basic['total_researchers']}")
                print(f"   • Total Publications: {basic['total_publications']}")
                print(f"   • Total Citations: {basic['total_citations']}")
                print(f"   • Average H-Index: {basic['average_h_index']}")
                print(f"   • Active Projects: {basic['active_projects']}")
                print(f"   • Recent Publications: {basic['recent_publications']}")
                
                # Top researchers
                top_researchers = analytics['top_researchers']
                print(f"\n🏆 Top 3 Researchers by H-Index:")
                for i, researcher in enumerate(top_researchers[:3], 1):
                    print(f"   {i}. {researcher['name']} (H-index: {researcher['metric_value']})")
                
                # Research areas
                research_areas = analytics['research_areas']
                print(f"\n🔬 Top Research Areas:")
                for area, count in list(research_areas.items())[:5]:
                    print(f"   • {area}: {count} researchers")
            else:
                print(f"❌ Error getting analytics: {analytics['error']}")
            
            # Publication analytics
            print(f"\n📚 Publication Analytics (Last 365 days)")
            pub_analytics = self.query_engine.get_publication_analytics(365)
            
            if "error" not in pub_analytics:
                basic = pub_analytics['basic_metrics']
                print(f"   • Total Publications: {basic['total_publications']}")
                print(f"   • Total Citations: {basic['total_citations']}")
                print(f"   • Average Citations per Publication: {basic['average_citations_per_publication']}")
                
                # Top journals
                top_journals = pub_analytics['top_journals']
                print(f"\n📖 Top 5 Journals:")
                for journal, count in list(top_journals.items())[:5]:
                    print(f"   • {journal}: {count} publications")
            else:
                print(f"❌ Error getting publication analytics: {pub_analytics['error']}")
            
            print(f"\n✅ Analytics demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in analytics: {e}")
    
    def demonstrate_caching(self):
        """Demonstrate caching functionality"""
        print("\n" + "="*60)
        print("⚡ CACHING FUNCTIONALITY DEMONSTRATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
        
        try:
            # Get cache statistics
            print("\n📊 Cache Statistics")
            redis_client = self.db_manager.redis.client
            info = redis_client.info()
            
            print(f"   • Used Memory: {info.get('used_memory_human', 'Unknown')}")
            print(f"   • Connected Clients: {info.get('connected_clients', 'Unknown')}")
            print(f"   • Total Commands Processed: {info.get('total_commands_processed', 'Unknown')}")
            
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            hit_rate = hits / max(hits + misses, 1) * 100
            print(f"   • Cache Hit Rate: {hit_rate:.1f}%")
            
            # Demonstrate caching with a researcher profile
            print(f"\n🎯 Demonstrating Caching with Researcher Profile")
            researchers = self.db_manager.mongodb.search_researchers({}, limit=1)
            
            if researchers:
                researcher_id = researchers[0]["_id"]
                researcher_name = f"{researchers[0]['personal_info']['first_name']} {researchers[0]['personal_info']['last_name']}"
                
                print(f"   Researcher: {researcher_name}")
                
                # First request (should be cache miss)
                print(f"   First request (cache miss expected)...")
                profile1 = self.query_engine.get_researcher_profile_complete(researcher_id)
                cache_status1 = profile1.get('cache_status', 'unknown')
                print(f"   Cache status: {cache_status1}")
                
                # Second request (should be cache hit)
                print(f"   Second request (cache hit expected)...")
                profile2 = self.query_engine.get_researcher_profile_complete(researcher_id)
                cache_status2 = profile2.get('cache_status', 'unknown')
                print(f"   Cache status: {cache_status2}")
                
                if cache_status1 == 'miss' and cache_status2 == 'hit':
                    print(f"   ✅ Caching working correctly!")
                else:
                    print(f"   ⚠️  Unexpected cache behavior")
            
            print(f"\n✅ Caching demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in caching demonstration: {e}")
    
    def demonstrate_database_operations(self):
        """Demonstrate basic CRUD operations"""
        print("\n" + "="*60)
        print("🗃️  DATABASE OPERATIONS DEMONSTRATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
        
        try:
            # MongoDB operations
            print("\n📄 MongoDB Operations:")
            researchers = self.db_manager.mongodb.search_researchers({}, limit=3)
            print(f"   • Retrieved {len(researchers)} researchers from MongoDB")
            
            if researchers:
                sample_researcher = researchers[0]
                print(f"   • Sample researcher: {sample_researcher['personal_info']['first_name']} {sample_researcher['personal_info']['last_name']}")
                print(f"   • Department: {sample_researcher['academic_profile']['department_id']}")
                print(f"   • Position: {sample_researcher['academic_profile']['position']}")
            
            # Neo4j operations
            print(f"\n🕸️  Neo4j Operations:")
            if researchers:
                sample_id = researchers[0]['_id']
                collaborators = self.db_manager.neo4j.find_collaborators(sample_id, max_depth=1)
                print(f"   • Found {len(collaborators)} direct collaborators")
                
                if collaborators:
                    print(f"   • Sample collaborator: {collaborators[0].get('name', 'Unknown')}")
            
            # Redis operations
            print(f"\n⚡ Redis Operations:")
            redis_client = self.db_manager.redis.client
            
            # Test cache operations
            test_key = "demo:test_key"
            test_value = {"demo": "data", "timestamp": datetime.utcnow().isoformat()}
            
            # Set
            redis_client.setex(test_key, 60, json.dumps(test_value))
            print(f"   • Set cache key: {test_key}")
            
            # Get
            cached_value = redis_client.get(test_key)
            if cached_value:
                print(f"   • Retrieved cached value: ✅")
            else:
                print(f"   • Retrieved cached value: ❌")
            
            # Delete
            redis_client.delete(test_key)
            print(f"   • Deleted cache key: {test_key}")
            
            # Cassandra operations
            print(f"\n📊 Cassandra Operations:")
            try:
                cassandra_analytics = self.db_manager.cassandra.get_department_analytics("dept_cs", days=7)
                print(f"   • Retrieved {len(cassandra_analytics)} days of analytics data")
                if cassandra_analytics:
                    latest = cassandra_analytics[0]
                    print(f"   • Latest analytics: {latest.get('analytics_date', 'Unknown')}")
            except Exception as e:
                print(f"   • Cassandra operations: ⚠️  {str(e)[:50]}...")
            
            print(f"\n✅ Database operations demonstration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in database operations: {e}")
    
    def add_new_project(self):
        """Interactive guide to add a new project"""
        print("\n" + "="*60)
        print("✏️  ADD NEW PROJECT")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
            
        try:
            print("\nPlease enter project details:")
            title = input("   Title: ").strip()
            if not title:
                print("❌ Title is required")
                return
                
            description = input("   Description: ").strip()
            status = input("   Status (active/completed/planned) [active]: ").strip() or "active"
            
            # Simple researcher assignment
            pi_name = input("   Principal Investigator Name (Search): ").strip()
            pi_id = None
            
            if pi_name:
                researchers = self.db_manager.mongodb.search_researchers({
                    "$or": [
                        {"personal_info.first_name": {"$regex": pi_name, "$options": "i"}},
                        {"personal_info.last_name": {"$regex": pi_name, "$options": "i"}}
                    ]
                }, limit=5)
                
                if researchers:
                    print(f"\n   Found {len(researchers)} matches:")
                    for i, r in enumerate(researchers, 1):
                        name = f"{r['personal_info']['first_name']} {r['personal_info']['last_name']}"
                        dept = r['academic_profile']['department_id']
                        print(f"   {i}. {name} ({dept})")
                    
                    try:
                        choice = int(input("\n   Select Researcher number (0 for none): "))
                        if 1 <= choice <= len(researchers):
                            pi_id = researchers[choice-1]['_id']
                    except ValueError:
                        pass
            
            project_data = {
                "title": title,
                "description": description,
                "status": status,
                "participants": {
                    "principal_investigators": [],
                    "co_investigators": []
                },
                "metadata": {
                    "created_by": "cli_user"
                }
            }
            
            if pi_id:
                project_data["participants"]["principal_investigators"].append({
                    "researcher_id": pi_id,
                    "role": "lead_pi",
                    "start_date": datetime.utcnow().isoformat()
                })
                
            project_id = self.db_manager.create_project_comprehensive(project_data)
            print(f"\n✅ Project created successfully! ID: {project_id}")
            
        except Exception as e:
            print(f"❌ Error creating project: {e}")

    def add_new_publication(self):
        """Interactive guide to add a new publication"""
        print("\n" + "="*60)
        print("📝 ADD NEW PUBLICATION")
        print("="*60)
        
        if not self.connected:
            print("❌ Please connect to databases first")
            return
            
        try:
            print("\nPlease enter publication details:")
            title = input("   Title: ").strip()
            if not title:
                print("❌ Title is required")
                return
                
            pub_type = input("   Type (journal_article/conference_paper) [journal_article]: ").strip() or "journal_article"
            journal = input("   Journal/Conference Name: ").strip()
            year = input("   Year [2024]: ").strip() or "2024"
            
            # Multiple authors
            authors = []
            while True:
                search_name = input("\n   Add Author (Name Search, or empty to finish): ").strip()
                if not search_name:
                    break
                    
                researchers = self.db_manager.mongodb.search_researchers({
                    "$or": [
                        {"personal_info.first_name": {"$regex": search_name, "$options": "i"}},
                        {"personal_info.last_name": {"$regex": search_name, "$options": "i"}}
                    ]
                }, limit=5)
                
                if researchers:
                    for i, r in enumerate(researchers, 1):
                        name = f"{r['personal_info']['first_name']} {r['personal_info']['last_name']}"
                        print(f"      {i}. {name}")
                        
                    try:
                        choice = int(input("      Select Author number: "))
                        if 1 <= choice <= len(researchers):
                            authors.append({
                                "researcher_id": researchers[choice-1]['_id'],
                                "author_order": len(authors) + 1,
                                "contribution": "author"
                            })
                            print("      ✅ Author added")
                    except ValueError:
                        pass
                else:
                    print("      No researchers found.")
            
            pub_data = {
                "title": title,
                "publication_type": pub_type,
                "bibliographic_info": {
                    "journal": journal,
                    "publication_date": f"{year}-01-01"
                },
                "authors": authors,
                "metrics": {
                    "citation_count": 0
                }
            }
            
            pub_id = self.db_manager.create_publication_comprehensive(pub_data)
            print(f"\n✅ Publication created successfully! ID: {pub_id}")
            
        except Exception as e:
            print(f"❌ Error creating publication: {e}")

    def update_researcher(self):
        """Interactive update researcher"""
        print("\n" + "="*50)
        print("✏️  UPDATE RESEARCHER")
        print("="*50)
        
        if not self.connected:
            print("❌ Not connected to databases")
            return
            
        try:
            # List some researchers
            researchers = self.db_manager.mongodb.search_researchers({}, limit=5)
            print("\n📋 First 5 researchers:")
            for r in researchers:
                name = f"{r.get('personal_info', {}).get('first_name', '')} {r.get('personal_info', {}).get('last_name', '')}"
                print(f"  - {r['_id']}: {name}")
            
            researcher_id = input("\n> Enter researcher ID to update: ").strip()
            
            if not researcher_id:
                print("❌ Researcher ID required")
                return
            
            researcher = self.db_manager.mongodb.get_researcher(researcher_id)
            if not researcher:
                print(f"❌ Researcher {researcher_id} not found")
                return
            
            print(f"\n📄 Current data:")
            personal = researcher.get('personal_info', {})
            print(f"  Name: {personal.get('first_name', '')} {personal.get('last_name', '')}")
            print(f"  Email: {personal.get('email', '')}")
            academic = researcher.get('academic_profile', {})
            print(f"  Department: {academic.get('department_id', '')}")
            print(f"  Position: {academic.get('position', '')}")
            
            print("\n📝 Enter new values (leave blank to keep current):")
            
            update_data = {}
            
            new_first = input(f"  First name [{personal.get('first_name', '')}]: ").strip()
            if new_first:
                update_data['personal_info.first_name'] = new_first
                
            new_last = input(f"  Last name [{personal.get('last_name', '')}]: ").strip()
            if new_last:
                update_data['personal_info.last_name'] = new_last
                
            new_email = input(f"  Email [{personal.get('email', '')}]: ").strip()
            if new_email:
                update_data['personal_info.email'] = new_email
                
            new_position = input(f"  Position [{academic.get('position', '')}]: ").strip()
            if new_position:
                update_data['academic_profile.position'] = new_position
            
            if update_data:
                success = self.db_manager.update_researcher_comprehensive(researcher_id, update_data)
                if success:
                    print(f"\n✅ Researcher {researcher_id} updated successfully!")
                else:
                    print(f"\n❌ Failed to update researcher {researcher_id}")
            else:
                print("\n⚠️ No changes made")
                
        except Exception as e:
            print(f"❌ Error updating researcher: {e}")

    def delete_researcher(self):
        """Interactive delete researcher"""
        print("\n" + "="*50)
        print("🗑️  DELETE RESEARCHER")
        print("="*50)
        
        if not self.connected:
            print("❌ Not connected to databases")
            return
            
        try:
            # List some researchers
            researchers = self.db_manager.mongodb.search_researchers({}, limit=5)
            print("\n📋 First 5 researchers:")
            for r in researchers:
                name = f"{r.get('personal_info', {}).get('first_name', '')} {r.get('personal_info', {}).get('last_name', '')}"
                print(f"  - {r['_id']}: {name}")
            
            researcher_id = input("\n> Enter researcher ID to delete: ").strip()
            
            if not researcher_id:
                print("❌ Researcher ID required")
                return
            
            researcher = self.db_manager.mongodb.get_researcher(researcher_id)
            if not researcher:
                print(f"❌ Researcher {researcher_id} not found")
                return
            
            name = f"{researcher.get('personal_info', {}).get('first_name', '')} {researcher.get('personal_info', {}).get('last_name', '')}"
            
            confirm = input(f"\n⚠️ Are you sure you want to delete '{name}' ({researcher_id})? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                success = self.db_manager.delete_researcher_comprehensive(researcher_id)
                if success:
                    print(f"\n✅ Researcher {researcher_id} deleted from all databases!")
                else:
                    print(f"\n❌ Failed to delete researcher {researcher_id}")
            else:
                print("\n⚠️ Deletion cancelled")
                
        except Exception as e:
            print(f"❌ Error deleting researcher: {e}")

    def add_supervision(self):
        """Interactive add supervision relationship"""
        print("\n" + "="*50)
        print("🎓 ADD SUPERVISION RELATIONSHIP")
        print("="*50)
        
        if not self.connected:
            print("❌ Not connected to databases")
            return
            
        try:
            # List some researchers
            researchers = self.db_manager.mongodb.search_researchers({}, limit=10)
            print("\n📋 Available researchers:")
            for r in researchers:
                name = f"{r.get('personal_info', {}).get('first_name', '')} {r.get('personal_info', {}).get('last_name', '')}"
                position = r.get('academic_profile', {}).get('position', '')
                print(f"  - {r['_id']}: {name} ({position})")
            
            supervisor_id = input("\n> Enter SUPERVISOR ID: ").strip()
            student_id = input("> Enter STUDENT ID: ").strip()
            
            if not supervisor_id or not student_id:
                print("❌ Both IDs are required")
                return
            
            print("\n📋 Supervision types:")
            print("  1. phd - PhD Supervision")
            print("  2. masters - Masters Supervision")
            print("  3. postdoc - Postdoc Supervision")
            
            sup_type = input("> Supervision type [phd]: ").strip() or "phd"
            
            success = self.db_manager.neo4j.create_supervision_relationship(
                supervisor_id, student_id, sup_type
            )
            
            if success:
                print(f"\n✅ Supervision relationship created!")
                print(f"   {supervisor_id} SUPERVISES {student_id} (type: {sup_type})")
            else:
                print("\n❌ Failed to create supervision relationship")
                
        except Exception as e:
            print(f"❌ Error creating supervision: {e}")

    def demonstrate_system_statistics(self):
        """Demonstrate system statistics from all databases"""
        print("\n" + "="*50)
        print("📊 SYSTEM STATISTICS")
        print("="*50)
        
        if not self.connected:
            print("❌ Not connected to databases")
            return
            
        try:
            stats = self.db_manager.get_system_statistics()
            
            print("\n🗄️  MongoDB Statistics:")
            mongodb = stats.get('mongodb', {})
            print(f"  • Researchers: {mongodb.get('researchers_count', 0)}")
            print(f"  • Projects: {mongodb.get('projects_count', 0)}")
            print(f"  • Publications: {mongodb.get('publications_count', 0)}")
            
            print("\n🕸️  Neo4j Statistics:")
            neo4j = stats.get('neo4j', {})
            print(f"  • Total Researchers: {neo4j.get('total_researchers', 0)}")
            print(f"  • Total Collaborations: {neo4j.get('total_collaborations', 0)}")
            print(f"  • Total Supervisions: {neo4j.get('total_supervisions', 0)}")
            print(f"  • Total Mentorships: {neo4j.get('total_mentorships', 0)}")
            print(f"  • Avg Collaborations/Researcher: {neo4j.get('avg_collaborations_per_researcher', 0)}")
            
            if neo4j.get('most_connected'):
                print("\n  Top 5 Most Connected Researchers:")
                for r in neo4j.get('most_connected', []):
                    print(f"    - {r.get('name', r.get('id', 'Unknown'))}: {r.get('connections', 0)} connections")
            
            print("\n💾 Redis Statistics:")
            redis_stats = stats.get('redis', {})
            print(f"  • Used Memory: {redis_stats.get('used_memory', 'N/A')}")
            print(f"  • Keyspace Hits: {redis_stats.get('keyspace_hits', 0)}")
            print(f"  • Keyspace Misses: {redis_stats.get('keyspace_misses', 0)}")
            print(f"  • Cache Hit Rate: {redis_stats.get('hit_rate', 0)}%")
            
            print("\n📈 Summary:")
            summary = stats.get('summary', {})
            print(f"  • Total Entities: {summary.get('total_entities', 0)}")
            print(f"  • Total Collaborations: {summary.get('total_collaborations', 0)}")
            print(f"  • Cache Hit Rate: {summary.get('cache_hit_rate', 0)}%")
            
        except Exception as e:
            print(f"❌ Error getting system statistics: {e}")

    def run_interactive_mode(self):
        """Run interactive CLI mode"""
        print("\n" + "="*80)
        print("🏛️  RESEARCH COLLABORATION SYSTEM - INTERACTIVE CLI")
        print("="*80)
        print("This CLI demonstrates the multi-database research collaboration system.")
        print("Features: MongoDB (documents), Neo4j (graphs), Redis (cache), Cassandra (analytics)")
        
        while True:
            if not self.connected:
                print("\n🔌 Not connected to databases. Please connect first.")
                if not self.connect():
                    continue
            
            print("\n" + "-"*60)
            print("📖 Read/Query:")
            print("  1. profile [id]   - Get complete researcher profile")
            print("  2. search         - Advanced search demonstration")
            print("  3. collaboration  - Collaboration network analysis")
            print("  4. analytics      - Analytics and reports")
            print("  5. cache          - Caching demonstration")
            print("  6. database       - Database operations demo")
            print("  7. stats          - System statistics")
            print("")
            print("✏️  Create/Update/Delete (CRUD):")
            print("  8. add_project    - Create new project")
            print("  9. add_pub        - Create new publication")
            print("  10. update        - Update researcher")
            print("  11. delete        - Delete researcher")
            print("  12. supervise     - Add supervision relationship")
            print("")
            print("⚙️  System:")
            print("  13. status        - Check database status")
            print("  14. connect       - Reconnect to databases")
            print("  15. disconnect    - Disconnect from databases")
            print("  0. quit           - Exit CLI")
            print("-"*60)
            
            try:
                command = input("\n> Enter command: ").strip().lower()
                
                if command == "quit" or command == "0":
                    print("👋 Goodbye!")
                    break
                elif command.startswith("profile") or command == "1":
                    parts = command.split()
                    researcher_id = parts[1] if len(parts) > 1 else None
                    self.demonstrate_complete_researcher_profile(researcher_id)
                elif command == "search" or command == "2":
                    self.demonstrate_advanced_search()
                elif command == "collaboration" or command == "3":
                    self.demonstrate_collaboration_analysis()
                elif command == "analytics" or command == "4":
                    self.demonstrate_analytics()
                elif command == "cache" or command == "5":
                    self.demonstrate_caching()
                elif command == "database" or command == "6":
                    self.demonstrate_database_operations()
                elif command == "stats" or command == "7":
                    self.demonstrate_system_statistics()
                elif command == "add_project" or command == "8":
                    self.add_new_project()
                elif command == "add_pub" or command == "9":
                    self.add_new_publication()
                elif command == "update" or command == "10":
                    self.update_researcher()
                elif command == "delete" or command == "11":
                    self.delete_researcher()
                elif command == "supervise" or command == "12":
                    self.add_supervision()
                elif command == "status" or command == "13":
                    self.show_database_status()
                elif command == "connect" or command == "14":
                    self.connect()
                elif command == "disconnect" or command == "15":
                    self.disconnect()
                else:
                    print(f"❓ Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_database_status(self):
        """Show database connection status"""
        print("\n" + "="*50)
        print("🗄️  DATABASE STATUS")
        print("="*50)
        
        if not self.connected:
            print("❌ Not connected to databases")
            return
        
        status = {
            "MongoDB": "disconnected",
            "Neo4j": "disconnected",
            "Redis": "disconnected",
            "Cassandra": "disconnected"
        }
        
        # Test each connection
        try:
            self.db_manager.mongodb.client.admin.command('ping')
            status["MongoDB"] = "connected ✅"
        except:
            status["MongoDB"] = "disconnected ❌"
        
        try:
            with self.db_manager.neo4j.driver.session() as session:
                session.run("RETURN 1")
            status["Neo4j"] = "connected ✅"
        except:
            status["Neo4j"] = "disconnected ❌"
        
        try:
            self.db_manager.redis.client.ping()
            status["Redis"] = "connected ✅"
        except:
            status["Redis"] = "disconnected ❌"
        
        try:
            self.db_manager.cassandra.session.execute("SELECT 1")
            status["Cassandra"] = "connected ✅"
        except:
            status["Cassandra"] = "disconnected ❌"
        
        for db, db_status in status.items():
            print(f"   {db}: {db_status}")
        
        all_connected = all("connected" in s for s in status.values())
        print(f"\nOverall Status: {'✅ All databases connected' if all_connected else '⚠️  Some databases disconnected'}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Research Collaboration System CLI")
    parser.add_argument("--mode", choices=["interactive", "demo"], default="interactive",
                       help="CLI mode: interactive or demo")
    parser.add_argument("--researcher-id", type=str, help="Researcher ID for profile demo")
    
    args = parser.parse_args()
    
    cli = ResearchCLI()
    
    try:
        if args.mode == "demo":
            # Run demonstration mode
            print("🎬 Running demonstration mode...")
            if cli.connect():
                cli.demonstrate_complete_researcher_profile(args.researcher_id)
                cli.demonstrate_advanced_search()
                cli.demonstrate_collaboration_analysis()
                cli.demonstrate_analytics()
                cli.demonstrate_caching()
                cli.demonstrate_database_operations()
                print("\n🎉 All demonstrations completed!")
            else:
                print("❌ Failed to connect to databases")
        else:
            # Run interactive mode
            cli.run_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        cli.disconnect()


if __name__ == "__main__":
    main()
