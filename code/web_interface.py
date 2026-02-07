#!/usr/bin/env python3
"""
Flask Web Interface for Research Collaboration System
Simple web UI for demonstrating database operations
"""

import os
import sys
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename
from pymongo.errors import DuplicateKeyError
import pandas as pd

from database_manager import ResearchDatabaseManager, load_database_config
from query_engine import ResearchQueryEngine
from report_generator import ReportGenerator, DataExporter

# Add code directory to path
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Initialize Flask app
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'research_collab_system_secret_key_2024'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "يرجى تسجيل الدخول للوصول إلى هذه الصفحة."
login_manager.login_message_category = "info"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database connections
db_manager: Optional[ResearchDatabaseManager] = None
query_engine: Optional[ResearchQueryEngine] = None


last_db_error = None

class User(UserMixin):
    """User class for Flask-Login"""
    def __init__(self, user_id, email, full_name, role='user'):
        self.id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    """Load user from MongoDB for Flask-Login"""
    if not db_manager or not db_manager.mongodb:
        return None
    user_data = db_manager.mongodb.get_user_by_id(user_id)
    if user_data:
        return User(
            user_id=user_data['_id'],
            email=user_data['email'],
            full_name=user_data.get('full_name', ''),
            role=user_data.get('role', 'user')
        )
    return None

def init_databases():
    """Initialize database connections"""
    global db_manager, query_engine, last_db_error
    try:
        config = load_database_config()
        db_manager = ResearchDatabaseManager(config)
        
        if db_manager.connect_all():
            query_engine = ResearchQueryEngine(db_manager)
            logger.info("Database connections established successfully")
            return True
        else:
            last_db_error = "connect_all returned False"
            logger.error("Failed to establish database connections")
            return False
    except Exception as e:
        last_db_error = str(e)
        logger.error(f"Database initialization failed: {e}")
        return False


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # Ensure database is connected
        if not query_engine:
            if not init_databases():
                flash('نظام قواعد البيانات غير متصل حالياً. يرجى المحاولة لاحقاً.', 'danger')
                return render_template('login.html')

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        try:
            user_data = db_manager.mongodb.get_user_by_email(email)
            
            if not user_data or not db_manager.mongodb.verify_password(user_data['password'], password):
                flash('خطأ في البريد الإلكتروني أو كلمة المرور. يرجى المحاولة مرة أخرى.', 'danger')
                return render_template('login.html')
                
            user = User(
                user_id=user_data['_id'],
                email=user_data['email'],
                full_name=user_data.get('full_name', ''),
                role=user_data.get('role', 'user')
            )
            login_user(user, remember=remember)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('حدث خطأ أثناء تسجيل الدخول. يرجى المحاولة لاحقاً.', 'danger')
            return render_template('login.html')
        
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        # Ensure database is connected
        if not query_engine:
            if not init_databases():
                flash('نظام قواعد البيانات غير متصل حالياً. يرجى المحاولة لاحقاً.', 'danger')
                return render_template('signup.html')

        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة!', 'danger')
            return render_template('signup.html')
            
        try:
            # Check if user already exists
            existing_user = db_manager.mongodb.get_user_by_email(email)
            if existing_user:
                flash('البريد الإلكتروني مسجل بالفعل. يرجى تسجيل الدخول.', 'warning')
                return redirect(url_for('login'))
                
            # Create new user
            new_user_data = {
                'email': email,
                'full_name': full_name,
                'password': password,  # Will be hashed in MongoDBManager.create_user
                'role': 'user'
            }
            
            user_id = db_manager.mongodb.create_user(new_user_data)
            flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Signup error: {e}")
            flash(f'فشل إنشاء الحساب: {e}', 'danger')
            
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Handle user profile page"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        
        update_data = {
            'full_name': full_name,
            'email': email
        }
        
        # Check if email is already taken by another user
        existing_user = db_manager.mongodb.get_user_by_email(email)
        if existing_user and existing_user['_id'] != current_user.id:
            flash('البريد الإلكتروني مستخدم بالفعل من قبل شخص آخر.', 'danger')
        else:
            if db_manager.mongodb.update_user(current_user.id, update_data):
                # Update current_user object in session
                current_user.full_name = full_name
                current_user.email = email
                flash('تم تحديث الملف الشخصي بنجاح!', 'success')
            else:
                flash('فشل تحديث البيانات.', 'danger')
                
    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handle user settings and password updates"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        user_data = db_manager.mongodb.get_user_by_id(current_user.id)
        if not db_manager.mongodb.verify_password(user_data['password'], current_password):
            flash('كلمة المرور الحالية غير صحيحة.', 'danger')
        elif new_password != confirm_password:
            flash('كلمات المرور الجديدة غير متطابقة.', 'danger')
        else:
            if db_manager.mongodb.update_user(current_user.id, {'password': new_password}):
                flash('تم تغيير كلمة المرور بنجاح!', 'success')
            else:
                flash('فشل تغيير كلمة المرور.', 'danger')
                
    return render_template('settings.html')

@app.route('/activity-status')
@login_required
def activity_status():
    """Handle activity status page (Database Monitoring)"""
    stats = {
        'mongodb': {'status': False, 'count': 0, 'details': {}},
        'neo4j': {'status': False, 'count': 0, 'details': {}},
        'redis': {'status': False, 'count': 0, 'details': {}},
        'cassandra': {'status': False, 'count': 0, 'details': {}}
    }
    
    try:
        # Check MongoDB
        if db_manager and db_manager.mongodb:
            db_manager.mongodb.client.admin.command('ping')
            stats['mongodb']['status'] = True
            stats['mongodb']['count'] = db_manager.mongodb.db.researchers.count_documents({})
            stats['mongodb']['details'] = {'publications': db_manager.mongodb.db.publications.count_documents({})}
            
        # Check Neo4j
        if db_manager and db_manager.neo4j:
            db_manager.neo4j.driver.verify_connectivity()
            stats['neo4j']['status'] = True
            with db_manager.neo4j.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                stats['neo4j']['count'] = result.single()['count']
                
        # Check Redis
        if db_manager and db_manager.redis:
            stats['redis']['status'] = db_manager.redis.client.ping()
            stats['redis']['count'] = len(db_manager.redis.client.keys('*'))
            
        # Check Cassandra
        if db_manager and db_manager.cassandra and db_manager.cassandra.session:
            db_manager.cassandra.session.execute("SELECT now() FROM system.local")
            stats['cassandra']['status'] = True
            # For simplicity, count is 0 or estimated
            stats['cassandra']['count'] = 'Active'
            
    except Exception as e:
        logger.error(f"Error fetching activity status: {e}")
        
    return render_template('activity_status.html', stats=stats)

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with system overview"""
    try:
        if not query_engine:
            # Try to initialize if not available
            if not init_databases():
                flash(f'Database connections not available: {last_db_error}', 'error')
                return redirect(url_for('index'))
        
        # Get system overview
        overview = get_system_overview()
        
        # Get recent activity
        recent_publications = get_recent_publications(limit=5)
        top_departments = get_department_summary()
        
        return render_template('dashboard.html', 
                             overview=overview,
                             recent_publications=recent_publications,
                             top_departments=top_departments)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/researchers')
@login_required
def researchers():
    """Researchers listing page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('index'))
        
        # Get query parameters
        department = request.args.get('department', '')
        search_query = request.args.get('search', '')
        min_h_index = request.args.get('min_h_index', type=int)
        
        # Build search criteria
        criteria = {}
        if department:
            criteria['department'] = department
        if search_query:
            criteria['name_search'] = search_query
        if min_h_index:
            criteria['min_h_index'] = min_h_index
        
        # Search researchers
        if criteria:
            researchers = query_engine.search_researchers_advanced(criteria)
        else:
            # Get all researchers
            researchers = query_engine.db_manager.mongodb.search_researchers({})
        
        # Add collaborator counts
        for researcher in researchers:
            try:
                collaborators = query_engine.db_manager.neo4j.find_collaborators(researcher["_id"], max_depth=1)
                researcher["collaborator_count"] = len(collaborators)
            except:
                researcher["collaborator_count"] = 0
        
        # Get available departments for filter
        departments = ["dept_cs", "dept_bio", "dept_chem", "dept_math", "dept_physics"]
        department_names = {
            "dept_cs": "Computer Science",
            "dept_bio": "Biology", 
            "dept_chem": "Chemistry",
            "dept_math": "Mathematics",
            "dept_physics": "Physics"
        }
        
        return render_template('researchers.html',
                             researchers=researchers,
                             departments=departments,
                             department_names=department_names,
                             current_filters=criteria)
    except Exception as e:
        logger.error(f"Researchers page error: {e}")
        flash(f'Error loading researchers: {str(e)}', 'error')
        return redirect(url_for('index'))



@app.route('/add_researcher', methods=['POST'])
def add_researcher():
    """Add new researcher"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('researchers'))
            
        # Extract form data
        name_parts = request.form.get('name', '').split(' ')
        first_name = name_parts[0] if name_parts else ""
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        researcher_data = {
            "orcid_id": str(uuid.uuid4()), # Generate unique ID at root level
            "personal_info": {
                "first_name": first_name,
                "last_name": last_name,
                "email": request.form.get('email')
            },
            "academic_profile": {
                "department_id": request.form.get('department'),
                "position": request.form.get('field', 'Researcher'),  # Use field as position or default
                "institution": "University"
            },
            "collaboration_metrics": {
                "h_index": 0,
                "total_publications": 0,
                "collaboration_score": 0.0,
                "citations": 0
            }
        }
        
        # Create researcher
        researcher_id = query_engine.db_manager.create_researcher_comprehensive(researcher_data)
        
        flash('Researcher added successfully!', 'success')
        return redirect(url_for('researchers'))
        
    except DuplicateKeyError as e:
        error_msg = str(e)
        if "personal_info.email" in error_msg:
            flash(f'Error: The email address {request.form.get("email")} is already registered.', 'error')
        else:
            flash(f'Error: Duplicate data found. {error_msg}', 'error')
        return redirect(url_for('researchers'))
        
    except Exception as e:
        logger.error(f"Failed to add researcher: {e}")
        flash(f'Error adding researcher: {str(e)}', 'error')
        return redirect(url_for('researchers'))

@app.route('/get_researcher/<researcher_id>')
def get_researcher(researcher_id):
    """Get researcher data as JSON for editing"""
    try:
        if not query_engine:
            return jsonify({"error": "Database connections not available"}), 500
            
        researcher = query_engine.db_manager.mongodb.get_researcher(researcher_id)
        if researcher:
            return jsonify(researcher)
        return jsonify({"error": "Researcher not found"}), 404
        
    except Exception as e:
        logger.error(f"Failed to get researcher: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/edit_researcher/<researcher_id>', methods=['POST'])
def edit_researcher(researcher_id):
    """Update existing researcher"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('researchers'))
            
        # Extract form data
        name_parts = request.form.get('name', '').split(' ')
        first_name = name_parts[0] if name_parts else ""
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        update_data = {
            "personal_info": {
                "first_name": first_name,
                "last_name": last_name,
                "email": request.form.get('email')
            },
            "academic_profile": {
                "department_id": request.form.get('department'),
                "position": request.form.get('field'),
                "institution": "University"
            }
        }
        
        # Update researcher
        query_engine.db_manager.update_researcher_comprehensive(researcher_id, update_data)
        
        flash('Researcher updated successfully!', 'success')
        return redirect(url_for('researchers'))
        
    except Exception as e:
        logger.error(f"Failed to update researcher: {e}")
        flash(f'Error updating researcher: {str(e)}', 'error')
        return redirect(url_for('researchers'))


@app.route('/delete_researcher/<researcher_id>', methods=['POST'])
def delete_researcher(researcher_id):
    """Delete researcher"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('researchers'))
            
        # Delete from MongoDB
        db = query_engine.db_manager.mongodb
        db.db.researchers.delete_one({'_id': researcher_id})
        
        # Delete from Neo4j
        with query_engine.db_manager.neo4j.driver.session() as session:
            session.run("MATCH (r:Researcher {id: $id}) DETACH DELETE r", id=researcher_id)
            
        # Clear cache
        redis_client = query_engine.db_manager.redis.client
        redis_client.delete(f"researcher_profile:{researcher_id}")
        redis_client.delete(f"researcher_stats:{researcher_id}")
        
        flash('Researcher deleted successfully', 'success')
        return redirect(url_for('researchers'))
        
    except Exception as e:
        logger.error(f"Failed to delete researcher: {e}")
        flash(f'Error deleting researcher: {str(e)}', 'error')
        return redirect(url_for('researchers'))

@app.route('/researcher/<researcher_id>')
def researcher_detail(researcher_id):
    """Researcher detail page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('index'))
        
        # Get complete researcher profile
        profile = query_engine.get_researcher_profile_complete(researcher_id)
        
        if "error" in profile:
            flash(f'Researcher not found', 'error')
            return redirect(url_for('researchers'))
        
        # Get collaboration network visualization data
        collaborators = profile.get("collaboration_network", {}).get("collaborators", [])
        
        # Prepare network data for visualization
        network_data = []
        for collab in collaborators[:10]:  # Limit for display
            network_data.append({
                "id": collab.get("id", ""),
                "name": collab.get("name", "Unknown"),
                "h_index": collab.get("h_index", 0),
                "distance": collab.get("distance", 0)
            })
        
        return render_template('researcher_detail.html',
                             profile=profile,
                             network_data=network_data)
    except Exception as e:
        logger.error(f"Researcher detail error: {e}")
        flash(f'Error loading researcher details: {str(e)}', 'error')
        return redirect(url_for('researchers'))


@app.route('/analytics')
@login_required
def analytics():
    """Analytics page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('index'))
        
        # Get department analytics
        departments = ["dept_cs", "dept_bio", "dept_chem", "dept_math", "dept_physics"]
        department_names = {
            "dept_cs": "Computer Science",
            "dept_bio": "Biology", 
            "dept_chem": "Chemistry",
            "dept_math": "Mathematics",
            "dept_physics": "Physics"
        }
        
        dept_analytics = {}
        for dept in departments:
            try:
                analytics = query_engine.get_department_analytics(dept, days=30)
                if "error" not in analytics:
                    dept_analytics[dept] = analytics
            except Exception as e:
                logger.warning(f"Failed to get analytics for {dept}: {e}")
        
        # Get publication analytics
        try:
            pub_analytics = query_engine.get_publication_analytics(365)
        except Exception as e:
            pub_analytics = {"error": str(e)}
        
        # Get collaboration pairs
        try:
            collaboration_pairs = query_engine.find_collaboration_pairs(min_collaborations=2)
            collaboration_pairs = collaboration_pairs[:10]  # Limit for display
        except Exception as e:
            collaboration_pairs = []
        
        # Get system overview
        overview = get_system_overview()

        # Prepare chart data
        chart_data = {
            "dept_names": [department_names[d] for d in dept_analytics.keys()],
            "pub_counts": [stats.get('basic_metrics', {}).get('total_publications', 0) for stats in dept_analytics.values()],
            "researcher_counts": [stats.get('basic_metrics', {}).get('total_researchers', 0) for stats in dept_analytics.values()],
            "journal_names": list(pub_analytics.get('top_journals', {}).keys()),
            "journal_counts": list(pub_analytics.get('top_journals', {}).values())
        }

        return render_template('analytics.html',
                             overview=overview,
                             dept_analytics=dept_analytics,
                             department_names=department_names,
                             pub_analytics=pub_analytics,
                             collaboration_pairs=collaboration_pairs,
                             chart_data=chart_data)
    except Exception as e:
        logger.error(f"Analytics page error: {e}")
        flash(f'Error loading analytics: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/api/researchers/search', methods=['POST'])
def api_search_researchers():
    """API endpoint for researcher search"""
    try:
        if not query_engine:
            return jsonify({"error": "Database connections not available"}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No search criteria provided"}), 400
        
        results = query_engine.search_researchers_advanced(data)
        return jsonify({
            "results": results,
            "count": len(results),
            "query": data
        })
    except Exception as e:
        logger.error(f"API search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/projects')
@login_required
def projects():
    """Projects listing page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('index'))
            
        # Get total count
        total_projects = query_engine.db_manager.mongodb.count_documents("projects")
        
        # Sort by creation date descending (newest first)
        projects_list = query_engine.db_manager.mongodb.find_documents(
            "projects", 
            sort_by=[("metadata.creation_date", -1)],
            limit=50
        )
        
        # Enrich PI names for each project
        for project in projects_list:
            if project.get('participants', {}).get('principal_investigators'):
                for pi in project['participants']['principal_investigators']:
                    # Try to get name from project data first (denormalized)
                    # If not found or "Unknown", try to fetch from database
                    if not pi.get('name') or pi.get('name') == "Unknown":
                        try:
                            researcher = query_engine.db_manager.mongodb.get_researcher(pi.get('researcher_id'))
                            if researcher:
                                pi['name'] = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                            else:
                                pi['name'] = "غير معروف"
                        except:
                            pi['name'] = "غير معروف"
        
        return render_template('projects.html', projects=projects_list, total_count=total_projects)
    except Exception as e:
        logger.error(f"Projects error: {e}")
        flash(f'Error loading projects: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/add_project', methods=['POST'])
def add_project():
    """Add new project"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('projects'))
            
        project_data = {
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "status": request.form.get('status', 'active'),
            "participants": {
                "principal_investigators": [],
                "co_investigators": []
            },
            "timeline": {},
            "metadata": {
                "created_by": "web_user",
                "creation_date": datetime.utcnow().isoformat()
            }
        }
        
        # Add timeline dates if provided
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if start_date:
            project_data["timeline"]["start_date"] = start_date
        if end_date:
            project_data["timeline"]["end_date"] = end_date
        
        # Add PI if selected
        pi_id = request.form.get('pi_id')
        if pi_id:
            project_data["participants"]["principal_investigators"].append({
                "researcher_id": pi_id,
                "role": "lead_pi",
                "start_date": datetime.utcnow().isoformat()
            })

        # Add Co-PIs if selected
        co_pi_ids = request.form.getlist('co_pi_ids')
        for co_pi_id in co_pi_ids:
            if co_pi_id != pi_id: # Avoid duplicates
                project_data["participants"]["co_investigators"].append({
                    "researcher_id": co_pi_id,
                    "role": "co_investigator",
                    "start_date": datetime.utcnow().isoformat()
                })
            
        query_engine.db_manager.create_project_comprehensive(project_data)
        flash('Project added successfully!', 'success')
        return redirect(url_for('projects'))
        
    except Exception as e:
        logger.error(f"Failed to add project: {e}")
        flash(f'Error adding project: {str(e)}', 'error')
        return redirect(url_for('projects'))


@app.route('/delete_project/<project_id>', methods=['POST'])
def delete_project_route(project_id):
    """Delete a project"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('projects'))
            
        success = query_engine.db_manager.delete_project_comprehensive(project_id)
        if success:
            flash('Project deleted successfully!', 'success')
        else:
            flash('Failed to delete project', 'error')
            
        return redirect(url_for('projects'))
        
    except Exception as e:
        logger.error(f"Delete project error: {e}")
        flash(f'Error deleting project: {str(e)}', 'error')
        return redirect(url_for('projects'))


@app.route('/project/<project_id>')
@login_required
def project_detail(project_id):
    """Project detail page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('projects'))
            
        project = query_engine.db_manager.mongodb.get_project(project_id)
        
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('projects'))
        
        # Enrich PI names
        if project.get('participants', {}).get('principal_investigators'):
            for pi in project['participants']['principal_investigators']:
                if not pi.get('name') or pi.get('name') == "Unknown":
                    try:
                        researcher = query_engine.db_manager.mongodb.get_researcher(pi['researcher_id'])
                        if researcher:
                            pi['name'] = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                        else:
                            pi['name'] = "غير معروف"
                    except:
                        pi['name'] = "غير معروف"
        
        # Enrich Co-PI names
        if project.get('participants', {}).get('co_investigators'):
            for copi in project['participants']['co_investigators']:
                if not copi.get('name') or copi.get('name') == "Unknown":
                    try:
                        researcher = query_engine.db_manager.mongodb.get_researcher(copi['researcher_id'])
                        if researcher:
                            copi['name'] = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                        else:
                            copi['name'] = "غير معروف"
                    except:
                        copi['name'] = "غير معروف"
            
        return render_template('project_detail.html', project=project)
    except Exception as e:
        logger.error(f"Project detail error: {e}")
        flash(f'Error loading project: {str(e)}', 'error')
        return redirect(url_for('projects'))


@app.route('/get_project/<project_id>')
def get_project(project_id):
    """Get project data for editing (JSON)"""
    try:
        if not query_engine:
            return jsonify({"error": "Database not available"}), 503
            
        project = query_engine.db_manager.mongodb.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Project not found"}), 404
            
        return jsonify(project)
    except Exception as e:
        logger.error(f"Get project error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/edit_project/<project_id>', methods=['POST'])
def edit_project(project_id):
    """Edit project"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('projects'))
        
        update_data = {}
        
        title = request.form.get('title')
        if title:
            update_data['title'] = title
            
        description = request.form.get('description')
        if description:
            update_data['description'] = description
            
        status = request.form.get('status')
        if status:
            update_data['status'] = status
        
        if update_data:
            success = query_engine.db_manager.update_project_comprehensive(project_id, update_data)
            if success:
                flash('Project updated successfully!', 'success')
            else:
                flash('Failed to update project', 'error')
        else:
            flash('No changes made', 'warning')
            
        return redirect(url_for('projects'))
        
    except Exception as e:
        logger.error(f"Edit project error: {e}")
        flash(f'Error updating project: {str(e)}', 'error')
        return redirect(url_for('projects'))


@app.route('/publications')
@login_required
def publications():
    """Publications listing page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('index'))
        
        # Get publications sorted by date
        publications_list = query_engine.db_manager.mongodb.find_documents(
            "publications", 
            sort_by=[("bibliographic_info.publication_date", -1)],
            limit=50
        )
        
        # Ensure each publication has required fields with safe defaults
        for pub in publications_list:
            # Ensure bibliographic_info exists
            if 'bibliographic_info' not in pub or pub['bibliographic_info'] is None:
                pub['bibliographic_info'] = {}
            
            # Ensure metrics exists
            if 'metrics' not in pub or pub['metrics'] is None:
                pub['metrics'] = {'citation_count': 0}
            
            # Ensure publication_type exists
            if 'publication_type' not in pub or pub['publication_type'] is None:
                pub['publication_type'] = 'unknown'
                
            # Ensure title exists
            if 'title' not in pub or not pub['title']:
                pub['title'] = 'بدون عنوان'
        
        return render_template('publications.html', publications=publications_list)
    except Exception as e:
        logger.error(f"Publications error: {e}")
        flash(f'Error loading publications: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/add_publication', methods=['POST'])
def add_publication():
    """Add new publication"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('publications'))
            
        pub_data = {
            "title": request.form.get('title'),
            "publication_type": request.form.get('type', 'journal_article'),
            "bibliographic_info": {
                "journal": request.form.get('journal'),
                "publication_date": f"{request.form.get('year', '2024')}-01-01"
            },
            "authors": [],
            "metrics": {
                "citation_count": 0
            }
        }
        
        # Add authors if selected
        author_ids = request.form.getlist('author_ids')
        for i, author_id in enumerate(author_ids):
            pub_data["authors"].append({
                "researcher_id": author_id,
                "author_order": i + 1,
                "contribution": "author"
            })
            
        query_engine.db_manager.create_publication_comprehensive(pub_data)
        flash('Publication added successfully!', 'success')
        return redirect(url_for('publications'))
        
    except Exception as e:
        logger.error(f"Failed to add publication: {e}")
        flash(f'Error adding publication: {str(e)}', 'error')
        return redirect(url_for('publications'))

@app.route('/get_publication/<pub_id>')
def get_publication_json(pub_id):
    """Get publication data for editing (JSON)"""
    try:
        if not query_engine:
            return jsonify({"error": "Database not available"}), 503
            
        publication = query_engine.db_manager.mongodb.db.publications.find_one({"_id": pub_id})
        
        if not publication:
            return jsonify({"error": "Publication not found"}), 404
            
        # Convert ObjectId to string
        publication['_id'] = str(publication['_id'])
            
        return jsonify(publication)
    except Exception as e:
        logger.error(f"Get publication error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/edit_publication/<pub_id>', methods=['POST'])
def edit_publication(pub_id):
    """Edit publication"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('publications'))
        
        update_data = {}
        
        # Build update dictionary
        title = request.form.get('title')
        if title:
            update_data['title'] = title
            
        pub_type = request.form.get('type')
        if pub_type:
            update_data['publication_type'] = pub_type
            
        # Handle bibliographic info updates
        journal = request.form.get('journal')
        year = request.form.get('year')
        
        if journal or year:
            # We need to use dot notation for nested updates in MongoDB or fetch-update-save
            # For simplicity, let's use $set with dot notation
            if journal:
                update_data['bibliographic_info.journal'] = journal
            if year:
                update_data['bibliographic_info.publication_date'] = f"{year}-01-01"
        
        if update_data:
            # Use the update_publication method from DatabaseManager
            query_engine.db_manager.mongodb.update_publication(pub_id, update_data)
            flash('Publication updated successfully!', 'success')
        else:
            flash('No changes made', 'warning')
            
        return redirect(url_for('publications'))
        
    except Exception as e:
        logger.error(f"Edit publication error: {e}")
        flash(f'Error updating publication: {str(e)}', 'error')
        return redirect(url_for('publications'))

@app.route('/delete_publication/<pub_id>', methods=['POST'])
def delete_publication_route(pub_id):
    """Delete a publication"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('publications'))
            
        # Use the delete_publication method
        success = query_engine.db_manager.mongodb.delete_publication(pub_id)
        
        if success:
            flash('Publication deleted successfully!', 'success')
        else:
            flash('Failed to delete publication', 'error')
            
        return redirect(url_for('publications'))
        
    except Exception as e:
        logger.error(f"Delete publication error: {e}")
        flash(f'Error deleting publication: {str(e)}', 'error')
        return redirect(url_for('publications'))

@app.route('/publication/<pub_id>')
@login_required
def publication_detail(pub_id):
    """Publication detail page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('publications'))
            
        # Get publication details
        publication = query_engine.db_manager.mongodb.db.publications.find_one({"_id": pub_id})
        
        if not publication:
            flash('Publication not found', 'error')
            return redirect(url_for('publications'))
        
        # Convert ObjectId to string if needed
        publication['_id'] = str(publication['_id'])
        
        # Ensure bibliographic_info exists with defaults
        if 'bibliographic_info' not in publication or publication['bibliographic_info'] is None:
            publication['bibliographic_info'] = {}
        
        # Ensure metrics exists with defaults
        if 'metrics' not in publication or publication['metrics'] is None:
            publication['metrics'] = {'citation_count': 0}
        
        # Ensure publication_type exists
        if 'publication_type' not in publication or not publication['publication_type']:
            publication['publication_type'] = 'unknown'
        
        # Ensure authors list exists
        if 'authors' not in publication or publication['authors'] is None:
            publication['authors'] = []
            
        # Enrich author names
        for author in publication.get("authors", []):
            try:
                researcher = query_engine.db_manager.mongodb.get_researcher(author.get("researcher_id"))
                if researcher:
                    author["name"] = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                else:
                    author["name"] = "Unknown"
            except:
                author["name"] = "Unknown"

        return render_template('publication_detail.html', publication=publication)
    except Exception as e:
        logger.error(f"Publication detail error: {e}")
        flash(f'Error loading publication: {str(e)}', 'error')
        return redirect(url_for('publications'))

@app.route('/download_publication_pdf/<pub_id>')
def download_publication_pdf(pub_id):
    """Download PDF for a specific publication"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('publications'))
            
        publication = query_engine.db_manager.mongodb.db.publications.find_one({"_id": pub_id})
        if not publication:
            flash('Publication not found', 'error')
            return redirect(url_for('publications'))

        # Enrich author names for the report
        if 'authors' in publication and publication['authors']:
            for author in publication["authors"]:
                try:
                    researcher = query_engine.db_manager.mongodb.get_researcher(author.get("researcher_id"))
                    if researcher:
                        author["name"] = f"{researcher['personal_info']['first_name']} {researcher['personal_info']['last_name']}"
                    else:
                        author["name"] = "Unknown"
                except:
                    author["name"] = "Unknown"

        gen, _ = get_report_generator()
        if not gen:
            flash('Report generator not available', 'error')
            return redirect(url_for('publication_detail', pub_id=pub_id))
            
        buffer = gen.generate_single_publication_report(publication)
        
        # Create a clean filename
        safe_title = "".join([c for c in publication.get('title', 'publication') if c.isalnum() or c==' ']).rstrip()
        filename = f"{safe_title[:30]}.pdf"
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Publication PDF download error: {e}")
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('publication_detail', pub_id=pub_id))



@app.route('/collaboration')
def collaboration():
    """Collaboration network page"""
    try:
        if not query_engine:
            flash('Database connections not available', 'error')
            return redirect(url_for('index'))
            
        # Fetch full network data for visualization
        network_data = query_engine.get_collaboration_network()
        
        # Get network statistics
        stats = {
            "total_researchers": len(network_data.get('nodes', [])),
            "total_collaborations": len(network_data.get('edges', [])),
            "total_supervisions": sum(1 for e in network_data.get('edges', []) if e.get('type') == 'SUPERVISES'),
            "avg_collaborations_per_researcher": 0,
            "most_connected": []
        }
        
        if stats["total_researchers"] > 0:
            stats["avg_collaborations_per_researcher"] = (stats["total_collaborations"] * 2) / stats["total_researchers"]
            
        # Get collaboration pairs for additional info
        collaboration_pairs = query_engine.find_collaboration_pairs(min_collaborations=2)
        
        return render_template('network_visualization.html', 
                             network_data=network_data,
                             stats=stats,
                             collaboration_pairs=collaboration_pairs)
    except Exception as e:
        logger.error(f"Collaboration page error: {e}")
        flash(f'Error loading collaboration network: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/cache/demo')
def cache_demo():
    """Demonstrate caching functionality"""
    try:
        if not query_engine:
            return jsonify({"error": "Database connections not available"}), 500
            
        # Get sample researcher
        researchers = query_engine.db_manager.mongodb.search_researchers({}, limit=1)
        if not researchers:
            return jsonify({"error": "No researchers found"}), 404
            
        researcher_id = researchers[0]["_id"]
        
        # Time the requests
        import time
        
        start1 = time.time()
        profile1 = query_engine.get_researcher_profile_complete(researcher_id)
        end1 = time.time()
        
        start2 = time.time()
        profile2 = query_engine.get_researcher_profile_complete(researcher_id)
        end2 = time.time()
        
        redis_info = query_engine.db_manager.redis.client.info()
        
        return jsonify({
            "request1": {
                "time": end1 - start1,
                "cache_status": profile1.get("cache_status")
            },
            "request2": {
                "time": end2 - start2,
                "cache_status": profile2.get("cache_status")
            },
            "redis_stats": {
                "used_memory": redis_info.get("used_memory_human"),
                "hits": redis_info.get("keyspace_hits"),
                "misses": redis_info.get("keyspace_misses")
            }
        })
    except Exception as e:
        logger.error(f"Cache demo error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/researchers/list')
def api_researchers_list():
    """API endpoint to get list of researchers"""
    try:
        if not query_engine:
            return jsonify({"error": "Database connections not available"}), 500
            
        limit = int(request.args.get('limit', 0))
        researchers = query_engine.db_manager.mongodb.search_researchers({}, limit=limit)
        
        return jsonify(researchers)
    except Exception as e:
        logger.error(f"API researchers list error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/researcher/<researcher_id>/collaborators/add', methods=['POST'])
def add_collaborator(researcher_id):
    """Add a collaborator manually"""
    try:
        if not query_engine:
            return jsonify({"error": "Database not connected"}), 503
            
        data = request.get_json()
        collaborator_id = data.get('collaborator_id')
        
        if not collaborator_id:
            return jsonify({"error": "Collaborator ID required"}), 400
            
        logger.info(f"Attempting to add collaboration: {researcher_id} <-> {collaborator_id}")
        success = query_engine.db_manager.neo4j.add_collaboration(researcher_id, collaborator_id)
        
        if success:
            # Comprehensive cache invalidation
            query_engine.db_manager.redis.client.delete(f"researcher_profile:{researcher_id}")
            query_engine.db_manager.redis.client.delete(f"researcher_profile:{collaborator_id}")
            logger.info(f"Successfully added collaboration and invalidated cache for {researcher_id} and {collaborator_id}")
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Failed to add collaborator in Neo4j"}), 500
            
    except Exception as e:
        logger.error(f"Add collaborator API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/researcher/<researcher_id>/collaborators/remove', methods=['POST'])
def remove_collaborator(researcher_id):
    """Remove a collaborator manually"""
    try:
        if not query_engine:
            return jsonify({"error": "Database not connected"}), 503
            
        data = request.get_json()
        collaborator_id = data.get('collaborator_id')
        
        if not collaborator_id:
            return jsonify({"error": "Collaborator ID required"}), 400
            
        logger.info(f"Attempting to remove collaboration: {researcher_id} <-> {collaborator_id}")
        success = query_engine.db_manager.neo4j.remove_collaboration(researcher_id, collaborator_id)
        
        if success:
            # Comprehensive cache invalidation
            query_engine.db_manager.redis.client.delete(f"researcher_profile:{researcher_id}")
            query_engine.db_manager.redis.client.delete(f"researcher_profile:{collaborator_id}")
            logger.info(f"Successfully removed collaboration and invalidated cache for {researcher_id} and {collaborator_id}")
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Failed to remove collaborator in Neo4j"}), 500
            
    except Exception as e:
        logger.error(f"Remove collaborator API error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/researcher/<researcher_id>')
def api_researcher_profile(researcher_id):
    """API endpoint for researcher profile"""
    try:
        if not query_engine:
            return jsonify({"error": "Database connections not available"}), 500
        
        profile = query_engine.get_researcher_profile_complete(researcher_id)
        if "error" in profile:
            return jsonify(profile), 404
        
        return jsonify(profile)
    except Exception as e:
        logger.error(f"API profile error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/department/<department_id>')
def api_department_analytics(department_id):
    """API endpoint for department analytics"""
    try:
        if not query_engine:
            return jsonify({"error": "Database connections not available"}), 500
        
        days = request.args.get('days', 30, type=int)
        analytics = query_engine.get_department_analytics(department_id, days)
        
        if "error" in analytics:
            return jsonify(analytics), 404
        
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"API analytics error: {e}")
        return jsonify({"error": str(e)}), 500


def get_system_overview() -> Dict[str, Any]:
    """Get system overview statistics"""
    try:
        db = query_engine.db_manager.mongodb
        
        # Basic counts
        total_researchers = db.count_documents("researchers", {})
        total_projects = db.count_documents("projects", {})
        total_publications = db.count_documents("publications", {})
        
        # Department stats
        departments = ["dept_cs", "dept_bio", "dept_chem", "dept_math", "dept_physics"]
        dept_stats = {}
        
        for dept in departments:
            researchers = db.search_researchers({"academic_profile.department_id": dept})
            dept_stats[dept] = {
                "researcher_count": len(researchers),
                "avg_h_index": sum(r.get("collaboration_metrics", {}).get("h_index", 0) for r in researchers) / max(len(researchers), 1)
            }
        
        # Recent activity
        recent_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).isoformat()
        recent_publications = db.find_documents("publications", {
            "bibliographic_info.publication_date": {"$gte": recent_date}
        })
        
        return {
            "total_researchers": total_researchers,
            "total_projects": total_projects,
            "total_publications": total_publications,
            "department_statistics": dept_stats,
            "recent_activity": {
                "recent_publications": len(recent_publications)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system overview: {e}")
        return {"error": str(e)}


def get_recent_publications(limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent publications"""
    try:
        publications = query_engine.db_manager.mongodb.find_documents("publications", {
            "bibliographic_info.publication_date": {"$exists": True}
        })
        
        # Sort by publication date (descending)
        sorted_publications = sorted(
            publications,
            key=lambda x: x.get("bibliographic_info", {}).get("publication_date", ""),
            reverse=True
        )
        
        # Limit and process
        recent_pubs = []
        for pub in sorted_publications[:limit]:
            processed_pub = {
                "id": pub.get("_id"),
                "title": pub.get("title", "No title"),
                "authors": [author.get("researcher_id", "") for author in pub.get("authors", [])],
                "publication_date": pub.get("bibliographic_info", {}).get("publication_date", ""),
                "journal": pub.get("bibliographic_info", {}).get("journal", "Unknown"),
                "citation_count": pub.get("metrics", {}).get("citation_count", 0)
            }
            recent_pubs.append(processed_pub)
        
        return recent_pubs
    except Exception as e:
        logger.error(f"Failed to get recent publications: {e}")
        return []


def get_department_summary() -> List[Dict[str, Any]]:
    """Get department summary"""
    try:
        departments = ["dept_cs", "dept_bio", "dept_chem", "dept_math", "dept_physics"]
        department_names = {
            "dept_cs": "Computer Science",
            "dept_bio": "Biology", 
            "dept_chem": "Chemistry",
            "dept_math": "Mathematics",
            "dept_physics": "Physics"
        }
        
        summary = []
        for dept in departments:
            try:
                analytics = query_engine.get_department_analytics(dept, days=30)
                if "error" not in analytics:
                    basic = analytics.get("basic_metrics", {})
                    summary.append({
                        "department": dept,
                        "name": department_names[dept],
                        "researcher_count": basic.get("total_researchers", 0),
                        "total_publications": basic.get("total_publications", 0),
                        "avg_h_index": basic.get("average_h_index", 0),
                        "active_projects": basic.get("active_projects", 0)
                    })
            except Exception as e:
                logger.warning(f"Failed to get summary for {dept}: {e}")
        
        return summary
    except Exception as e:
        logger.error(f"Failed to get department summary: {e}")
        return []


# ==================== NEW FEATURES ====================

# Report Generator instance
report_gen = None
data_exporter = None

def get_report_generator():
    """Get or create report generator instance"""
    global report_gen, data_exporter
    if report_gen is None and db_manager:
        report_gen = ReportGenerator(db_manager, query_engine)
        data_exporter = DataExporter(db_manager)
    return report_gen, data_exporter


@app.route('/reports')
@login_required
def reports():
    """Reports and export page"""
    try:
        stats = {
            'researchers': 0,
            'projects': 0,
            'publications': 0
        }
        
        if query_engine and db_manager:
            try:
                stats['researchers'] = db_manager.mongodb.count_documents('researchers')
                stats['projects'] = db_manager.mongodb.count_documents('projects')
                stats['publications'] = db_manager.mongodb.count_documents('publications')
            except:
                pass
        
        return render_template('reports.html', stats=stats)
    except Exception as e:
        logger.error(f"Reports page error: {e}")
        flash(f'Error loading reports page: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download_report/<report_type>')
def download_report(report_type):
    """Download PDF report"""
    try:
        gen, _ = get_report_generator()
        if not gen:
            flash('Report generator not available', 'error')
            return redirect(url_for('reports'))
        
        buffer = None
        filename = f"{report_type}_report.pdf"
        
        if report_type == 'system_overview':
            buffer = gen.generate_system_overview_report()
        elif report_type == 'researchers':
            buffer = gen.generate_researchers_report()
        elif report_type == 'projects':
            buffer = gen.generate_projects_report()
        elif report_type == 'publications':
            buffer = gen.generate_publications_report()
        elif report_type == 'analytics':
            buffer = gen.generate_analytics_report()
        elif report_type == 'collaboration':
            buffer = gen.generate_collaboration_report()
        else:
            flash('Unknown report type', 'error')
            return redirect(url_for('reports'))
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Report download error: {e}")
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/export_data/<data_type>/<format>')
def export_data(data_type, format):
    """Export data in various formats"""
    try:
        _, exporter = get_report_generator()
        if not exporter:
            flash('Data exporter not available', 'error')
            return redirect(url_for('reports'))
        
        buffer = None
        mimetype = 'text/csv'
        filename = f"{data_type}.{format}"
        
        if format == 'csv':
            if data_type == 'researchers':
                buffer = exporter.export_researchers_csv()
            elif data_type == 'projects':
                buffer = exporter.export_projects_csv()
            elif data_type == 'publications':
                buffer = exporter.export_publications_csv()
            mimetype = 'text/csv'
        elif format == 'json':
            if data_type == 'researchers' and db_manager:
                data = db_manager.mongodb.find_documents('researchers', {})
            elif data_type == 'projects' and db_manager:
                data = db_manager.mongodb.find_documents('projects', {})
            elif data_type == 'publications' and db_manager:
                data = db_manager.mongodb.find_documents('publications', {})
            else:
                data = []
            buffer = exporter.export_to_json(data)
            mimetype = 'application/json'
        
        if buffer:
            return Response(
                buffer.getvalue(),
                mimetype=mimetype,
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
        
        flash('Export failed', 'error')
        return redirect(url_for('reports'))
    except Exception as e:
        logger.error(f"Export error: {e}")
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/backup_all_data')
def backup_all_data():
    """Backup all system data"""
    try:
        if not db_manager:
            flash('Database not available', 'error')
            return redirect(url_for('reports'))
        
        import io
        
        backup_data = {
            'backup_date': datetime.utcnow().isoformat(),
            'researchers': db_manager.mongodb.find_documents('researchers', {}),
            'projects': db_manager.mongodb.find_documents('projects', {}),
            'publications': db_manager.mongodb.find_documents('publications', {})
        }
        
        buffer = io.StringIO()
        json.dump(backup_data, buffer, indent=2, default=str)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=system_backup_{datetime.now().strftime("%Y%m%d")}.json'}
        )
    except Exception as e:
        logger.error(f"Backup error: {e}")
        flash(f'Error creating backup: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/import_data', methods=['POST'])
def import_data():
    """Import data from file"""
    try:
        if not db_manager:
            flash('Database not available', 'error')
            return redirect(url_for('reports'))
        
        file = request.files.get('file')
        data_type = request.form.get('data_type')
        
        if not file:
            flash('No file provided', 'error')
            return redirect(url_for('reports'))
        
        filename = secure_filename(file.filename)
        
        if filename.endswith('.json'):
            import_data = json.load(file)
            if isinstance(import_data, list):
                for item in import_data:
                    if data_type == 'researchers':
                        db_manager.mongodb.create_researcher(item)
                    elif data_type == 'projects':
                        db_manager.mongodb.create_project(item)
                    elif data_type == 'publications':
                        db_manager.mongodb.create_publication(item)
            flash(f'Imported {len(import_data)} items successfully!', 'success')
        elif filename.endswith('.csv'):
            df = pd.read_csv(file)
            flash(f'Imported {len(df)} items from CSV!', 'success')
        else:
            flash('Unsupported file format', 'error')
        
        return redirect(url_for('reports'))
    except Exception as e:
        logger.error(f"Import error: {e}")
        flash(f'Error importing data: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/generate_custom_report', methods=['POST'])
def generate_custom_report():
    """Generate custom report based on user selection"""
    try:
        gen, exporter = get_report_generator()
        if not gen:
            flash('Report generator not available', 'error')
            return redirect(url_for('reports'))
        
        includes = request.form.getlist('include')
        format_type = request.form.get('format', 'pdf')
        
        if format_type == 'pdf':
            buffer = gen.generate_system_overview_report()
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='custom_report.pdf'
            )
        else:
            flash('Custom report generated!', 'success')
            return redirect(url_for('reports'))
    except Exception as e:
        logger.error(f"Custom report error: {e}")
        flash(f'Error generating custom report: {str(e)}', 'error')
        return redirect(url_for('reports'))


@app.route('/network')
@login_required
def network_visualization():
    """Interactive network visualization page"""
    try:
        stats = {
            'total_researchers': 0,
            'total_collaborations': 0,
            'total_supervisions': 0,
            'avg_collaborations_per_researcher': 0,
            'most_connected': []
        }
        
        network_data = {'nodes': [], 'edges': []}
        
        if query_engine and db_manager:
            # 1. Get stats from Neo4j
            try:
                stats = db_manager.neo4j.get_collaboration_statistics()
            except Exception as e:
                logger.warning(f"Error fetching network stats: {e}")

            # 2. Get researchers from MongoDB
            try:
                researchers = db_manager.mongodb.find_documents('researchers', {})
                for r in researchers:
                    network_data['nodes'].append({
                        'id': str(r['_id']),
                        'name': f"{r.get('personal_info', {}).get('first_name', '')} {r.get('personal_info', {}).get('last_name', '')}",
                        'h_index': r.get('collaboration_metrics', {}).get('h_index', 0),
                        'publication_count': r.get('collaboration_metrics', {}).get('total_publications', 0),
                        'department': r.get('academic_profile', {}).get('department_id', '')
                    })
            except Exception as e:
                logger.warning(f"Error fetching network nodes: {e}")

            # 3. Get relationships from Neo4j
            try:
                with db_manager.neo4j.driver.session() as session:
                    # Use undirected match with ID comparison to avoid duplicates
                    result = session.run("""
                        MATCH (r1:Researcher)-[rel]-(r2:Researcher)
                        WHERE r1.id < r2.id
                        RETURN r1.id as from, r2.id as to, type(rel) as type, 
                               COALESCE(rel.strength, 1) as strength
                        LIMIT 1000
                    """)
                    for record in result:
                        network_data['edges'].append({
                            'from': record['from'],
                            'to': record['to'],
                            'type': record['type'],
                            'strength': record['strength']
                        })
            except Exception as e:
                logger.warning(f"Error fetching network edges: {e}")
        
        return render_template('network_visualization.html', 
                             stats=stats, 
                             network_data=network_data)
    except Exception as e:
        logger.error(f"Network visualization error: {e}")
        flash(f'Error loading network visualization: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/compare')
@login_required
def compare_researchers():
    """Researcher comparison page"""
    try:
        researchers_list = []
        researcher1 = None
        researcher2 = None
        
        if query_engine and db_manager:
            researchers_list = db_manager.mongodb.find_documents('researchers', {})
            
            r1_id = request.args.get('researcher1')
            r2_id = request.args.get('researcher2')
            
            if r1_id:
                researcher1 = db_manager.mongodb.get_researcher(r1_id)
                if researcher1:
                    try:
                        collabs = query_engine.db_manager.neo4j.find_collaborators(r1_id, max_depth=1)
                        researcher1['collaboration_metrics']['active_collaborations'] = len(collabs)
                    except:
                        if 'collaboration_metrics' not in researcher1: researcher1['collaboration_metrics'] = {}
                        researcher1['collaboration_metrics']['active_collaborations'] = 0
                        
            if r2_id:
                researcher2 = db_manager.mongodb.get_researcher(r2_id)
                if researcher2:
                    try:
                        collabs = query_engine.db_manager.neo4j.find_collaborators(r2_id, max_depth=1)
                        researcher2['collaboration_metrics']['active_collaborations'] = len(collabs)
                    except:
                        if 'collaboration_metrics' not in researcher2: researcher2['collaboration_metrics'] = {}
                        researcher2['collaboration_metrics']['active_collaborations'] = 0

        
        # Prepare comparison data JSON for the frontend
        comparison_data = {}
        if researcher1 and researcher2:
            comparison_data = {
                'r1': {
                    'name': f"{researcher1['personal_info']['first_name']} {researcher1['personal_info']['last_name']}",
                    'hindex': researcher1.get('collaboration_metrics', {}).get('h_index', 0),
                    'publications': researcher1.get('collaboration_metrics', {}).get('total_publications', 0),
                    'citations': researcher1.get('collaboration_metrics', {}).get('total_citations', 0),
                    'collaborations': researcher1.get('collaboration_metrics', {}).get('active_collaborations', 0)
                },
                'r2': {
                    'name': f"{researcher2['personal_info']['first_name']} {researcher2['personal_info']['last_name']}",
                    'hindex': researcher2.get('collaboration_metrics', {}).get('h_index', 0),
                    'publications': researcher2.get('collaboration_metrics', {}).get('total_publications', 0),
                    'citations': researcher2.get('collaboration_metrics', {}).get('total_citations', 0),
                    'collaborations': researcher2.get('collaboration_metrics', {}).get('active_collaborations', 0)
                }
            }
        
        return render_template('compare_researchers.html',
                             researchers=researchers_list,
                             researcher1=researcher1,
                             researcher2=researcher2,
                             comparison_data_json=json.dumps(comparison_data))
    except Exception as e:
        logger.error(f"Compare researchers error: {e}")
        flash(f'Error loading comparison page: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/export_comparison_pdf')
def export_comparison_pdf():
    """Export researcher comparison as PDF"""
    try:
        r1_id = request.args.get('r1')
        r2_id = request.args.get('r2')
        
        gen, _ = get_report_generator()
        if gen and db_manager and r1_id and r2_id:
            r1 = db_manager.mongodb.get_researcher(r1_id)
            r2 = db_manager.mongodb.get_researcher(r2_id)
            
            if r1 and r2:
                # Generate comparison report
                buffer = gen.generate_researchers_report([r1, r2])
                return send_file(
                    buffer,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name='comparison_report.pdf'
                )
        
        flash('Could not generate comparison report', 'error')
        return redirect(url_for('compare_researchers'))
    except Exception as e:
        logger.error(f"Comparison PDF error: {e}")
        flash(f'Error generating comparison PDF: {str(e)}', 'error')
        return redirect(url_for('compare_researchers'))


@app.route('/advanced-search')
@login_required
def advanced_search():
    """Advanced search page"""
    try:
        query = request.args.get('q', '')
        entity_type = request.args.get('type', 'all')
        results = []
        
        if query and query_engine and db_manager:
            # Search researchers
            if entity_type in ['all', 'researcher']:
                researchers = db_manager.mongodb.find_documents('researchers', {
                    '$or': [
                        {'personal_info.first_name': {'$regex': query, '$options': 'i'}},
                        {'personal_info.last_name': {'$regex': query, '$options': 'i'}},
                        {'personal_info.email': {'$regex': query, '$options': 'i'}}
                    ]
                })
                for r in researchers:
                    r['type'] = 'researcher'
                    results.append(r)
            
            # Search projects
            if entity_type in ['all', 'project']:
                projects = db_manager.mongodb.find_documents('projects', {
                    '$or': [
                        {'title': {'$regex': query, '$options': 'i'}},
                        {'description': {'$regex': query, '$options': 'i'}}
                    ]
                })
                for p in projects:
                    p['type'] = 'project'
                    results.append(p)
            
            # Search publications
            if entity_type in ['all', 'publication']:
                publications = db_manager.mongodb.find_documents('publications', {
                    '$or': [
                        {'title': {'$regex': query, '$options': 'i'}},
                        {'bibliographic_info.journal': {'$regex': query, '$options': 'i'}}
                    ]
                })
                for pub in publications:
                    pub['type'] = 'publication'
                    results.append(pub)
        
        return render_template('advanced_search.html',
                             query=query,
                             entity_type=entity_type,
                             results=results)
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        flash(f'Error performing search: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/api/search/suggestions')
def search_suggestions():
    """API for search suggestions"""
    try:
        query = request.args.get('q', '')
        suggestions = []
        
        if query and len(query) >= 2 and db_manager:
            # Get researcher suggestions
            researchers = db_manager.mongodb.find_documents('researchers', {
                '$or': [
                    {'personal_info.first_name': {'$regex': f'^{query}', '$options': 'i'}},
                    {'personal_info.last_name': {'$regex': f'^{query}', '$options': 'i'}}
                ]
            }, limit=5)
            
            for r in researchers:
                name = f"{r.get('personal_info', {}).get('first_name', '')} {r.get('personal_info', {}).get('last_name', '')}"
                suggestions.append({'text': name, 'type': 'researcher'})
            
            # Get project suggestions
            projects = db_manager.mongodb.find_documents('projects', {
                'title': {'$regex': f'^{query}', '$options': 'i'}
            }, limit=3)
            
            for p in projects:
                suggestions.append({'text': p.get('title', ''), 'type': 'project'})
        
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return jsonify({'suggestions': []})


@app.route('/export_search_results')
def export_search_results():
    """Export search results"""
    query = request.args.get('q', '')
    format_type = request.args.get('format', 'csv')
    
    # Redirect to search with export flag
    return redirect(url_for('advanced_search', q=query))


@app.route('/timeline')
@login_required
def activity_timeline():
    """Activity timeline page"""
    try:
        stats = {
            'total_created': 0,
            'total_updated': 0,
            'total_deleted': 0,
            'total_collaborations': 0
        }
        
        activities = []
        
        # In a real implementation, you would track activities in a database
        # For now, we'll show sample data from the template
        
        if query_engine and db_manager:
            try:
                collab_stats = db_manager.neo4j.get_collaboration_statistics()
                stats['total_collaborations'] = collab_stats.get('total_collaborations', 0)
                
                # Count items as "created"
                stats['total_created'] = (
                    db_manager.mongodb.count_documents('researchers') +
                    db_manager.mongodb.count_documents('projects') +
                    db_manager.mongodb.count_documents('publications')
                )
            except:
                pass
        
        return render_template('activity_timeline.html',
                             stats=stats,
                             activities=activities)
    except Exception as e:
        logger.error(f"Activity timeline error: {e}")
        flash(f'Error loading activity timeline: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/export_activity_log')
def export_activity_log():
    """Export activity log"""
    try:
        import io
        
        # In a real implementation, this would export actual activity data
        log_data = {
            'export_date': datetime.utcnow().isoformat(),
            'activities': []
        }
        
        buffer = io.StringIO()
        json.dump(log_data, buffer, indent=2)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=activity_log.json'}
        )
    except Exception as e:
        logger.error(f"Export activity log error: {e}")
        flash(f'Error exporting activity log: {str(e)}', 'error')
        return redirect(url_for('activity_timeline'))


@app.route('/db/status')
def db_status():
    """Check database connection status"""
    db_type = request.args.get('db')
    status = False
    
    try:
        if not query_engine or not query_engine.db_manager:
            return jsonify({"status": False, "error": "Database manager not initialized"}), 503

        if db_type == 'mongodb':
            query_engine.db_manager.mongodb.client.admin.command('ping')
            status = True
        elif db_type == 'neo4j':
            query_engine.db_manager.neo4j.driver.verify_connectivity()
            status = True
        elif db_type == 'redis':
            status = query_engine.db_manager.redis.client.ping()
        elif db_type == 'cassandra':
            query_engine.db_manager.cassandra.session.execute("SELECT now() FROM system.local")
            status = True
            
        return jsonify({"status": status})
    except Exception as e:
        logger.error(f"Status check failed for {db_type}: {e}")
        return jsonify({"status": False, "error": str(e)})


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code="404",
                         error_message="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code="500", 
                         error_message="Internal server error"), 500


def initialize_app():
    """Initialize the application"""
    logger.info("Initializing Research Collaboration System Web Interface...")
    try:
        if not init_databases():
            logger.error("Failed to initialize databases")
        else:
            logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Error during app initialization: {e}")
        logger.warning("Continuing to start Flask server despite initialization errors...")

if __name__ == "__main__":
    # Initialize implementation
    initialize_app()
    
    os.makedirs('templates', exist_ok=True)
    port = int(os.environ.get("WEB_PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)